"""
Artifact Writer - Simple utility for atomic JSON file writing
Provides safe, reliable file operations for sustainability training artifacts
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class ArtifactWriteError(Exception):
    """Custom exception for artifact writing failures"""
    pass


def write_artifact(artifact_directory: str, filename: str, data: Dict[str, Any]) -> bool:
    """
    Write data to artifact file with atomic operation
    
    Args:
        artifact_directory: Directory to write the artifact
        filename: Name of the file (e.g., 'scenario.json')
        data: Dictionary data to write as JSON
        
    Returns:
        bool: True if successful, False if failed
        
    Raises:
        ArtifactWriteError: If writing fails
    """
    try:
        # Ensure directory exists
        artifact_dir = Path(artifact_directory)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        # Define file paths
        final_path = artifact_dir / filename
        temp_path = artifact_dir / f"{filename}.tmp"
        
        # Add metadata to data
        enriched_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "filename": filename,
                "schema_version": "1.0"
            },
            "data": data
        }
        
        # Write to temporary file first (atomic write pattern)
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, indent=2, ensure_ascii=False)
        
        # Verify the temp file was written correctly
        if not temp_path.exists() or temp_path.stat().st_size == 0:
            raise ArtifactWriteError(f"Temporary file {temp_path} was not created properly")
        
        # Atomic rename operation
        temp_path.rename(final_path)
        
        # Verify final file exists
        if not final_path.exists():
            raise ArtifactWriteError(f"Final file {final_path} was not created")
        
        print(f"✅ Artifact written successfully: {final_path}")
        print(f"   Size: {final_path.stat().st_size} bytes")
        
        return True
        
    except json.JSONEncodeError as e:
        error_msg = f"JSON encoding failed for {filename}: {str(e)}"
        print(f"❌ {error_msg}")
        raise ArtifactWriteError(error_msg)
        
    except PermissionError as e:
        error_msg = f"Permission denied writing {filename}: {str(e)}"
        print(f"❌ {error_msg}")
        raise ArtifactWriteError(error_msg)
        
    except OSError as e:
        error_msg = f"OS error writing {filename}: {str(e)}"
        print(f"❌ {error_msg}")
        raise ArtifactWriteError(error_msg)
        
    except Exception as e:
        error_msg = f"Unexpected error writing {filename}: {str(e)}"
        print(f"❌ {error_msg}")
        raise ArtifactWriteError(error_msg)


def read_artifact(artifact_directory: str, filename: str) -> Optional[Dict[str, Any]]:
    """
    Read and parse artifact file
    
    Args:
        artifact_directory: Directory containing the artifact
        filename: Name of the file to read
        
    Returns:
        Dict containing the artifact data, or None if failed
    """
    try:
        artifact_path = Path(artifact_directory) / filename
        
        if not artifact_path.exists():
            print(f"⚠️ Artifact file not found: {artifact_path}")
            return None
        
        with open(artifact_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Extract data from metadata wrapper
        if "data" in raw_data:
            return raw_data["data"]
        else:
            # Handle legacy files without metadata wrapper
            return raw_data
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error reading {filename}: {str(e)}")
        return None
        
    except Exception as e:
        print(f"❌ Error reading {filename}: {str(e)}")
        return None


def validate_json_structure(data: Dict[str, Any]) -> bool:
    """
    Basic validation that data can be serialized to JSON
    
    Args:
        data: Dictionary to validate
        
    Returns:
        bool: True if valid, False if not
    """
    try:
        # Test JSON serialization
        json.dumps(data)
        return True
    except (TypeError, ValueError) as e:
        print(f"❌ JSON validation failed: {str(e)}")
        return False


def artifact_exists(artifact_directory: str, filename: str) -> bool:
    """
    Check if artifact file exists
    
    Args:
        artifact_directory: Directory to check
        filename: Filename to check
        
    Returns:
        bool: True if exists, False if not
    """
    artifact_path = Path(artifact_directory) / filename
    return artifact_path.exists() and artifact_path.is_file()


def get_artifact_info(artifact_directory: str, filename: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata about an artifact file
    
    Args:
        artifact_directory: Directory containing the artifact
        filename: Name of the file
        
    Returns:
        Dict with file information or None if file doesn't exist
    """
    try:
        artifact_path = Path(artifact_directory) / filename
        
        if not artifact_path.exists():
            return None
        
        stat = artifact_path.stat()
        
        return {
            "filename": filename,
            "path": str(artifact_path),
            "size_bytes": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "exists": True
        }
        
    except Exception as e:
        print(f"❌ Error getting artifact info for {filename}: {str(e)}")
        return None


def cleanup_temp_files(artifact_directory: str) -> int:
    """
    Clean up any leftover temporary files
    
    Args:
        artifact_directory: Directory to clean
        
    Returns:
        int: Number of temp files removed
    """
    try:
        artifact_dir = Path(artifact_directory)
        if not artifact_dir.exists():
            return 0
        
        temp_files = list(artifact_dir.glob("*.tmp"))
        removed_count = 0
        
        for temp_file in temp_files:
            try:
                temp_file.unlink()
                removed_count += 1
                print(f"🧹 Cleaned up temp file: {temp_file.name}")
            except Exception as e:
                print(f"⚠️ Could not remove temp file {temp_file.name}: {str(e)}")
        
        return removed_count
        
    except Exception as e:
        print(f"❌ Error during temp file cleanup: {str(e)}")
        return 0


def list_artifacts(artifact_directory: str) -> Dict[str, Any]:
    """
    List all artifacts in a directory
    
    Args:
        artifact_directory: Directory to scan
        
    Returns:
        Dict with artifact inventory
    """
    try:
        artifact_dir = Path(artifact_directory)
        
        if not artifact_dir.exists():
            return {"exists": False, "artifacts": []}
        
        artifacts = []
        json_files = list(artifact_dir.glob("*.json"))
        
        for json_file in json_files:
            info = get_artifact_info(artifact_directory, json_file.name)
            if info:
                artifacts.append(info)
        
        return {
            "exists": True,
            "directory": str(artifact_dir),
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
            "has_playbook": (artifact_dir / "playbook.md").exists()
        }
        
    except Exception as e:
        print(f"❌ Error listing artifacts: {str(e)}")
        return {"exists": False, "error": str(e), "artifacts": []}