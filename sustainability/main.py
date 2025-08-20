#!/usr/bin/env python
"""
FastAPI Backend for Sustainability Training - COMPLETE DATA DUMP VERSION
Dumps everything from crew execution and creates comprehensive reports
"""

import os
import sys
import uuid
import asyncio
import warnings
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
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
    description="AI-powered sustainability messaging training with complete data dump",
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
    """Create a new training session"""
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
        "progress_updates": []
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
    """Remove sessions older than 2 hours"""
    cutoff_time = datetime.now() - timedelta(hours=2)
    expired_sessions = [
        sid for sid, session in sessions.items()
        if session["created_at"] < cutoff_time
    ]
    
    for sid in expired_sessions:
        # Clean up any files
        if sessions[sid].get("file_path") and os.path.exists(sessions[sid]["file_path"]):
            try:
                os.remove(sessions[sid]["file_path"])
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
# DATA EXTRACTION AND PROCESSING FUNCTIONS
# ============================================================================

def extract_all_detailed_data(result) -> Dict[str, Any]:
    """Extract ALL detailed data from result object"""
    detailed_data = {
        "tasks": [],
        "raw_result": str(result),
        "extraction_log": [],
        "metadata": {
            "extraction_timestamp": datetime.now().isoformat(),
            "result_type": type(result).__name__
        }
    }
    
    print("🔍 Starting comprehensive data extraction...")
    
    if hasattr(result, 'tasks_output') and result.tasks_output:
        detailed_data["extraction_log"].append(f"Found {len(result.tasks_output)} task outputs")
        
        for i, task_output in enumerate(result.tasks_output):
            print(f"📋 Processing task {i+1}...")
            
            task_data = {
                "task_number": i + 1,
                "raw_output": str(task_output),
                "task_type": type(task_output).__name__,
                "available_attributes": [attr for attr in dir(task_output) if not attr.startswith('_')]
            }
            
            # Try to get pydantic data (most likely location of detailed data)
            if hasattr(task_output, 'pydantic') and task_output.pydantic:
                try:
                    structured_data = task_output.pydantic.model_dump()
                    task_data["structured_data"] = structured_data
                    task_data["pydantic_type"] = type(task_output.pydantic).__name__
                    detailed_data["extraction_log"].append(f"✅ Task {i+1}: Got structured data ({len(str(structured_data))} chars)")
                    print(f"✅ Task {i+1}: Extracted structured data")
                except Exception as e:
                    detailed_data["extraction_log"].append(f"❌ Task {i+1}: Error getting structured data: {e}")
                    print(f"❌ Task {i+1}: Error getting structured data: {e}")
            else:
                detailed_data["extraction_log"].append(f"⚠️ Task {i+1}: No pydantic data found")
                print(f"⚠️ Task {i+1}: No pydantic data found")
            
            # Try to get raw data
            if hasattr(task_output, 'raw'):
                task_data["raw"] = str(task_output.raw)
                detailed_data["extraction_log"].append(f"📄 Task {i+1}: Got raw data")
            
            # Try to get other common attributes
            for attr in ['json_dict', 'output', 'result', 'agent', 'description']:
                if hasattr(task_output, attr):
                    try:
                        value = getattr(task_output, attr)
                        task_data[attr] = str(value) if not isinstance(value, (dict, list)) else value
                        detailed_data["extraction_log"].append(f"📎 Task {i+1}: Got {attr}")
                    except Exception as e:
                        detailed_data["extraction_log"].append(f"❌ Task {i+1}: Error getting {attr}: {e}")
            
            detailed_data["tasks"].append(task_data)
    else:
        detailed_data["extraction_log"].append("❌ No tasks_output found in result")
        print("❌ No tasks_output found in result")
    
    print(f"✅ Extraction complete: {len(detailed_data['tasks'])} tasks processed")
    return detailed_data

def create_comprehensive_markdown(data: Dict[str, Any], session_id: str, training_request: TrainingRequest) -> str:
    """Create comprehensive markdown from ALL extracted data"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    content = f"""# Complete Sustainability Training Report

**🤖 Generated by:** Sustainability Training AI Crew  
**📅 Timestamp:** {timestamp}  
**🆔 Session ID:** {session_id}  
**🏢 Industry Focus:** {training_request.industry_focus}  
**🌍 Regulatory Framework:** {training_request.regulatory_framework}  
**📊 Training Level:** {training_request.training_level}  

---

## 📊 Extraction Summary

**📋 Tasks Processed:** {len(data.get('tasks', []))}  
**🔍 Extraction Method:** Comprehensive data dump  
**⏰ Extraction Time:** {data.get('metadata', {}).get('extraction_timestamp', 'Unknown')}  

### 📝 Extraction Log
{format_extraction_log(data.get('extraction_log', []))}

---

## 🎯 Complete Training Results

This report contains **every detail** from your AI training session, including all agent outputs, structured data, and raw results.

"""
    
    # Process each task
    for task in data.get('tasks', []):
        content += f"""## 📋 Task {task.get('task_number', 'Unknown')} - {task.get('pydantic_type', 'Unknown Type')}

**Task Type:** {task.get('task_type', 'Unknown')}  
**Available Attributes:** {', '.join(task.get('available_attributes', []))}  

"""
        
        # Show structured data if available
        if 'structured_data' in task:
            content += format_structured_data_section(task['structured_data'], task.get('task_number', 0))
        
        # Show raw output (truncated)
        content += f"""### 📄 Raw Task Output
<details>
<summary>Click to view raw output</summary>

```
{task.get('raw_output', 'No raw output')[:2000]}{"..." if len(task.get('raw_output', '')) > 2000 else ""}
```

</details>

---

"""
    
    # Add complete raw result at the end
    content += f"""## 🔧 Complete Raw Result Object

<details>
<summary>Click to view complete result object ({len(data.get('raw_result', '')):,} characters)</summary>

```
{data.get('raw_result', 'No raw result')[:5000]}{"..." if len(data.get('raw_result', '')) > 5000 else ""}
```

</details>

---

## 🎯 Training Session Summary

This comprehensive report contains **every piece of data** generated during your sustainability training session:

✅ **Complete Agent Outputs** - All detailed JSON data from each AI agent  
✅ **Structured Business Scenarios** - Full company profiles and regulatory contexts  
✅ **Detailed Problematic Message Analysis** - Complete breakdown of issues and violations  
✅ **Comprehensive Best Practice Corrections** - All improvements and explanations  
✅ **Complete Implementation Playbooks** - Full frameworks and checklists  
✅ **All Research Sources** - Every reference and real-world example used  

### 🚀 How to Use This Report

- **📋 For Immediate Implementation** - Use the structured data sections
- **🔍 For Deep Analysis** - Review the complete agent reasoning
- **📚 For Team Training** - Share the case studies and frameworks
- **⚖️ For Compliance** - Use the regulatory references and checklists

---

*Complete report generated on {timestamp}*  
*All data extracted using comprehensive dump method*
"""
    
    return content

def format_extraction_log(log_entries: list) -> str:
    """Format the extraction log entries"""
    if not log_entries:
        return "*No extraction log entries*"
    
    formatted = ""
    for entry in log_entries:
        if "✅" in entry:
            formatted += f"✅ {entry}\n"
        elif "❌" in entry:
            formatted += f"❌ {entry}\n"
        elif "⚠️" in entry:
            formatted += f"⚠️ {entry}\n"
        else:
            formatted += f"📎 {entry}\n"
    
    return formatted

def format_structured_data_section(structured_data: Dict[str, Any], task_number: int) -> str:
    """Format structured data into readable sections"""
    
    content = f"### 📊 Structured Data (Task {task_number})\n\n"
    
    # Try to identify what type of data this is and format accordingly
    if 'problematic_messages' in structured_data:
        content += format_problematic_messages(structured_data)
    elif 'corrected_messages' in structured_data:
        content += format_corrected_messages(structured_data)
    elif 'company_name' in structured_data:
        content += format_business_scenario(structured_data)
    elif 'playbook_title' in structured_data:
        content += format_playbook_data(structured_data)
    else:
        # Generic formatting
        content += f"```json\n{json.dumps(structured_data, indent=2)}\n```\n\n"
    
    return content

def format_problematic_messages(data: Dict[str, Any]) -> str:
    """Format problematic messages data"""
    content = f"**Scenario:** {data.get('scenario_reference', 'N/A')}\n\n"
    content += f"**Regulatory Landscape:** {data.get('regulatory_landscape', 'N/A')}\n\n"
    
    content += "#### 🚨 Problematic Messages\n\n"
    for msg in data.get('problematic_messages', []):
        content += f"**Message {msg.get('id', 'Unknown')}:** {msg.get('message', 'N/A')}\n\n"
        content += f"**Problems:** {', '.join(msg.get('problems_identified', []))}\n\n"
        content += f"**Violations:** {', '.join(msg.get('regulatory_violations', []))}\n\n"
        content += f"**Why Problematic:** {msg.get('why_problematic', 'N/A')}\n\n"
        content += "---\n\n"
    
    return content

def format_corrected_messages(data: Dict[str, Any]) -> str:
    """Format corrected messages data"""
    content = f"**Scenario:** {data.get('scenario_reference', 'N/A')}\n\n"
    
    content += "#### ✅ Corrected Messages\n\n"
    for msg in data.get('corrected_messages', []):
        content += f"**Original ID:** {msg.get('original_message_id', 'Unknown')}\n\n"
        content += f"**Corrected Message:** {msg.get('corrected_message', 'N/A')}\n\n"
        content += f"**Changes Made:** {', '.join(msg.get('changes_made', []))}\n\n"
        content += f"**Compliance Notes:** {msg.get('compliance_notes', 'N/A')}\n\n"
        content += "---\n\n"
    
    return content

def format_business_scenario(data: Dict[str, Any]) -> str:
    """Format business scenario data"""
    content = f"**Company:** {data.get('company_name', 'N/A')}\n\n"
    content += f"**Industry:** {data.get('industry', 'N/A')}\n\n"
    content += f"**Location:** {data.get('location', 'N/A')}\n\n"
    content += f"**Product/Service:** {data.get('product_service', 'N/A')}\n\n"
    content += f"**Target Audience:** {data.get('target_audience', 'N/A')}\n\n"
    
    if 'marketing_objectives' in data:
        content += "**Marketing Objectives:**\n"
        for obj in data['marketing_objectives']:
            content += f"- {obj}\n"
        content += "\n"
    
    return content

def format_playbook_data(data: Dict[str, Any]) -> str:
    """Format playbook data"""
    content = f"**Title:** {data.get('playbook_title', 'N/A')}\n\n"
    content += f"**Target Audience:** {data.get('target_audience', 'N/A')}\n\n"
    content += f"**Executive Summary:** {data.get('executive_summary', 'N/A')}\n\n"
    
    return content

# ============================================================================
# TRAINING EXECUTION WITH COMPLETE DATA DUMP
# ============================================================================

def run_training_session(session_id: str, training_request: TrainingRequest):
    """Run training and dump EVERYTHING to files"""
    try:
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
        
        # Create and run crew
        sustainability_crew = Sustainability()
        crew = sustainability_crew.crew()
        
        update_session_progress(session_id, 15, "AI agents collaborating...", "System")
        
        # Run the training
        result = crew.kickoff(inputs=inputs)
        
        update_session_progress(session_id, 70, "Training complete, saving ALL data...", "System")
        
        # Create outputs directory if needed
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(exist_ok=True)
        
        # Generate file names
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. DUMP EVERYTHING TO TXT FILE
        dump_filename = f"complete_result_dump_{session_id[:8]}_{timestamp}.txt"
        dump_file_path = outputs_dir / dump_filename
        
        with open(dump_file_path, 'w', encoding='utf-8') as f:
            f.write("COMPLETE CREW RESULT DUMP\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Session ID: {session_id}\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"Industry: {training_request.industry_focus}\n")
            f.write(f"Framework: {training_request.regulatory_framework}\n\n")
            
            # Dump the entire result object
            f.write("RESULT OBJECT:\n")
            f.write("-" * 30 + "\n")
            f.write(str(result) + "\n\n")
            
            # Dump tasks_output if it exists
            if hasattr(result, 'tasks_output'):
                f.write(f"TASKS OUTPUT ({len(result.tasks_output)} tasks):\n")
                f.write("-" * 30 + "\n")
                for i, task_output in enumerate(result.tasks_output):
                    f.write(f"\nTASK {i+1}:\n")
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
                    
                    # Try to get all attributes
                    f.write(f"All attributes: {[attr for attr in dir(task_output) if not attr.startswith('_')]}\n")
                    f.write("-" * 20 + "\n")
            
            # Try other attributes
            f.write("\nOTHER RESULT ATTRIBUTES:\n")
            f.write("-" * 30 + "\n")
            for attr in dir(result):
                if not attr.startswith('_'):
                    try:
                        value = getattr(result, attr)
                        f.write(f"{attr}: {value}\n")
                    except:
                        f.write(f"{attr}: <could not access>\n")
        
        update_session_progress(session_id, 80, "Extracting detailed data...", "System")
        
        # 2. EXTRACT ALL THE DETAILED DATA
        all_detailed_data = extract_all_detailed_data(result)
        
        update_session_progress(session_id, 90, "Creating comprehensive markdown...", "System")
        
        # 3. CREATE COMPREHENSIVE MARKDOWN
        md_filename = f"comprehensive_sustainability_report_{session_id[:8]}_{timestamp}.md"
        md_file_path = outputs_dir / md_filename
        
        markdown_content = create_comprehensive_markdown(all_detailed_data, session_id, training_request)
        
        with open(md_file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        update_session_progress(session_id, 95, "Finalizing files...", "System")
        
        print(f"✅ Files created:")
        print(f"📄 Complete dump: {dump_file_path} ({os.path.getsize(dump_file_path):,} bytes)")
        print(f"📄 Comprehensive markdown: {md_file_path} ({os.path.getsize(md_file_path):,} bytes)")
        
        # Complete session with markdown file
        complete_session(session_id, result, str(md_file_path))
        
    except Exception as e:
        error_msg = f"Training failed: {str(e)}"
        print(f"❌ Error in session {session_id}: {error_msg}")
        complete_session(session_id, None, None, error_msg)

# ============================================================================
# API ENDPOINTS
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
        message="Training session started with complete data dump"
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
    """Download the generated comprehensive report"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Training not completed yet")
    
    if not session["file_path"] or not os.path.exists(session["file_path"]):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    file_path = session["file_path"]
    filename = os.path.basename(file_path)
    
    # Return file and schedule cleanup
    def cleanup_file():
        try:
            os.remove(file_path)
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
            "created_at": session["created_at"].isoformat()
        } for sid, session in sessions.items()}
    }

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    print("🌱 Starting Sustainability Training API with Complete Data Dump...")
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