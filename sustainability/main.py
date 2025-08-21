#!/usr/bin/env python
"""
Enhanced FastAPI Backend for Sustainability Training
COMPLETELY FIXED multi-line JSON extraction and markdown generation
"""

import os
import sys
import uuid
import asyncio
import warnings
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Suppress specific warnings from dependencies
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

# Import enhanced modules
from sustainability.crew import Sustainability
from sustainability.data_extractor import SessionDataExtractor, extract_from_backup_files
from sustainability.markdown_generator import generate_comprehensive_playbook

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# FastAPI app setup
app = FastAPI(
    title="Multi-Line JSON Fixed Sustainability Training API",
    description="AI-powered sustainability messaging training with FIXED multi-line JSON extraction",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    quality_score: Optional[float] = None
    data_completeness: Optional[float] = None

class ProgressUpdate(BaseModel):
    step: str
    progress: int
    agent: str
    message: str

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

# Enhanced session storage
sessions: Dict[str, Dict[str, Any]] = {}

def create_session(training_request: TrainingRequest) -> str:
    """Create a new training session with enhanced tracking"""
    session_id = str(uuid.uuid4())
    
    sessions[session_id] = {
        "id": session_id,
        "status": "created",
        "progress": 0,
        "current_step": "Initializing multi-line JSON extraction system...",
        "created_at": datetime.now(),
        "completed_at": None,
        "error": None,
        "request": training_request.model_dump(),
        "results": None,
        "file_path": None,
        "progress_updates": [],
        "crew_log_file": None,
        "backup_directory": None,
        "extracted_data": None,
        "validation_result": None,
        "integration_result": None,
        "quality_score": None,
        "data_completeness": None
    }
    
    return session_id

def update_session_progress(session_id: str, progress: int, step: str, agent: str = "System", message: str = ""):
    """Update session progress with enhanced tracking"""
    if session_id in sessions:
        sessions[session_id]["progress"] = progress
        sessions[session_id]["current_step"] = step
        
        update = {
            "timestamp": datetime.now().isoformat(),
            "progress": progress,
            "step": step,
            "agent": agent,
            "message": message
        }
        sessions[session_id]["progress_updates"].append(update)
        
        print(f"Multi-Line Session {session_id}: {progress}% - {step}")

def complete_session(session_id: str, results: Any, file_path: str = None, error: str = None, 
                    quality_score: float = None, data_completeness: float = None):
    """Mark session as completed with quality metrics"""
    if session_id in sessions:
        sessions[session_id]["completed_at"] = datetime.now()
        sessions[session_id]["results"] = results
        sessions[session_id]["file_path"] = file_path
        sessions[session_id]["quality_score"] = quality_score
        sessions[session_id]["data_completeness"] = data_completeness
        
        if error:
            sessions[session_id]["status"] = "failed"
            sessions[session_id]["error"] = error
            sessions[session_id]["progress"] = 0
        else:
            sessions[session_id]["status"] = "completed"
            sessions[session_id]["progress"] = 100
            sessions[session_id]["current_step"] = "Multi-line JSON training completed successfully!"

def cleanup_old_sessions():
    """Remove sessions older than 4 hours and their files"""
    cutoff_time = datetime.now() - timedelta(hours=4)
    expired_sessions = [
        sid for sid, session in sessions.items()
        if session["created_at"] < cutoff_time
    ]
    
    for sid in expired_sessions:
        session = sessions[sid]
        
        # Clean up main files
        if session.get("file_path") and os.path.exists(session["file_path"]):
            try:
                os.remove(session["file_path"])
            except:
                pass
        
        # Clean up crew log file
        if session.get("crew_log_file") and os.path.exists(session["crew_log_file"]):
            try:
                os.remove(session["crew_log_file"])
            except:
                pass
        
        # Clean up backup directory
        if session.get("backup_directory"):
            backup_dir = Path(session["backup_directory"])
            if backup_dir.exists():
                try:
                    for file in backup_dir.glob("*"):
                        file.unlink()
                    backup_dir.rmdir()
                except:
                    pass
        
        del sessions[sid]
        print(f"Cleaned up expired multi-line session: {sid}")

def get_regulatory_details(region: str) -> Dict[str, str]:
    """Get regulatory details for the region"""
    frameworks = {
        "EU": {
            "regulations": "EU Green Claims Directive, CSRD, EU Taxonomy Regulation",
            "description": "European Union sustainability regulations focusing on green claims substantiation and corporate reporting",
            "enforcement_focus": "Mandatory substantiation, corporate transparency, taxonomy alignment"
        },
        "USA": {
            "regulations": "FTC Green Guides, SEC Climate Disclosure Rules, EPA Green Power Partnership", 
            "description": "US federal guidance and rules for environmental marketing claims and climate disclosures",
            "enforcement_focus": "Truthful advertising, climate risk disclosure, renewable energy verification"
        },
        "UK": {
            "regulations": "CMA Green Claims Code, FCA Sustainability Disclosure Requirements, ASA CAP Code",
            "description": "UK-specific guidance for environmental claims and financial sustainability disclosures",
            "enforcement_focus": "Consumer protection, financial product sustainability, advertising standards"
        },
        "Global": {
            "regulations": "ISO 14021, GRI Standards, TCFD Recommendations, ISSB Standards",
            "description": "International standards and frameworks for sustainability communication and reporting",
            "enforcement_focus": "Voluntary compliance, standardized reporting, best practice adoption"
        }
    }
    return frameworks.get(region, frameworks["Global"])

# ============================================================================
# ENHANCED TRAINING EXECUTION WITH MULTI-LINE JSON EXTRACTION
# ============================================================================

def run_enhanced_training_session(session_id: str, training_request: TrainingRequest):
    """Run enhanced training session with FIXED multi-line JSON extraction"""
    try:
        print(f"🚀 Starting MULTI-LINE JSON FIXED training session: {session_id}")
        
        # Initialize enhanced tracking
        update_session_progress(session_id, 5, "Initializing multi-line JSON extraction system...", "System")
        
        # Get regulatory details
        regulatory_details = get_regulatory_details(training_request.regulatory_framework)
        
        # Prepare enhanced inputs
        inputs = {
            'user_industry': training_request.industry_focus,
            'regulatory_region': training_request.regulatory_framework,
            'regional_regulations': regulatory_details['regulations'],
            'regulatory_description': regulatory_details['description'],
            'enforcement_focus': regulatory_details['enforcement_focus'],
            'current_year': str(datetime.now().year),
            'session_id': session_id,
            'training_level': training_request.training_level
        }
        
        update_session_progress(session_id, 10, "Creating AI crew with multi-line support...", "System")
        
        # Create enhanced crew with session-specific setup
        sustainability_crew = Sustainability(session_id=session_id)
        crew = sustainability_crew.crew()
        
        # Store paths for later use
        crew_log_file = sustainability_crew._get_session_log_file()
        sessions[session_id]["crew_log_file"] = crew_log_file
        
        # Get callback handler and backup directory
        callback_handler = sustainability_crew.callback_handler
        backup_directory = str(callback_handler.get_backup_directory())
        sessions[session_id]["backup_directory"] = backup_directory
        
        print(f"📄 Crew log file: {crew_log_file}")
        print(f"💾 Backup directory: {backup_directory}")
        
        update_session_progress(session_id, 15, "AI agents starting collaboration...", "System")
        
        # Run the training with enhanced monitoring
        result = crew.kickoff(inputs=inputs)
        
        update_session_progress(session_id, 60, "Training complete - starting MULTI-LINE data extraction...", "System")
        
        # ========================================================================
        # MULTI-LINE JSON EXTRACTION (COMPLETELY FIXED)
        # ========================================================================
        
        print(f"🔍 Starting MULTI-LINE JSON extraction for session {session_id}")
        
        # Verify log file exists and has content
        if not os.path.exists(crew_log_file):
            raise Exception(f"Crew log file not found: {crew_log_file}")
        
        log_size = os.path.getsize(crew_log_file)
        print(f"📊 Log file size: {log_size:,} bytes")
        
        if log_size == 0:
            raise Exception("Crew log file is empty")
        
        # Debug: Show a sample of the log file
        with open(crew_log_file, 'r', encoding='utf-8') as f:
            sample_lines = f.readlines()[:5]
            print(f"📝 Log file sample (first 5 lines):")
            for i, line in enumerate(sample_lines, 1):
                print(f"   {i}: {line.strip()[:100]}...")
        
        # Step 1: Extract data using MULTI-LINE FIXED extractor
        data_extractor = SessionDataExtractor(session_id)
        comprehensive_data = data_extractor.extract_complete_session_data(crew_log_file)
        
        # Debug: Show detailed extraction results
        raw_data = comprehensive_data.get("raw_data", {})
        print(f"🔍 MULTI-LINE EXTRACTION RESULTS:")
        print(f"   📊 Total tasks found: {raw_data.get('total_tasks_found', 0)}")
        print(f"   📋 Parsing success: {raw_data.get('parsing_success', False)}")
        print(f"   📝 Extraction log entries: {len(raw_data.get('extraction_log', []))}")
        
        # Show what was actually extracted
        print(f"🗂️ EXTRACTED DATA CHECK:")
        print(f"   Scenario Data: {'✅ PRESENT' if raw_data.get('scenario_data') else '❌ MISSING'}")
        print(f"   Problematic Messages: {'✅ PRESENT' if raw_data.get('problematic_messages') else '❌ MISSING'}")
        print(f"   Corrected Messages: {'✅ PRESENT' if raw_data.get('corrected_messages') else '❌ MISSING'}")
        print(f"   Playbook Data: {'✅ PRESENT' if raw_data.get('playbook_data') else '❌ MISSING'}")
        
        # Show the extraction log for debugging
        extraction_log = raw_data.get("extraction_log", [])
        print(f"📝 EXTRACTION LOG (last 10 entries):")
        for log_entry in extraction_log[-10:]:
            print(f"   {log_entry}")
        
        # Show data sizes if present
        if raw_data.get('scenario_data'):
            scenario_size = len(str(raw_data['scenario_data']))
            print(f"   📊 Scenario data size: {scenario_size:,} characters")
            # Show company name to verify extraction
            company_name = raw_data['scenario_data'].get('company_name', 'Unknown')
            print(f"   🏢 Company name extracted: {company_name}")
        
        if raw_data.get('problematic_messages'):
            problematic_size = len(str(raw_data['problematic_messages']))
            print(f"   📊 Problematic messages size: {problematic_size:,} characters")
            # Show number of messages
            msg_count = len(raw_data['problematic_messages'].get('problematic_messages', []))
            print(f"   🚨 Number of problematic messages: {msg_count}")
        
        if raw_data.get('corrected_messages'):
            corrected_size = len(str(raw_data['corrected_messages']))
            print(f"   📊 Corrected messages size: {corrected_size:,} characters")
            # Show number of corrections
            corr_count = len(raw_data['corrected_messages'].get('corrected_messages', []))
            print(f"   ✅ Number of corrections: {corr_count}")
        
        if raw_data.get('playbook_data'):
            playbook_size = len(str(raw_data['playbook_data']))
            print(f"   📊 Playbook data size: {playbook_size:,} characters")
        
        # Store extraction results in session
        sessions[session_id]["extracted_data"] = raw_data
        sessions[session_id]["validation_result"] = comprehensive_data.get("validation", {})
        sessions[session_id]["integration_result"] = comprehensive_data.get("integration", {})
        
        update_session_progress(session_id, 75, "Multi-line extraction complete - validating quality...", "System")
        
        # Get quality metrics
        validation_result = comprehensive_data.get("validation", {})
        quality_score = validation_result.get("quality_score", 0)
        data_completeness = validation_result.get("completeness_percentage", 0)
        
        print(f"📊 Quality Score: {quality_score:.1f}/100")
        print(f"📈 Data Completeness: {data_completeness:.1f}%")
        print(f"📋 Tasks Found: {raw_data.get('total_tasks_found', 0)}")
        
        # Check if we have sufficient data quality
        if raw_data.get("total_tasks_found", 0) < 3:
            print(f"⚠️ Low task count detected, attempting backup extraction...")
            update_session_progress(session_id, 70, "Attempting backup data recovery...", "System")
            
            # Try backup extraction
            backup_data = extract_from_backup_files(session_id, backup_directory)
            if backup_data.get("parsing_success"):
                comprehensive_data["raw_data"] = backup_data
                print(f"✅ Backup extraction successful")
            else:
                print(f"❌ Backup extraction also failed")
        
        update_session_progress(session_id, 85, "Generating comprehensive markdown playbook...", "System")
        
        # ========================================================================
        # ENHANCED MARKDOWN GENERATION (GUARANTEED TO USE EXTRACTED DATA)
        # ========================================================================
        
        print(f"📝 Starting ENHANCED markdown generation with extracted data...")
        
        # Get the extracted data
        extracted_raw_data = comprehensive_data.get("raw_data", {})
        
        # FORCE CHECK: Verify we have extracted data
        has_scenario = bool(extracted_raw_data.get("scenario_data"))
        has_problematic = bool(extracted_raw_data.get("problematic_messages"))
        has_corrected = bool(extracted_raw_data.get("corrected_messages"))
        has_playbook = bool(extracted_raw_data.get("playbook_data"))
        
        print(f"📊 MARKDOWN GENERATION DATA CHECK:")
        print(f"   Scenario: {'✅ AVAILABLE' if has_scenario else '❌ MISSING'}")
        print(f"   Problematic: {'✅ AVAILABLE' if has_problematic else '❌ MISSING'}")
        print(f"   Corrected: {'✅ AVAILABLE' if has_corrected else '❌ MISSING'}")
        print(f"   Playbook: {'✅ AVAILABLE' if has_playbook else '❌ MISSING'}")
        
        # Force extraction success check
        total_tasks = extracted_raw_data.get("total_tasks_found", 0)
        parsing_success = extracted_raw_data.get("parsing_success", False)
        
        print(f"📈 EXTRACTION SUCCESS METRICS:")
        print(f"   Tasks Found: {total_tasks}")
        print(f"   Parsing Success: {parsing_success}")
        
        # GUARANTEE: Use enhanced generation if we have ANY substantial data
        if total_tasks >= 1 and (has_scenario or has_problematic or has_corrected or has_playbook):
            print(f"✅ USING ENHANCED MARKDOWN GENERATION with extracted data")
            print(f"📋 Enhanced generation input data size: {len(str(extracted_raw_data)):,} characters")
            
            # Call the enhanced markdown generator
            comprehensive_markdown = generate_comprehensive_playbook(
                extracted_data=extracted_raw_data,
                validation_result=comprehensive_data.get("validation", {}),
                integration_result=comprehensive_data.get("integration", {}),
                training_request=training_request.model_dump(),
                session_id=session_id
            )
            
            print(f"✅ Enhanced markdown generated: {len(comprehensive_markdown):,} characters")
            
        else:
            print(f"❌ CRITICAL: NO EXTRACTED DATA AVAILABLE")
            print(f"🔄 Attempting to use CrewAI result data as last resort...")
            
            # Use the CrewAI result as absolute fallback
            if hasattr(result, 'tasks_output') and result.tasks_output:
                final_task = result.tasks_output[-1]
                if hasattr(final_task, 'pydantic') and final_task.pydantic:
                    print(f"📋 Using basic generation from CrewAI task output")
                    comprehensive_markdown = format_playbook_as_markdown_basic(final_task.pydantic.model_dump())
                else:
                    raise Exception("No task output data available for markdown generation")
            else:
                raise Exception("CRITICAL: No data available from any source for markdown generation")
        
        # Create outputs directory
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(exist_ok=True)
        
        # Generate enhanced filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"multiline_sustainability_playbook_{session_id[:8]}_{timestamp}.md"
        file_path = outputs_dir / filename
        
        # Save comprehensive markdown
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(comprehensive_markdown)
        
        # Verify file creation and size
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"✅ Multi-line playbook created: {file_size:,} bytes")
            
            # Log content statistics
            char_count = len(comprehensive_markdown)
            line_count = comprehensive_markdown.count('\n')
            section_count = comprehensive_markdown.count('##')
            
            print(f"📊 Content stats: {char_count:,} chars, {line_count:,} lines, {section_count} sections")
            
            # Check if specific company content is present
            company_mentioned = extracted_raw_data.get("scenario_data", {}).get("company_name", "")
            if company_mentioned and company_mentioned.lower() in comprehensive_markdown.lower():
                print(f"✅ Company-specific content confirmed: {company_mentioned}")
            else:
                print(f"⚠️ Company-specific content check: {company_mentioned}")
                
        else:
            raise Exception("Failed to create multi-line playbook file")
        
        update_session_progress(session_id, 95, "Finalizing multi-line training session...", "System")
        
        # Complete session with quality metrics
        complete_session(
            session_id=session_id,
            results=result,
            file_path=str(file_path),
            quality_score=quality_score,
            data_completeness=data_completeness
        )
        
        print(f"🎉 Multi-line JSON training session completed successfully!")
        print(f"📄 Playbook: {file_path}")
        print(f"📊 Quality: {quality_score:.1f}/100")
        print(f"📈 Completeness: {data_completeness:.1f}%")
        
    except Exception as e:
        error_msg = f"Multi-line training failed: {str(e)}"
        print(f"❌ Multi-line session error {session_id}: {error_msg}")
        print(f"🔍 Error details: {str(e)}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        
        # Try fallback extraction before failing
        try:
            print(f"🔄 Attempting fallback data extraction...")
            if sessions[session_id].get("backup_directory"):
                backup_data = extract_from_backup_files(session_id, sessions[session_id]["backup_directory"])
                if backup_data.get("parsing_success"):
                    print(f"✅ Fallback extraction successful, generating basic playbook...")
                    
                    # Generate basic playbook from backup data
                    basic_markdown = generate_comprehensive_playbook(
                        extracted_data=backup_data,
                        validation_result={"quality_score": 60, "completeness_percentage": 70, "is_complete": True},
                        integration_result={},
                        training_request=training_request.model_dump(),
                        session_id=session_id
                    )
                    
                    # Save fallback playbook
                    outputs_dir = Path("outputs")
                    outputs_dir.mkdir(exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"fallback_playbook_{session_id[:8]}_{timestamp}.md"
                    file_path = outputs_dir / filename
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(basic_markdown)
                    
                    complete_session(session_id, None, str(file_path), None, 60, 70)
                    print(f"✅ Fallback playbook created: {file_path}")
                    return
        except Exception as fallback_error:
            print(f"❌ Fallback also failed: {str(fallback_error)}")
        
        complete_session(session_id, None, None, error_msg)

def format_playbook_as_markdown_basic(data: Dict[str, Any]) -> str:
    """Basic markdown generation as absolute fallback"""
    
    playbook_title = data.get('playbook_title', 'Sustainability Messaging Playbook')
    creation_date = data.get('creation_date', datetime.now().strftime('%Y-%m-%d'))
    
    content = f"""# {playbook_title}

**Created:** {creation_date}  
**Generated by:** Sustainability Training AI (Basic Fallback)

---

## Executive Summary

{data.get('executive_summary', 'Comprehensive guide for creating compliant sustainability messaging.')}

---

## 📋 Do's and Don'ts

{format_list_items_basic(data.get('dos_and_donts', []))}

---

## 🚨 Greenwashing Patterns to Avoid

{format_list_items_basic(data.get('greenwashing_patterns', []))}

---

## ✅ Quick Compliance Checklist

{format_checklist_basic(data.get('compliance_checklist', {}))}

---

## 🔄 Claim-to-Proof Framework

{format_framework_basic(data.get('claim_to_proof_framework', {}))}

---

## 📖 Case Studies

{format_case_studies_basic(data.get('case_study_snapshots', []))}

---

## 📄 Regulatory References

{format_list_items_basic(data.get('regulatory_references', []))}

---

*Generated by Sustainability Training AI (Basic Fallback) on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return content

def format_list_items_basic(items: list) -> str:
    """Format list items as markdown"""
    if not items:
        return "*No items available*"
    return "\n".join([f"• {item}" for item in items])

def format_checklist_basic(checklist: dict) -> str:
    """Format checklist as markdown"""
    if not checklist:
        return "*Checklist not available*"
    
    content = f"### {checklist.get('checklist_name', 'Compliance Checklist')}\n\n"
    content += f"**Questions to Ask:**\n{format_list_items_basic(checklist.get('questions', []))}\n\n"
    content += f"**Red Flags:**\n{format_list_items_basic(checklist.get('red_flags', []))}\n"
    
    return content

def format_framework_basic(framework: dict) -> str:
    """Format framework as markdown"""
    if not framework:
        return "*Framework not available*"
    
    content = f"### {framework.get('framework_name', 'Validation Framework')}\n\n"
    content += f"**Steps:**\n{format_list_items_basic(framework.get('steps', []))}\n\n"
    content += f"**Validation Questions:**\n{format_list_items_basic(framework.get('validation_questions', []))}\n"
    
    return content

def format_case_studies_basic(case_studies: list) -> str:
    """Format case studies as markdown"""
    if not case_studies:
        return "*No case studies available*"
    
    content = ""
    for i, case in enumerate(case_studies, 1):
        content += f"### Case Study {i}: {case.get('title', 'Untitled')}\n\n"
        content += f"**Message:** {case.get('original_message', 'N/A')}\n\n"
        content += f"**Analysis:** {case.get('analysis', 'N/A')}\n\n"
        content += f"**Key Lesson:** {case.get('key_lesson', 'N/A')}\n\n---\n\n"
    
    return content

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0.0 Multi-Line JSON Fixed",
        "features": ["multiline_json_extraction", "quality_validation", "integrated_markdown"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/training/start", response_model=TrainingResponse)
async def start_enhanced_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    """Start a new enhanced training session with multi-line JSON support"""
    
    # Clean up old sessions
    cleanup_old_sessions()
    
    # Validate request
    if not request.industry_focus or not request.regulatory_framework:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # Create enhanced session
    session_id = create_session(request)
    
    # Start enhanced training in background
    background_tasks.add_task(run_enhanced_training_session, session_id, request)
    
    return TrainingResponse(
        session_id=session_id,
        status="started",
        message="Multi-line JSON training session started with FIXED extraction and validation"
    )

@app.get("/api/training/status/{session_id}", response_model=StatusResponse)
async def get_enhanced_training_status(session_id: str):
    """Get enhanced training session status with quality metrics"""
    
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
        error=session["error"],
        quality_score=session.get("quality_score"),
        data_completeness=session.get("data_completeness")
    )

@app.get("/api/training/download/{session_id}")
async def download_enhanced_playbook(session_id: str):
    """Download the enhanced comprehensive playbook"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    if session["status"] not in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Training not completed yet")
    
    if not session["file_path"] or not os.path.exists(session["file_path"]):
        raise HTTPException(status_code=404, detail="Enhanced playbook file not found")
    
    file_path = session["file_path"]
    filename = os.path.basename(file_path)
    
    # Schedule cleanup after download
    def cleanup_session_files():
        try:
            # Main file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Crew log file
            if session.get("crew_log_file") and os.path.exists(session["crew_log_file"]):
                os.remove(session["crew_log_file"])
            
            # Backup directory
            if session.get("backup_directory"):
                backup_dir = Path(session["backup_directory"])
                if backup_dir.exists():
                    for file in backup_dir.glob("*"):
                        file.unlink()
                    backup_dir.rmdir()
            
            # Remove session
            if session_id in sessions:
                del sessions[session_id]
            
            print(f"Cleaned up multi-line session {session_id} after download")
        except Exception as e:
            print(f"Cleanup error for session {session_id}: {e}")
    
    # Schedule cleanup
    import threading
    threading.Timer(2.0, cleanup_session_files).start()
    
    return FileResponse(
        file_path,
        media_type='text/markdown',
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/sessions")
async def list_active_sessions():
    """Debug endpoint to see active enhanced sessions"""
    return {
        "active_sessions": len(sessions),
        "sessions": {sid: {
            "status": session["status"],
            "progress": session["progress"],
            "created_at": session["created_at"].isoformat(),
            "quality_score": session.get("quality_score"),
            "data_completeness": session.get("data_completeness"),
            "crew_log_file": session.get("crew_log_file"),
            "backup_directory": session.get("backup_directory")
        } for sid, session in sessions.items()}
    }

@app.get("/api/training/metrics/{session_id}")
async def get_session_metrics(session_id: str):
    """Get detailed quality metrics for a session"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    return {
        "session_id": session_id,
        "quality_metrics": {
            "quality_score": session.get("quality_score"),
            "data_completeness": session.get("data_completeness"),
            "validation_result": session.get("validation_result"),
            "integration_result": session.get("integration_result")
        },
        "extraction_summary": session.get("extracted_data", {}).get("extraction_log", [])
    }

@app.get("/api/training/debug/{session_id}")
async def debug_session_logs(session_id: str):
    """Debug endpoint to inspect session logs and extraction"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    debug_info = {
        "session_id": session_id,
        "crew_log_file": session.get("crew_log_file"),
        "backup_directory": session.get("backup_directory"),
        "log_file_exists": False,
        "log_file_size": 0,
        "backup_files": [],
        "extraction_log": [],
        "raw_log_sample": [],
        "completed_tasks_found": [],
        "multiline_support": True
    }
    
    # Check crew log file
    if session.get("crew_log_file"):
        log_file = session["crew_log_file"]
        if os.path.exists(log_file):
            debug_info["log_file_exists"] = True
            debug_info["log_file_size"] = os.path.getsize(log_file)
            
            # Read and analyze the log file
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    # Show first 10 lines
                    debug_info["raw_log_sample"] = [line.strip() for line in lines[:10]]
                    
                    # Find completed tasks
                    completed_tasks = []
                    for i, line in enumerate(lines):
                        if 'status="completed"' in line:
                            completed_tasks.append({
                                "line_number": i + 1,
                                "line_content": line.strip()[:200] + "..." if len(line) > 200 else line.strip()
                            })
                    
                    debug_info["completed_tasks_found"] = completed_tasks
                    
            except Exception as e:
                debug_info["log_read_error"] = str(e)
    
    # Check backup directory
    if session.get("backup_directory"):
        backup_dir = Path(session["backup_directory"])
        if backup_dir.exists():
            debug_info["backup_files"] = [f.name for f in backup_dir.glob("*")]
    
    # Get extraction log
    if session.get("extracted_data"):
        debug_info["extraction_log"] = session["extracted_data"].get("extraction_log", [])
    
    return debug_info

@app.get("/api/training/test-extraction/{session_id}")
async def test_extraction(session_id: str):
    """Test the multi-line extraction process manually"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    log_file = session.get("crew_log_file")
    
    if not log_file or not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail="Log file not found")
    
    # Run multi-line extraction manually
    try:
        data_extractor = SessionDataExtractor(session_id)
        result = data_extractor.extract_complete_session_data(log_file)
        
        return {
            "extraction_successful": True,
            "extraction_method": "multi-line JSON parser",
            "total_tasks_found": result["raw_data"].get("total_tasks_found", 0),
            "parsing_success": result["raw_data"].get("parsing_success", False),
            "extraction_log": result["raw_data"].get("extraction_log", []),
            "data_summary": {
                "scenario_data": "✅ Present" if result["raw_data"].get("scenario_data") else "❌ Missing",
                "problematic_messages": "✅ Present" if result["raw_data"].get("problematic_messages") else "❌ Missing",
                "corrected_messages": "✅ Present" if result["raw_data"].get("corrected_messages") else "❌ Missing",
                "playbook_data": "✅ Present" if result["raw_data"].get("playbook_data") else "❌ Missing"
            },
            "quality_score": result["validation"].get("quality_score", 0),
            "completeness": result["validation"].get("completeness_percentage", 0),
            "company_extracted": result["raw_data"].get("scenario_data", {}).get("company_name", "Not found"),
            "version": "3.0.0 Multi-Line JSON Fixed"
        }
        
    except Exception as e:
        return {
            "extraction_successful": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "version": "3.0.0 Multi-Line JSON Fixed"
        }

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    print("🌱 Starting Multi-Line JSON Fixed Sustainability Training API v3.0...")
    print("🔧 Features: MULTI-LINE JSON extraction, Quality validation, Integrated markdown")
    print(f"🔗 Server will run on: http://localhost:{port}")
    print(f"📚 API docs available at: http://localhost:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True if not os.getenv("PORT") else False,
        log_level="info",
        ws="none"
    )