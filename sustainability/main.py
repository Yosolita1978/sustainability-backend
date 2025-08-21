#!/usr/bin/env python
"""
FastAPI Backend for Sustainability Training
Single file approach - everything in one place for MVP
"""

import os
import sys
import uuid
import asyncio
import warnings
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Suppress specific warnings from dependencies until they update to Pydantic v2
# Note: Our code uses Pydantic v2 correctly, but CrewAI/LangChain still use v1 syntax
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings(
    "ignore", 
    category=DeprecationWarning,
    message="Support for class-based `config` is deprecated",
    module="pydantic._internal._config"
)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets.legacy")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn.protocols.websockets.websockets_impl")


# Add sustainability module to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import your existing crew
from sustainability.crew import Sustainability

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# FastAPI app setup
app = FastAPI(
    title="Sustainability Training API",
    description="AI-powered sustainability messaging training",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELS
# ============================================================================

class TrainingRequest(BaseModel):
    industry_focus: str
    regulatory_framework: str
    training_level: str

class TrainingResponse(BaseModel):
    session_id: str
    status: str
    message: str

class StatusResponse(BaseModel):
    session_id: str
    status: str
    progress: int
    current_step: str
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None

class ProgressUpdate(BaseModel):
    step: str
    progress: int
    agent: str
    message: str

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

# In-memory session storage
sessions: Dict[str, Dict[str, Any]] = {}

def create_session(training_request: TrainingRequest) -> str:
    """Create a new training session with unique ID"""
    session_id = str(uuid.uuid4())
    
    sessions[session_id] = {
        "id": session_id,
        "status": "created",
        "progress": 0,
        "current_step": "Initializing...",
        "created_at": datetime.now(),
        "completed_at": None,
        "error": None,
        "request": training_request.model_dump(),
        "results": None,
        "file_path": None,
        "progress_updates": [],
        "txt_dump_file": None,  # Track the .txt dump file for this session
        "crew_log_file": None   # Track the crew log file for this session
    }
    
    return session_id

def update_session_progress(session_id: str, progress: int, step: str, agent: str = "System", message: str = ""):
    """Update session progress"""
    if session_id in sessions:
        sessions[session_id]["progress"] = progress
        sessions[session_id]["current_step"] = step
        
        # Add to progress history
        update = {
            "timestamp": datetime.now().isoformat(),
            "progress": progress,
            "step": step,
            "agent": agent,
            "message": message
        }
        sessions[session_id]["progress_updates"].append(update)
        
        print(f"Session {session_id}: {progress}% - {step}")

def complete_session(session_id: str, results: Any, file_path: str = None, error: str = None):
    """Mark session as completed"""
    if session_id in sessions:
        sessions[session_id]["completed_at"] = datetime.now()
        sessions[session_id]["results"] = results
        sessions[session_id]["file_path"] = file_path
        
        if error:
            sessions[session_id]["status"] = "failed"
            sessions[session_id]["error"] = error
            sessions[session_id]["progress"] = 0
        else:
            sessions[session_id]["status"] = "completed"
            sessions[session_id]["progress"] = 100
            sessions[session_id]["current_step"] = "Training completed successfully!"

def cleanup_old_sessions():
    """Remove sessions older than 2 hours and their files"""
    cutoff_time = datetime.now() - timedelta(hours=2)
    expired_sessions = [
        sid for sid, session in sessions.items()
        if session["created_at"] < cutoff_time
    ]
    
    for sid in expired_sessions:
        # Clean up session files
        if sessions[sid].get("file_path") and os.path.exists(sessions[sid]["file_path"]):
            try:
                os.remove(sessions[sid]["file_path"])
            except:
                pass
        
        # Clean up .txt dump file
        if sessions[sid].get("txt_dump_file") and os.path.exists(sessions[sid]["txt_dump_file"]):
            try:
                os.remove(sessions[sid]["txt_dump_file"])
            except:
                pass
        
        # Clean up crew log file
        if sessions[sid].get("crew_log_file") and os.path.exists(sessions[sid]["crew_log_file"]):
            try:
                os.remove(sessions[sid]["crew_log_file"])
            except:
                pass
        
        del sessions[sid]
        print(f"Cleaned up expired session: {sid}")

def get_regulatory_details(region: str) -> Dict[str, str]:
    """Get regulatory details for the region"""
    frameworks = {
        "EU": {
            "regulations": "EU Green Claims Directive, CSRD, EU Taxonomy Regulation",
            "description": "European Union sustainability regulations focusing on green claims substantiation"
        },
        "USA": {
            "regulations": "FTC Green Guides, SEC Climate Disclosure Rules, EPA Green Power Partnership", 
            "description": "US federal guidance and rules for environmental marketing claims"
        },
        "UK": {
            "regulations": "CMA Green Claims Code, FCA Sustainability Disclosure Requirements, ASA CAP Code",
            "description": "UK-specific guidance for environmental claims and financial sustainability disclosures"
        },
        "Global": {
            "regulations": "ISO 14021, GRI Standards, TCFD Recommendations, ISSB Standards",
            "description": "International standards and frameworks for sustainability communication"
        }
    }
    return frameworks.get(region, frameworks["Global"])

# ============================================================================
# MODIFIED CALLBACK SYSTEM
# ============================================================================

class APICallbackHandler:
    """Callback handler that updates session instead of Panel"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.task_count = 0
        self.completed_tasks = 0
    
    def on_task_start(self, agent_name: str, task_description: str):
        """Called when a task starts"""
        self.task_count += 1
        progress = min(20 + (self.completed_tasks * 20), 80)
        
        update_session_progress(
            self.session_id,
            progress,
            f"Task {self.task_count}/4: {agent_name} working...",
            agent_name,
            task_description[:100] + "..." if len(task_description) > 100 else task_description
        )
    
    def on_task_complete(self, agent_name: str, task_output: str):
        """Called when a task completes"""
        self.completed_tasks += 1
        progress = min(20 + (self.completed_tasks * 20), 95)
        
        update_session_progress(
            self.session_id,
            progress,
            f"Completed: {agent_name}",
            agent_name,
            "Task completed successfully"
        )

# ============================================================================
# COMPREHENSIVE DATA EXTRACTION FROM LOG FILES
# ============================================================================

def extract_all_task_data_from_log(log_file_path: str) -> Dict[str, Any]:
    """Extract ALL detailed data from the session log file"""
    print(f"🔍 EXTRACTING: Reading session log file: {log_file_path}")
    
    extracted_data = {
        "scenario_data": None,
        "problematic_messages": None,
        "corrected_messages": None,
        "playbook_data": None,
        "extraction_log": []
    }
    
    if not os.path.exists(log_file_path):
        print(f"❌ EXTRACTING: Log file not found: {log_file_path}")
        return extracted_data
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Extract task outputs using regex patterns
        task_pattern = r'task_name="([^"]+)".*?status="completed".*?output="(\{.*?\})"(?=\n\d{4}-\d{2}-\d{2}|\Z)'
        
        matches = re.findall(task_pattern, log_content, re.DOTALL)
        
        for task_name, output_json in matches:
            try:
                # Clean and parse the JSON
                cleaned_json = output_json.replace('\n', '').replace('\\', '')
                task_data = json.loads(cleaned_json)
                
                # Categorize based on task name
                if "scenario" in task_name:
                    extracted_data["scenario_data"] = task_data
                    extracted_data["extraction_log"].append(f"✅ Extracted scenario data: {task_data.get('company_name', 'Unknown')}")
                    
                elif "mistake" in task_name:
                    extracted_data["problematic_messages"] = task_data
                    num_messages = len(task_data.get('problematic_messages', []))
                    extracted_data["extraction_log"].append(f"✅ Extracted {num_messages} problematic messages")
                    
                elif "best_practice" in task_name:
                    extracted_data["corrected_messages"] = task_data
                    num_corrections = len(task_data.get('corrected_messages', []))
                    extracted_data["extraction_log"].append(f"✅ Extracted {num_corrections} corrected messages")
                    
                elif "playbook" in task_name:
                    extracted_data["playbook_data"] = task_data
                    extracted_data["extraction_log"].append(f"✅ Extracted playbook: {task_data.get('playbook_title', 'Unknown')}")
                    
            except json.JSONDecodeError as e:
                extracted_data["extraction_log"].append(f"❌ JSON parse error for {task_name}: {e}")
                print(f"❌ EXTRACTING: JSON parse error for {task_name}: {e}")
                
        print(f"✅ EXTRACTING: Completed extraction from {log_file_path}")
        return extracted_data
        
    except Exception as e:
        print(f"❌ EXTRACTING: Error reading log file: {e}")
        extracted_data["extraction_log"].append(f"❌ Error reading log file: {e}")
        return extracted_data

def create_comprehensive_markdown(all_data: Dict[str, Any], session_id: str, training_request: TrainingRequest) -> str:
    """Create comprehensive markdown from ALL extracted task data"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Extract data sections
    scenario = all_data.get('scenario_data', {})
    problematic = all_data.get('problematic_messages', {})
    corrected = all_data.get('corrected_messages', {})
    playbook = all_data.get('playbook_data', {})
    
    # Start building comprehensive content
    content = f"""# {playbook.get('playbook_title', 'Comprehensive Sustainability Training Report')}

**🤖 Generated by:** Sustainability Training AI  
**📅 Created:** {timestamp}  
**🆔 Session ID:** {session_id}  
**🏢 Industry Focus:** {training_request.industry_focus}  
**🌍 Regulatory Framework:** {training_request.regulatory_framework}  
**📊 Training Level:** {training_request.training_level}  

---

## 📋 Executive Summary

{playbook.get('executive_summary', 'This comprehensive report provides detailed sustainability messaging guidance tailored to your industry and regulatory context.')}

---

## 🏢 Business Scenario: {scenario.get('company_name', 'Your Company')}

**Industry:** {scenario.get('industry', 'N/A')}  
**Company Size:** {scenario.get('company_size', 'N/A')}  
**Location:** {scenario.get('location', 'N/A')}  

**Product/Service:** {scenario.get('product_service', 'N/A')}

**Target Audience:** {scenario.get('target_audience', 'N/A')}

### Marketing Objectives
{format_list_items(scenario.get('marketing_objectives', []))}

### Sustainability Context
{scenario.get('sustainability_context', 'N/A')}

### Initial Claims to Review
{format_list_items(scenario.get('preliminary_claims', []))}

### Regulatory Context
{scenario.get('regulatory_context', 'N/A')}

---

## 🚨 Problematic Messaging Analysis

{format_problematic_messages_detailed(problematic)}

---

## ✅ Best Practice Corrections

{format_corrected_messages_detailed(corrected)}

---

## 📋 Do's and Don'ts

{format_list_items(playbook.get('dos_and_donts', []))}

---

## 🚨 Greenwashing Patterns to Avoid

{format_list_items(playbook.get('greenwashing_patterns', []))}

---

## 🔄 Claim-to-Proof Framework

{format_framework_detailed(playbook.get('claim_to_proof_framework', {}))}

---

## ✅ Compliance Checklist

{format_checklist_detailed(playbook.get('compliance_checklist', {}))}

---

## 📖 Case Study Examples

{format_case_studies_detailed(playbook.get('case_study_snapshots', []))}

---

## 📄 Regulatory References

{format_list_items(playbook.get('regulatory_references', []))}

---

## 🚀 Implementation Guide

### Quick Start Guide
{format_list_items(playbook.get('quick_start_guide', []))}

### Team Training Tips
{format_list_items(playbook.get('team_training_tips', []))}

---

## 📚 Additional Resources

{format_list_items(playbook.get('additional_resources', []))}

---

## 📞 Contact Resources

{format_list_items(playbook.get('contact_resources', []))}

---

## 📖 Glossary

{format_list_items(playbook.get('glossary_terms', []))}

---

## 📊 Training Session Summary

**Total Tasks Completed:** 4  
**Data Extraction Status:** {len([x for x in all_data['extraction_log'] if '✅' in x])} successful extractions  

### Extraction Log
{format_list_items(all_data.get('extraction_log', []))}

---

*Generated by Sustainability Training AI on {timestamp}*  
*Session ID: {session_id}*  
*All data extracted from session-specific logs for maximum detail*
"""
    
    return content

def format_problematic_messages_detailed(problematic_data: Dict[str, Any]) -> str:
    """Format problematic messages with full detail"""
    if not problematic_data or not problematic_data.get('problematic_messages'):
        return "*No problematic messages data available*"
    
    content = f"**Scenario Reference:** {problematic_data.get('scenario_reference', 'N/A')}\n\n"
    content += f"**Regulatory Landscape:** {problematic_data.get('regulatory_landscape', 'N/A')}\n\n"
    
    for i, msg in enumerate(problematic_data.get('problematic_messages', []), 1):
        content += f"""### ❌ Problematic Message {i}

**Message:** "{msg.get('message', 'N/A')}"

**Problems Identified:**
{format_list_items(msg.get('problems_identified', []))}

**Regulatory Violations:**
{format_list_items(msg.get('regulatory_violations', []))}

**Greenwashing Patterns:**
{format_list_items(msg.get('greenwashing_patterns', []))}

**Why Problematic:**
{msg.get('why_problematic', 'N/A')}

**Real-World Examples:**
{format_list_items(msg.get('real_world_examples', []))}

**Potential Consequences:**
{format_list_items(msg.get('potential_consequences', []))}

---

"""
    
    return content

def format_corrected_messages_detailed(corrected_data: Dict[str, Any]) -> str:
    """Format corrected messages with full detail"""
    if not corrected_data or not corrected_data.get('corrected_messages'):
        return "*No corrected messages data available*"
    
    content = f"**Scenario Reference:** {corrected_data.get('scenario_reference', 'N/A')}\n\n"
    
    for i, msg in enumerate(corrected_data.get('corrected_messages', []), 1):
        content += f"""### ✅ Corrected Message {i}

**Original Problem:** Message {msg.get('original_message_id', 'N/A')}

**Improved Message:** "{msg.get('corrected_message', 'N/A')}"

**Changes Made:**
{format_list_items(msg.get('changes_made', []))}

**Compliance Notes:**
{msg.get('compliance_notes', 'N/A')}

**Best Practices Applied:**
{format_list_items(msg.get('best_practices_applied', []))}

**Real-World Examples:**
{format_list_items(msg.get('real_world_examples', []))}

**Effectiveness Rationale:**
{msg.get('effectiveness_rationale', 'N/A')}

---

"""
    
    return content

def format_framework_detailed(framework: Dict[str, Any]) -> str:
    """Format framework with full detail"""
    if not framework:
        return "*Framework not available*"
    
    content = f"""### {framework.get('framework_name', 'Validation Framework')}

**Steps:**
{format_list_items(framework.get('steps', []))}

**Validation Questions:**
{format_list_items(framework.get('validation_questions', []))}

**Proof Requirements:**
{format_list_items(framework.get('proof_requirements', []))}

**Common Pitfalls:**
{format_list_items(framework.get('common_pitfalls', []))}

**Examples:**
{format_list_items(framework.get('examples', []))}
"""
    
    return content

def format_checklist_detailed(checklist: Dict[str, Any]) -> str:
    """Format checklist with full detail"""
    if not checklist:
        return "*Checklist not available*"
    
    content = f"""### {checklist.get('checklist_name', 'Compliance Checklist')}

**Categories:**
{format_list_items(checklist.get('categories', []))}

**Validation Questions:**
{format_list_items(checklist.get('questions', []))}

**Red Flags:**
{format_list_items(checklist.get('red_flags', []))}

**Approval Criteria:**
{format_list_items(checklist.get('approval_criteria', []))}
"""
    
    return content

def format_case_studies_detailed(case_studies: List[Dict[str, Any]]) -> str:
    """Format case studies with full detail"""
    if not case_studies:
        return "*No case studies available*"
    
    content = ""
    for i, case in enumerate(case_studies, 1):
        content += f"""### Case Study {i}: {case.get('title', 'Untitled')}

**Company:** {case.get('company_name', 'Anonymous')}  
**Message Type:** {case.get('message_type', 'Unknown')}

**Original Message:**
> {case.get('original_message', 'Not provided')}

**Analysis:**
{case.get('analysis', 'No analysis provided')}

**Key Lesson:**
{case.get('key_lesson', 'No lesson provided')}

**Regulatory Context:**
{case.get('regulatory_context', 'No context provided')}

---

"""
    
    return content

# ============================================================================
# TRAINING EXECUTION WITH COMPREHENSIVE DATA EXTRACTION
# ============================================================================

def run_training_session(session_id: str, training_request: TrainingRequest):
    """Run the actual training session with comprehensive data extraction"""
    try:
        # Update session status
        update_session_progress(session_id, 5, "Initializing AI agents...", "System")
        
        # Get regulatory details
        regulatory_details = get_regulatory_details(training_request.regulatory_framework)
        
        # Prepare inputs for CrewAI
        inputs = {
            'user_industry': training_request.industry_focus,
            'regulatory_region': training_request.regulatory_framework,
            'regional_regulations': regulatory_details['regulations'],
            'regulatory_description': regulatory_details['description'],
            'current_year': str(datetime.now().year),
            'session_id': session_id
        }
        
        update_session_progress(session_id, 10, "Starting training crew...", "System")
        
        # Create callback handler for this session
        callback_handler = APICallbackHandler(session_id)
        
        # Create and run crew WITH SESSION ID
        print(f"🔧 DEBUGGING: Creating crew with session_id: {session_id}")
        sustainability_crew = Sustainability(session_id=session_id)  # PASS SESSION ID
        crew = sustainability_crew.crew()
        
        # Store the crew log file path in session
        crew_log_file = sustainability_crew._get_session_log_file()
        sessions[session_id]["crew_log_file"] = crew_log_file
        print(f"🔧 DEBUGGING: Crew log file will be: {crew_log_file}")
        
        update_session_progress(session_id, 15, "AI agents collaborating...", "System")
        
        # Run the training
        result = crew.kickoff(inputs=inputs)
        
        # Generate comprehensive report
        update_session_progress(session_id, 70, "Training complete, extracting ALL data...", "System")
        
        # Create outputs directory if needed
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(exist_ok=True)
        
        # Generate file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # =================================================================
        # SESSION-SPECIFIC .TXT DUMP FILE CREATION (UNCHANGED)
        # =================================================================
        print(f"🔍 DEBUGGING: Starting SESSION-SPECIFIC .txt dump file creation...")
        
        # Create session-specific dump filename
        dump_filename = f"session_{session_id[:8]}_{timestamp}_complete_dump.txt"
        dump_file_path = outputs_dir / dump_filename
        
        # Store the txt dump file path in session
        sessions[session_id]["txt_dump_file"] = str(dump_file_path)
        
        # Create .txt dump file (same as before)
        txt_file_created = False
        try:
            with open(dump_file_path, 'w', encoding='utf-8') as f:
                f.write(f"COMPLETE CREW RESULT DUMP - SESSION {session_id}\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Session ID: {session_id}\n")
                f.write(f"Timestamp: {datetime.now()}\n")
                f.write(f"Industry: {training_request.industry_focus}\n")
                f.write(f"Framework: {training_request.regulatory_framework}\n")
                f.write(f"Training Level: {training_request.training_level}\n")
                f.write(f"Session Log File: {crew_log_file}\n\n")
                
                f.write("RESULT OBJECT:\n")
                f.write("-" * 30 + "\n")
                f.write(str(result) + "\n\n")
                
                if hasattr(result, 'tasks_output'):
                    f.write(f"TASKS OUTPUT ({len(result.tasks_output)} tasks):\n")
                    f.write("-" * 30 + "\n")
                    for i, task_output in enumerate(result.tasks_output):
                        f.write(f"\nTASK {i+1} (Session {session_id}):\n")
                        f.write(f"Task Output Object: {task_output}\n")
                        
                        if hasattr(task_output, 'pydantic'):
                            f.write(f"Pydantic Data: {task_output.pydantic}\n")
                            if task_output.pydantic:
                                try:
                                    pydantic_dump = task_output.pydantic.model_dump()
                                    f.write(f"Pydantic Model Dump: {json.dumps(pydantic_dump, indent=2)}\n")
                                except Exception as e:
                                    f.write(f"Pydantic Model Dump Error: {e}\n")
                        
                        if hasattr(task_output, 'raw'):
                            f.write(f"Raw Output: {task_output.raw}\n")
                        
                        if hasattr(task_output, 'json_dict'):
                            f.write(f"JSON Dict: {task_output.json_dict}\n")
                        
                        f.write(f"All attributes: {[attr for attr in dir(task_output) if not attr.startswith('_')]}\n")
                        f.write("-" * 20 + "\n")
                
                f.write(f"\nSESSION ISOLATION INFO:\n")
                f.write("-" * 30 + "\n")
                f.write(f"Session ID: {session_id}\n")
                f.write(f"Crew Log File: {crew_log_file}\n")
                f.write(f"Dump File: {dump_file_path}\n")
                f.write(f"Creation Time: {datetime.now()}\n")
            
            if dump_file_path.exists():
                file_size = dump_file_path.stat().st_size
                print(f"✅ DEBUGGING: Session-specific .txt file created successfully!")
                print(f"✅ DEBUGGING: File size: {file_size:,} bytes")
                txt_file_created = True
                
        except Exception as txt_error:
            print(f"❌ DEBUGGING: Session-specific .txt file creation failed: {str(txt_error)}")
        
        # =================================================================
        # NEW: COMPREHENSIVE MARKDOWN GENERATION FROM LOG FILE
        # =================================================================
        update_session_progress(session_id, 85, "Extracting comprehensive data from logs...", "System")
        
        # Extract ALL data from the session log file
        all_task_data = extract_all_task_data_from_log(crew_log_file)
        
        update_session_progress(session_id, 90, "Generating comprehensive playbook...", "System")
        
        # Generate comprehensive markdown filename
        filename = f"comprehensive_playbook_{session_id[:8]}_{timestamp}.md"
        file_path = outputs_dir / filename
        
        # Create comprehensive markdown content
        comprehensive_markdown = create_comprehensive_markdown(all_task_data, session_id, training_request)
        
        # Save comprehensive markdown
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(comprehensive_markdown)
        
        # Complete session
        complete_session(session_id, result, str(file_path))
        
        print(f"✅ SESSION {session_id} COMPLETED WITH COMPREHENSIVE DATA")
        print(f"📄 Comprehensive markdown file: {file_path}")
        print(f"📄 TXT dump file: {dump_file_path if txt_file_created else 'FAILED'}")
        print(f"📄 Crew log file: {crew_log_file}")
        
    except Exception as e:
        error_msg = f"Training failed: {str(e)}"
        print(f"❌ Error in session {session_id}: {error_msg}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        complete_session(session_id, None, None, error_msg)

def format_list_items(items: list) -> str:
    """Format list items as markdown"""
    if not items:
        return "*No items available*"
    return "\n".join([f"• {item}" for item in items])

# ============================================================================
# API ENDPOINTS (UNCHANGED)
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/training/start", response_model=TrainingResponse)
async def start_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    """Start a new training session"""
    
    # Clean up old sessions
    cleanup_old_sessions()
    
    # Validate request
    if not request.industry_focus or not request.regulatory_framework:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # Create session
    session_id = create_session(request)
    
    # Start training in background
    background_tasks.add_task(run_training_session, session_id, request)
    
    return TrainingResponse(
        session_id=session_id,
        status="started",
        message="Training session started with comprehensive data extraction"
    )

@app.get("/api/training/status/{session_id}", response_model=StatusResponse)
async def get_training_status(session_id: str):
    """Get training session status"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    return StatusResponse(
        session_id=session_id,
        status=session["status"],
        progress=session["progress"],
        current_step=session["current_step"],
        created_at=session["created_at"].isoformat(),
        completed_at=session["completed_at"].isoformat() if session["completed_at"] else None,
        error=session["error"]
    )

@app.get("/api/training/download/{session_id}")
async def download_playbook(session_id: str):
    """Download the generated comprehensive playbook"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Training not completed yet")
    
    if not session["file_path"] or not os.path.exists(session["file_path"]):
        raise HTTPException(status_code=404, detail="Playbook file not found")
    
    file_path = session["file_path"]
    filename = os.path.basename(file_path)
    
    # Return file and schedule cleanup
    def cleanup_file():
        try:
            os.remove(file_path)
            # Also clean up session-specific files
            if session.get("txt_dump_file") and os.path.exists(session["txt_dump_file"]):
                os.remove(session["txt_dump_file"])
            if session.get("crew_log_file") and os.path.exists(session["crew_log_file"]):
                os.remove(session["crew_log_file"])
            if session_id in sessions:
                del sessions[session_id]
            print(f"Cleaned up session {session_id} after download")
        except:
            pass
    
    # Schedule cleanup after response
    import threading
    threading.Timer(1.0, cleanup_file).start()
    
    return FileResponse(
        file_path,
        media_type='text/markdown',
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/sessions")
async def list_active_sessions():
    """Debug endpoint to see active sessions"""
    return {
        "active_sessions": len(sessions),
        "sessions": {sid: {
            "status": session["status"],
            "progress": session["progress"],
            "created_at": session["created_at"].isoformat(),
            "txt_dump_file": session.get("txt_dump_file"),
            "crew_log_file": session.get("crew_log_file")
        } for sid, session in sessions.items()}
    }

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    print("🌱 Starting Sustainability Training API with Comprehensive Data Extraction...")
    print(f"🔗 Server will run on: http://localhost:{port}")
    print(f"📚 API docs available at: http://localhost:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True if not os.getenv("PORT") else False,  # Only reload in development
        log_level="info",
        ws="none"
    )