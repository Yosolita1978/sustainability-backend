#!/usr/bin/env python
"""
Enhanced FastAPI Backend for Sustainability Training
Comprehensive data extraction and markdown generation
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
from sustainability.callbacks import create_session_callback_handler

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# FastAPI app setup
app = FastAPI(
    title="Enhanced Sustainability Training API",
    description="AI-powered sustainability messaging training with comprehensive data extraction",
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
        "current_step": "Initializing enhanced training system...",
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
        
        print(f"Enhanced Session {session_id}: {progress}% - {step}")

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
            sessions[session_id]["current_step"] = "Enhanced training completed successfully!"

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
        print(f"Cleaned up expired enhanced session: {sid}")

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
# ENHANCED TRAINING EXECUTION
# ============================================================================

def run_enhanced_training_session(session_id: str, training_request: TrainingRequest):
    """Run enhanced training session with comprehensive data extraction and validation"""
    try:
        print(f"🚀 Starting enhanced training session: {session_id}")
        
        # Initialize enhanced tracking
        update_session_progress(session_id, 5, "Initializing enhanced AI training system...", "System")
        
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
        
        update_session_progress(session_id, 10, "Creating enhanced AI crew with validation...", "System")
        
        # Create enhanced crew with session-specific callback handler
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
        
        update_session_progress(session_id, 15, "Enhanced AI agents collaborating with real-time validation...", "System")
        
        # Run the training with enhanced monitoring
        result = crew.kickoff(inputs=inputs)
        
        update_session_progress(session_id, 60, "Training complete - starting comprehensive data extraction...", "System")
        
        # ========================================================================
        # ENHANCED DATA EXTRACTION AND PROCESSING
        # ========================================================================
        
        print(f"🔍 Starting comprehensive data extraction for session {session_id}")
        
        # Step 1: Extract data using enhanced extractor
        data_extractor = SessionDataExtractor(session_id)
        comprehensive_data = data_extractor.extract_complete_session_data(crew_log_file)
        
        # Store extraction results in session
        sessions[session_id]["extracted_data"] = comprehensive_data.get("raw_data", {})
        sessions[session_id]["validation_result"] = comprehensive_data.get("validation", {})
        sessions[session_id]["integration_result"] = comprehensive_data.get("integration", {})
        
        update_session_progress(session_id, 75, "Data extraction complete - validating quality...", "System")
        
        # Get quality metrics
        validation_result = comprehensive_data.get("validation", {})
        quality_score = validation_result.get("quality_score", 0)
        data_completeness = validation_result.get("completeness_percentage", 0)
        
        print(f"📊 Quality Score: {quality_score:.1f}/100")
        print(f"📈 Data Completeness: {data_completeness:.1f}%")
        
        # Check if we have sufficient data quality
        if quality_score < 50 or data_completeness < 60:
            print(f"⚠️ Low quality data detected, attempting backup extraction...")
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
        # ENHANCED MARKDOWN GENERATION
        # ========================================================================
        
        # Generate comprehensive markdown using extracted data
        comprehensive_markdown = generate_comprehensive_playbook(
            extracted_data=comprehensive_data.get("raw_data", {}),
            validation_result=comprehensive_data.get("validation", {}),
            integration_result=comprehensive_data.get("integration", {}),
            training_request=training_request.model_dump(),
            session_id=session_id
        )
        
        # Create outputs directory
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(exist_ok=True)
        
        # Generate enhanced filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_sustainability_playbook_{session_id[:8]}_{timestamp}.md"
        file_path = outputs_dir / filename
        
        # Save comprehensive markdown
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(comprehensive_markdown)
        
        # Verify file creation and size
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"✅ Enhanced playbook created: {file_size:,} bytes")
            
            # Log content statistics
            char_count = len(comprehensive_markdown)
            line_count = comprehensive_markdown.count('\n')
            section_count = comprehensive_markdown.count('##')
            
            print(f"📊 Content stats: {char_count:,} chars, {line_count:,} lines, {section_count} sections")
        else:
            raise Exception("Failed to create enhanced playbook file")
        
        update_session_progress(session_id, 95, "Finalizing enhanced training session...", "System")
        
        # Complete session with quality metrics
        complete_session(
            session_id=session_id,
            results=result,
            file_path=str(file_path),
            quality_score=quality_score,
            data_completeness=data_completeness
        )
        
        print(f"🎉 Enhanced training session completed successfully!")
        print(f"📄 Playbook: {file_path}")
        print(f"📊 Quality: {quality_score:.1f}/100")
        print(f"📈 Completeness: {data_completeness:.1f}%")
        
    except Exception as e:
        error_msg = f"Enhanced training failed: {str(e)}"
        print(f"❌ Enhanced session error {session_id}: {error_msg}")
        
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

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0 Enhanced",
        "features": ["comprehensive_extraction", "quality_validation", "integrated_markdown"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/training/start", response_model=TrainingResponse)
async def start_enhanced_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    """Start a new enhanced training session"""
    
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
        message="Enhanced training session started with comprehensive data extraction and validation"
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
            
            print(f"Cleaned up enhanced session {session_id} after download")
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

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    print("🌱 Starting Enhanced Sustainability Training API v2.0...")
    print("🔧 Features: Comprehensive extraction, Quality validation, Integrated markdown")
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