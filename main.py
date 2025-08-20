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
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Suppress specific warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic._internal._config")
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
# TRAINING EXECUTION
# ============================================================================

def run_training_session(session_id: str, training_request: TrainingRequest):
    """Run the actual training session"""
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
        
        # Create and run crew
        sustainability_crew = Sustainability()
        crew = sustainability_crew.crew()
        
        update_session_progress(session_id, 15, "AI agents collaborating...", "System")
        
        # Run the training
        result = crew.kickoff(inputs=inputs)
        
        # Generate markdown file
        update_session_progress(session_id, 90, "Generating playbook file...", "System")
        
        # Create outputs directory if needed
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(exist_ok=True)
        
        # Generate file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sustainability_playbook_{session_id[:8]}_{timestamp}.md"
        file_path = outputs_dir / filename
        
        # Format and save playbook
        if hasattr(result, 'tasks_output') and result.tasks_output:
            final_task = result.tasks_output[-1]
            if hasattr(final_task, 'pydantic') and final_task.pydantic:
                markdown_content = format_playbook_as_markdown(final_task.pydantic.model_dump())
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
        
        # Complete session
        complete_session(session_id, result, str(file_path))
        
    except Exception as e:
        error_msg = f"Training failed: {str(e)}"
        print(f"Error in session {session_id}: {error_msg}")
        complete_session(session_id, None, None, error_msg)

def format_playbook_as_markdown(data: Dict[str, Any]) -> str:
    """Convert playbook data to markdown format"""
    
    playbook_title = data.get('playbook_title', 'Sustainability Messaging Playbook')
    creation_date = data.get('creation_date', datetime.now().strftime('%Y-%m-%d'))
    
    content = f"""# {playbook_title}

**Created:** {creation_date}  
**Generated by:** Sustainability Training AI

---

## Executive Summary

{data.get('executive_summary', 'Comprehensive guide for creating compliant sustainability messaging.')}

---

## 📋 Do's and Don'ts

{format_list_items(data.get('dos_and_donts', []))}

---

## 🚨 Greenwashing Patterns to Avoid

{format_list_items(data.get('greenwashing_patterns', []))}

---

## ✅ Quick Compliance Checklist

{format_checklist(data.get('compliance_checklist', {}))}

---

## 🔄 Claim-to-Proof Framework

{format_framework(data.get('claim_to_proof_framework', {}))}

---

## 📖 Case Studies

{format_case_studies(data.get('case_study_snapshots', []))}

---

## 📄 Regulatory References

{format_list_items(data.get('regulatory_references', []))}

---

*Generated by Sustainability Training AI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return content

def format_list_items(items: list) -> str:
    """Format list items as markdown"""
    if not items:
        return "*No items available*"
    return "\n".join([f"• {item}" for item in items])

def format_checklist(checklist: dict) -> str:
    """Format checklist as markdown"""
    if not checklist:
        return "*Checklist not available*"
    
    content = f"### {checklist.get('checklist_name', 'Compliance Checklist')}\n\n"
    content += f"**Questions to Ask:**\n{format_list_items(checklist.get('questions', []))}\n\n"
    content += f"**Red Flags:**\n{format_list_items(checklist.get('red_flags', []))}\n"
    
    return content

def format_framework(framework: dict) -> str:
    """Format framework as markdown"""
    if not framework:
        return "*Framework not available*"
    
    content = f"### {framework.get('framework_name', 'Validation Framework')}\n\n"
    content += f"**Steps:**\n{format_list_items(framework.get('steps', []))}\n\n"
    content += f"**Validation Questions:**\n{format_list_items(framework.get('validation_questions', []))}\n"
    
    return content

def format_case_studies(case_studies: list) -> str:
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
        message="Training session started successfully"
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
    """Download the generated playbook"""
    
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
    
    print("🌱 Starting Sustainability Training API...")
    print(f"🔗 Server will run on: http://localhost:{port}")
    print(f"📚 API docs available at: http://localhost:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True if not os.getenv("PORT") else False,  # Only reload in development
        log_level="info"
    )