"""
Validators - Simple safety net validation for sustainability training artifacts
Focuses on structural validation, trusts agents for content quality
"""

from typing import Dict, Any, List, Optional, Tuple


class ValidationError(Exception):
    """Custom exception for validation failures"""
    pass


def validate_scenario_artifact(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate scenario artifact has basic required structure
    
    Args:
        data: Scenario data to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required string fields - just check they exist and aren't empty
    required_string_fields = [
        'company_name', 'industry', 'company_size', 'location',
        'product_service', 'target_audience', 'sustainability_context',
        'regulatory_context'
    ]
    
    for field in required_string_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], str) or not data[field].strip():
            errors.append(f"Field '{field}' must be a non-empty string")
    
    # Required list fields - just check they exist and have some content
    required_list_fields = [
        'marketing_objectives', 'preliminary_claims', 'current_practices', 
        'challenges_faced', 'market_research_sources'
    ]
    
    for field in required_list_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], list):
            errors.append(f"Field '{field}' must be a list")
        elif len(data[field]) == 0:
            errors.append(f"Field '{field}' cannot be empty")
        else:
            # Just check list items are strings, don't police content
            for i, item in enumerate(data[field]):
                if not isinstance(item, str) or not item.strip():
                    errors.append(f"Field '{field}' item {i+1} must be a non-empty string")
    
    return len(errors) == 0, errors


def validate_problems_artifact(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate problems artifact has basic required structure
    
    Args:
        data: Problems data to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check basic top-level structure
    if 'problematic_messages' not in data:
        errors.append("Missing required field: problematic_messages")
        return False, errors
    
    messages = data['problematic_messages']
    if not isinstance(messages, list):
        errors.append("Field 'problematic_messages' must be a list")
        return False, errors
    
    if len(messages) != 4:
        errors.append(f"Must have exactly 4 problematic messages, got {len(messages)}")
        return False, errors
    
    # Validate each message - basic structure only
    found_ids = []
    
    for i, msg in enumerate(messages):
        # Required fields for each message - just check they exist
        required_msg_fields = ['id', 'message', 'why_problematic']
        
        for field in required_msg_fields:
            if field not in msg:
                errors.append(f"Message {i+1}: Missing required field '{field}'")
            elif not isinstance(msg[field], str) or not msg[field].strip():
                errors.append(f"Message {i+1}: Field '{field}' must be a non-empty string")
        
        # Check message ID uniqueness (don't police the format)
        if 'id' in msg:
            if msg['id'] in found_ids:
                errors.append(f"Message {i+1}: Duplicate message ID '{msg['id']}'")
            found_ids.append(msg['id'])
        
        # Check list fields exist but don't police content
        list_fields = ['problems_identified', 'regulatory_violations', 'potential_consequences']
        for field in list_fields:
            if field in msg and not isinstance(msg[field], list):
                errors.append(f"Message {i+1}: Field '{field}' must be a list")
    
    return len(errors) == 0, errors


def validate_corrections_artifact(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate corrections artifact has basic required structure
    
    Args:
        data: Corrections data to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check basic structure
    if 'corrected_messages' not in data:
        errors.append("Missing required field: corrected_messages")
        return False, errors
    
    corrections = data['corrected_messages']
    if not isinstance(corrections, list):
        errors.append("Field 'corrected_messages' must be a list")
        return False, errors
    
    if len(corrections) != 4:
        errors.append(f"Must have exactly 4 corrected messages, got {len(corrections)}")
        return False, errors
    
    # Validate each correction - basic structure only
    found_original_ids = []
    
    for i, correction in enumerate(corrections):
        # Basic required fields
        required_fields = ['original_message_id', 'corrected_message', 'changes_made', 'compliance_notes']
        
        for field in required_fields:
            if field not in correction:
                errors.append(f"Correction {i+1}: Missing required field '{field}'")
            elif field in ['original_message_id', 'corrected_message', 'compliance_notes']:
                # These should be strings
                if not isinstance(correction[field], str) or not correction[field].strip():
                    errors.append(f"Correction {i+1}: Field '{field}' must be a non-empty string")
            elif field == 'changes_made':
                # This should be a list
                if not isinstance(correction[field], list) or len(correction[field]) == 0:
                    errors.append(f"Correction {i+1}: Field '{field}' must be a non-empty list")
        
        # Track original message IDs
        if 'original_message_id' in correction:
            found_original_ids.append(correction['original_message_id'])
    
    # Check we have corrections for different messages
    if len(set(found_original_ids)) != len(found_original_ids):
        errors.append("Duplicate original_message_id found - each correction should be for a different message")
    
    return len(errors) == 0, errors


def validate_implementation_artifact(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate implementation artifact has basic required structure
    
    Args:
        data: Implementation data to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required list fields - just check they exist and have content
    required_lists = [
        'implementation_roadmap', 'success_metrics', 'timeline_milestones',
        'team_training_requirements', 'tools_and_resources'
    ]
    
    for field in required_lists:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], list):
            errors.append(f"Field '{field}' must be a list")
        elif len(data[field]) == 0:
            errors.append(f"Field '{field}' cannot be empty")
        else:
            # Check list items are strings, don't police content
            for i, item in enumerate(data[field]):
                if not isinstance(item, str) or not item.strip():
                    errors.append(f"Field '{field}' item {i+1} must be a non-empty string")
    
    # Required string fields - just check they exist
    required_string_fields = ['industry_specific_considerations', 'regulatory_compliance_schedule']
    
    for field in required_string_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], str) or not data[field].strip():
            errors.append(f"Field '{field}' must be a non-empty string")
    
    return len(errors) == 0, errors


def validate_all_artifacts(artifact_directory: str) -> Dict[str, Any]:
    """
    Validate all artifacts in a directory - safety net only
    
    Args:
        artifact_directory: Directory containing artifacts
        
    Returns:
        Dict with validation results for all artifacts
    """
    from sustainability.artifact_writer import read_artifact, artifact_exists
    
    results = {
        "all_valid": False,
        "artifacts": {},
        "missing_artifacts": [],
        "total_errors": 0
    }
    
    # Define required artifacts and their validators
    artifact_validators = {
        'scenario.json': validate_scenario_artifact,
        'problems.json': validate_problems_artifact,
        'corrections.json': validate_corrections_artifact,
        'implementation.json': validate_implementation_artifact
    }
    
    # Check each artifact
    for filename, validator in artifact_validators.items():
        if not artifact_exists(artifact_directory, filename):
            results["missing_artifacts"].append(filename)
            results["artifacts"][filename] = {
                "exists": False,
                "valid": False,
                "errors": [f"Artifact file {filename} not found"]
            }
        else:
            # Read and validate artifact
            artifact_data = read_artifact(artifact_directory, filename)
            if artifact_data is None:
                results["artifacts"][filename] = {
                    "exists": True,
                    "valid": False,
                    "errors": [f"Could not read or parse {filename}"]
                }
            else:
                is_valid, errors = validator(artifact_data)
                results["artifacts"][filename] = {
                    "exists": True,
                    "valid": is_valid,
                    "errors": errors
                }
        
        # Count total errors
        results["total_errors"] += len(results["artifacts"][filename]["errors"])
    
    # Overall validation status
    results["all_valid"] = (
        len(results["missing_artifacts"]) == 0 and 
        all(artifact["valid"] for artifact in results["artifacts"].values())
    )
    
    return results


def get_validation_summary(validation_results: Dict[str, Any]) -> str:
    """
    Generate human-readable validation summary
    
    Args:
        validation_results: Results from validate_all_artifacts
        
    Returns:
        String summary of validation status
    """
    if validation_results["all_valid"]:
        return "✅ All artifacts are structurally valid"
    
    summary_lines = ["❌ Artifact validation failed:"]
    
    if validation_results["missing_artifacts"]:
        summary_lines.append(f"   Missing artifacts: {', '.join(validation_results['missing_artifacts'])}")
    
    for filename, result in validation_results["artifacts"].items():
        if not result["valid"]:
            summary_lines.append(f"   {filename}: {len(result['errors'])} errors")
            for error in result["errors"][:3]:  # Show first 3 errors
                summary_lines.append(f"     - {error}")
            if len(result["errors"]) > 3:
                summary_lines.append(f"     - ... and {len(result['errors']) - 3} more errors")
    
    summary_lines.append(f"   Total errors: {validation_results['total_errors']}")
    
    return "\n".join(summary_lines)