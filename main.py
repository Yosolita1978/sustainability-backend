#!/usr/bin/env python
"""
Clean FastAPI Backend for Sustainability Training
Direct artifact generation - no log parsing complexity
"""

import os
import sys
import uuid
import warnings
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Suppress specific warnings from dependencies
# Suppress specific warnings from dependencies until they update to newer versions
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd.segmenter")
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd.lang.arabic")
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd.lang.persian")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic._internal._config")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets.legacy")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn.protocols.websockets.websockets_impl")
# Add sustainability module to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import clean crew (will be modified)
from sustainability.crew import Sustainability

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# FastAPI app setup
app = FastAPI(
    title="Clean Sustainability Training API",
    description="AI-powered sustainability messaging training with direct artifact generation",
    version="2.0.0"
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

# ============================================================================
# SESSION MANAGEMENT (SIMPLIFIED)
# ============================================================================

# Clean session storage
sessions: Dict[str, Dict[str, Any]] = {}

def create_session(training_request: TrainingRequest) -> str:
    """Create a new training session"""
    session_id = str(uuid.uuid4())
    
    # Create session artifact directory
    artifact_dir = Path("outputs") / session_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    
    sessions[session_id] = {
        "id": session_id,
        "status": "created",
        "progress": 0,
        "current_step": "Initializing session...",
        "created_at": datetime.now(),
        "completed_at": None,
        "error": None,
        "request": training_request.model_dump(),
        "artifact_directory": str(artifact_dir),
        "playbook_file": None
    }
    
    return session_id

def update_session_progress(session_id: str, progress: int, step: str):
    """Update session progress"""
    if session_id in sessions:
        sessions[session_id]["progress"] = progress
        sessions[session_id]["current_step"] = step
        print(f"Session {session_id}: {progress}% - {step}")

def complete_session(session_id: str, playbook_file: str = None, error: str = None):
    """Mark session as completed"""
    if session_id in sessions:
        sessions[session_id]["completed_at"] = datetime.now()
        sessions[session_id]["playbook_file"] = playbook_file
        
        if error:
            sessions[session_id]["status"] = "failed"
            sessions[session_id]["error"] = error
            sessions[session_id]["progress"] = 0
            sessions[session_id]["current_step"] = f"Training failed: {error}"
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
        session = sessions[sid]
        
        # Clean up artifact directory
        if session.get("artifact_directory"):
            artifact_dir = Path(session["artifact_directory"])
            if artifact_dir.exists():
                try:
                    for file in artifact_dir.glob("*"):
                        file.unlink()
                    artifact_dir.rmdir()
                except Exception as e:
                    print(f"Cleanup error for {sid}: {e}")
        
        del sessions[sid]
        print(f"Cleaned up expired session: {sid}")

def get_regulatory_details(region: str) -> Dict[str, str]:
    """Get regulatory details for the region"""
    frameworks = {
        "EU": {
            "regulations": "EU Green Claims Directive, CSRD, EU Taxonomy Regulation",
            "description": "European Union sustainability regulations focusing on green claims substantiation",
            "enforcement_focus": "Mandatory substantiation, corporate transparency, taxonomy alignment"
        },
        "USA": {
            "regulations": "FTC Green Guides, SEC Climate Disclosure Rules, EPA Green Power Partnership", 
            "description": "US federal guidance and rules for environmental marketing claims",
            "enforcement_focus": "Truthful advertising, climate risk disclosure, renewable energy verification"
        },
        "UK": {
            "regulations": "CMA Green Claims Code, FCA Sustainability Disclosure Requirements, ASA CAP Code",
            "description": "UK-specific guidance for environmental claims and financial sustainability disclosures",
            "enforcement_focus": "Consumer protection, financial product sustainability, advertising standards"
        },
        "Global": {
            "regulations": "ISO 14021, GRI Standards, TCFD Recommendations, ISSB Standards",
            "description": "International standards and frameworks for sustainability communication",
            "enforcement_focus": "Voluntary compliance, standardized reporting, best practice adoption"
        }
    }
    return frameworks.get(region, frameworks["Global"])

# ============================================================================
# CLEAN TRAINING EXECUTION (NO LOG PARSING)
# ============================================================================

def run_clean_training_session(session_id: str, training_request: TrainingRequest):
    """Run training session with direct artifact generation"""
    try:
        print(f"🚀 Starting clean training session: {session_id}")
        
        # Get session info
        session = sessions[session_id]
        artifact_dir = Path(session["artifact_directory"])
        
        update_session_progress(session_id, 5, "Preparing training inputs...")
        
        # Get regulatory details
        regulatory_details = get_regulatory_details(training_request.regulatory_framework)
        
        # Prepare inputs for CrewAI
        inputs = {
            'user_industry': training_request.industry_focus,
            'regulatory_region': training_request.regulatory_framework,
            'regional_regulations': regulatory_details['regulations'],
            'regulatory_description': regulatory_details['description'],
            'enforcement_focus': regulatory_details['enforcement_focus'],
            'current_year': str(datetime.now().year),
            'session_id': session_id,
            'training_level': training_request.training_level,
            'artifact_directory': str(artifact_dir)
        }
        
        update_session_progress(session_id, 10, "Creating AI crew...")
        
        # Create sustainability crew
        sustainability_crew = Sustainability(session_id=session_id, artifact_directory=str(artifact_dir))
        crew = sustainability_crew.crew()
        
        update_session_progress(session_id, 20, "AI agents starting work...")
        
        # Run the training - agents will write artifacts directly
        result = crew.kickoff(inputs=inputs)
        
        update_session_progress(session_id, 80, "Validating generated artifacts...")
        
        # Validate all required artifacts exist
        required_artifacts = ['scenario.json', 'problems.json', 'corrections.json', 'implementation.json']
        missing_artifacts = []
        
        for artifact in required_artifacts:
            artifact_path = artifact_dir / artifact
            if not artifact_path.exists():
                missing_artifacts.append(artifact)
        
        if missing_artifacts:
            raise Exception(f"Missing required artifacts: {missing_artifacts}")
        
        update_session_progress(session_id, 90, "Building comprehensive playbook...")
        
        # Build markdown from artifacts (will create new markdown_builder)
        from sustainability.markdown_builder import build_playbook_from_artifacts
        
        playbook_file = artifact_dir / "playbook.md"
        build_playbook_from_artifacts(
            artifact_directory=str(artifact_dir),
            output_file=str(playbook_file),
            training_request=training_request.model_dump(),
            session_id=session_id
        )
        
        # Verify playbook was created
        if not playbook_file.exists():
            raise Exception("Failed to generate playbook.md")
        
        update_session_progress(session_id, 95, "Finalizing training session...")
        
        # Complete session successfully
        complete_session(session_id=session_id, playbook_file=str(playbook_file))
        
        print(f"✅ Clean training session completed successfully!")
        print(f"📄 Playbook: {playbook_file}")
        print(f"📁 Artifacts: {artifact_dir}")
        
    except Exception as e:
        error_msg = f"Training failed: {str(e)}"
        print(f"❌ Clean session error {session_id}: {error_msg}")
        complete_session(session_id=session_id, error=error_msg)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0 Clean Architecture",
        "features": ["direct_artifact_generation", "fail_fast_validation", "rich_content"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/training/start", response_model=TrainingResponse)
async def start_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    """Start a new clean training session"""
    
    # Clean up old sessions
    cleanup_old_sessions()
    
    # Validate request
    if not request.industry_focus or not request.regulatory_framework:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # Create session
    session_id = create_session(request)
    
    # Start training in background
    background_tasks.add_task(run_clean_training_session, session_id, request)
    
    return TrainingResponse(
        session_id=session_id,
        status="started",
        message="Clean training session started with direct artifact generation"
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
    
    if not session["playbook_file"] or not os.path.exists(session["playbook_file"]):
        raise HTTPException(status_code=404, detail="Playbook file not found")
    
    file_path = session["playbook_file"]
    filename = os.path.basename(file_path)
    
    # Schedule cleanup after download
    def cleanup_session():
        try:
            artifact_dir = Path(session["artifact_directory"])
            if artifact_dir.exists():
                for file in artifact_dir.glob("*"):
                    file.unlink()
                artifact_dir.rmdir()
            
            if session_id in sessions:
                del sessions[session_id]
            
            print(f"Cleaned up session {session_id} after download")
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    # Schedule cleanup
    import threading
    threading.Timer(1.0, cleanup_session).start()
    
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
            "artifact_directory": session.get("artifact_directory")
        } for sid, session in sessions.items()}
    }

@app.get("/api/training/artifacts/{session_id}")
async def get_session_artifacts(session_id: str):
    """Debug endpoint to inspect session artifacts"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    artifact_dir = Path(session["artifact_directory"])
    
    artifacts_info = {
        "session_id": session_id,
        "artifact_directory": str(artifact_dir),
        "artifacts": {}
    }
    
    if artifact_dir.exists():
        for artifact_file in artifact_dir.glob("*.json"):
            try:
                artifacts_info["artifacts"][artifact_file.name] = {
                    "exists": True,
                    "size": artifact_file.stat().st_size,
                    "modified": artifact_file.stat().st_mtime
                }
            except Exception as e:
                artifacts_info["artifacts"][artifact_file.name] = {
                    "exists": False,
                    "error": str(e)
                }
        
        # Check for playbook
        playbook_file = artifact_dir / "playbook.md"
        if playbook_file.exists():
            artifacts_info["playbook"] = {
                "exists": True,
                "size": playbook_file.stat().st_size
            }
    
    return artifacts_info

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    print("🌱 Starting Clean Sustainability Training API v2.0...")
    print("🔧 Features: Direct artifact generation, Fail-fast validation, Rich content")
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