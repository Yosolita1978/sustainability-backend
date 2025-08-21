import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import traceback

class LogParser:
    """Advanced log parser for extracting task data from CrewAI session logs with multi-line JSON support"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.extraction_log = []
        self.parsed_tasks = {}
        
    def parse_session_log(self, log_file_path: str) -> Dict[str, Any]:
        """Parse session log file and extract all task data"""
        extraction_result = {
            "scenario_data": None,
            "problematic_messages": None,
            "corrected_messages": None,
            "playbook_data": None,
            "extraction_log": [],
            "parsing_success": False,
            "total_tasks_found": 0
        }
        
        if not os.path.exists(log_file_path):
            extraction_result["extraction_log"].append(f"❌ Log file not found: {log_file_path}")
            return extraction_result
        
        try:
            # Read log file with proper encoding
            with open(log_file_path, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()
            
            extraction_result["extraction_log"].append(f"✅ Log file read successfully: {len(log_lines)} lines")
            
            # Extract task completions using multi-line JSON parser
            task_data = self._extract_multiline_task_completions(log_lines)
            
            # Process each task type
            for task_name, task_json in task_data.items():
                processed_data = self._process_task_data(task_name, task_json)
                if processed_data:
                    self._categorize_task_data(task_name, processed_data, extraction_result)
                    extraction_result["total_tasks_found"] += 1
            
            # Validate extraction completeness
            extraction_result["parsing_success"] = extraction_result["total_tasks_found"] >= 3
            extraction_result["extraction_log"] = self.extraction_log
            
        except Exception as e:
            extraction_result["extraction_log"].append(f"❌ Log parsing error: {str(e)}")
            extraction_result["extraction_log"].append(f"❌ Traceback: {traceback.format_exc()}")
        
        return extraction_result
    
    def _extract_multiline_task_completions(self, log_lines: List[str]) -> Dict[str, str]:
        """Extract task completion data from log lines - MULTI-LINE JSON PARSER"""
        task_data = {}
        
        i = 0
        while i < len(log_lines):
            line = log_lines[i].strip()
            
            # Look for completed task lines
            if 'status="completed"' in line and 'output="' in line:
                # Extract task name
                task_name_match = re.search(r'task_name="([^"]+)"', line)
                if not task_name_match:
                    i += 1
                    continue
                
                task_name = task_name_match.group(1)
                self.extraction_log.append(f"📋 Found completed task: {task_name}")
                
                # Find the start of JSON output
                output_start = line.find('output="')
                if output_start == -1:
                    self.extraction_log.append(f"❌ No output found for {task_name}")
                    i += 1
                    continue
                
                # Extract JSON starting from output="
                json_start_pos = output_start + 8  # Skip 'output="'
                json_content = line[json_start_pos:]
                
                # Check if JSON starts on this line
                if '{' not in json_content:
                    self.extraction_log.append(f"❌ No JSON start found for {task_name}")
                    i += 1
                    continue
                
                # Find the opening brace
                brace_start = json_content.find('{')
                if brace_start == -1:
                    i += 1
                    continue
                
                # Start collecting JSON from the opening brace
                json_lines = [json_content[brace_start:]]
                brace_count = 1  # We found the first opening brace
                current_line = i + 1
                
                # Continue reading lines until we have a complete JSON object
                while current_line < len(log_lines) and brace_count > 0:
                    next_line = log_lines[current_line].strip()
                    
                    # Count braces in this line
                    for char in next_line:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                    
                    json_lines.append(next_line)
                    current_line += 1
                    
                    # Safety check to prevent infinite loops
                    if current_line - i > 100:  # Max 100 lines for JSON
                        self.extraction_log.append(f"⚠️ JSON too long for {task_name}, stopping")
                        break
                
                # Combine all JSON lines
                full_json = '\n'.join(json_lines)
                
                # Clean the JSON string
                cleaned_json = self._clean_multiline_json(full_json)
                
                if cleaned_json:
                    # Validate JSON
                    try:
                        json.loads(cleaned_json)  # Test parse
                        task_data[task_name] = cleaned_json
                        self.extraction_log.append(f"✅ Successfully extracted {task_name}: {len(cleaned_json):,} characters")
                    except json.JSONDecodeError as e:
                        self.extraction_log.append(f"❌ Invalid JSON for {task_name}: {str(e)}")
                        self.extraction_log.append(f"📝 First 200 chars: {cleaned_json[:200]}...")
                
                # Move to next line after the JSON block
                i = current_line
            else:
                i += 1
        
        self.extraction_log.append(f"📊 Total tasks successfully extracted: {len(task_data)}")
        
        # Debug: Show what we extracted
        for task_name in task_data.keys():
            self.extraction_log.append(f"✅ Confirmed extraction: {task_name}")
        
        return task_data
    
    def _clean_multiline_json(self, json_str: str) -> str:
        """Clean multi-line JSON string from log artifacts"""
        if not json_str:
            return ""
        
        lines = json_str.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove timestamp prefixes
            line = re.sub(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}:', '', line)
            
            # Remove any remaining log artifacts
            line = re.sub(r'task_name="[^"]*"[^"]*status="[^"]*"[^"]*output="', '', line)
            
            # Handle ending quotes from log format
            if line.endswith('"') and line.count('"') % 2 == 1:  # Odd number of quotes
                line = line[:-1]  # Remove trailing quote
            
            # Clean up extra whitespace but preserve JSON structure
            line = line.strip()
            
            if line:
                cleaned_lines.append(line)
        
        # Join lines back together
        cleaned = '\n'.join(cleaned_lines)
        
        # Fix common escaping issues
        cleaned = cleaned.replace('\\"', '"')
        cleaned = cleaned.replace('\\n', '\n')
        cleaned = cleaned.replace('\\\\', '\\')
        
        # Ensure JSON starts with { and ends with }
        if not cleaned.startswith('{'):
            start_brace = cleaned.find('{')
            if start_brace != -1:
                cleaned = cleaned[start_brace:]
        
        if not cleaned.endswith('}'):
            end_brace = cleaned.rfind('}')
            if end_brace != -1:
                cleaned = cleaned[:end_brace + 1]
        
        return cleaned
    
    def _process_task_data(self, task_name: str, json_str: str) -> Optional[Dict[str, Any]]:
        """Process and validate task JSON data"""
        try:
            # Parse JSON
            data = json.loads(json_str)
            
            # Validate structure
            if not isinstance(data, dict):
                self.extraction_log.append(f"⚠️ {task_name}: Data is not a dictionary")
                return None
            
            # Check for essential fields based on task type
            if self._validate_task_structure(task_name, data):
                self.extraction_log.append(f"✅ {task_name}: Valid structure with {len(str(data)):,} chars")
                return data
            else:
                self.extraction_log.append(f"⚠️ {task_name}: Invalid structure but proceeding with available data")
                return data  # Return even if structure is imperfect
                
        except json.JSONDecodeError as e:
            self.extraction_log.append(f"❌ {task_name}: JSON parse error - {str(e)}")
            # Try to fix common JSON issues
            fixed_data = self._attempt_json_repair(json_str)
            if fixed_data:
                self.extraction_log.append(f"✅ {task_name}: Repaired and parsed successfully")
                return fixed_data
            return None
        except Exception as e:
            self.extraction_log.append(f"❌ {task_name}: Processing error - {str(e)}")
            return None
    
    def _validate_task_structure(self, task_name: str, data: Dict[str, Any]) -> bool:
        """Validate task data structure"""
        if "scenario" in task_name:
            required = ["company_name", "industry", "product_service"]
            return all(field in data and data[field] for field in required)
        elif "mistake" in task_name:
            return "problematic_messages" in data and isinstance(data["problematic_messages"], list)
        elif "best_practice" in task_name:
            return "corrected_messages" in data and isinstance(data["corrected_messages"], list)
        elif "playbook" in task_name:
            required = ["playbook_title", "dos_and_donts"]
            return all(field in data for field in required)
        return True
    
    def _attempt_json_repair(self, json_str: str) -> Optional[Dict[str, Any]]:
        """Attempt to repair malformed JSON"""
        try:
            # Common fixes
            fixes = [
                # Fix trailing commas
                lambda s: re.sub(r',(\s*[}\]])', r'\1', s),
                # Fix unescaped quotes in strings
                lambda s: re.sub(r'(?<!\\)"(?=[^,}\]]*[,}\]])', r'\\"', s),
                # Fix missing quotes on keys
                lambda s: re.sub(r'(\w+):', r'"\1":', s),
            ]
            
            for fix in fixes:
                try:
                    fixed = fix(json_str)
                    data = json.loads(fixed)
                    return data
                except:
                    continue
            
            return None
        except:
            return None
    
    def _categorize_task_data(self, task_name: str, data: Dict[str, Any], result: Dict[str, Any]):
        """Categorize task data into result structure"""
        if "scenario" in task_name:
            result["scenario_data"] = data
        elif "mistake" in task_name:
            result["problematic_messages"] = data
        elif "best_practice" in task_name:
            result["corrected_messages"] = data
        elif "playbook" in task_name:
            result["playbook_data"] = data

class DataValidator:
    """Validates extracted data for completeness and quality"""
    
    def __init__(self):
        self.validation_log = []
    
    def validate_complete_dataset(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete dataset from all tasks"""
        validation_result = {
            "is_complete": False,
            "quality_score": 0,
            "completeness_percentage": 0,
            "task_validations": {},
            "overall_issues": [],
            "data_richness": {}
        }
        
        # Validate each task's data
        task_scores = []
        
        if extracted_data.get("scenario_data"):
            scenario_validation = self._validate_scenario_completeness(extracted_data["scenario_data"])
            validation_result["task_validations"]["scenario"] = scenario_validation
            task_scores.append(scenario_validation["score"])
        else:
            validation_result["overall_issues"].append("Missing scenario data")
        
        if extracted_data.get("problematic_messages"):
            mistakes_validation = self._validate_mistakes_completeness(extracted_data["problematic_messages"])
            validation_result["task_validations"]["mistakes"] = mistakes_validation
            task_scores.append(mistakes_validation["score"])
        else:
            validation_result["overall_issues"].append("Missing problematic messages data")
        
        if extracted_data.get("corrected_messages"):
            corrections_validation = self._validate_corrections_completeness(extracted_data["corrected_messages"])
            validation_result["task_validations"]["corrections"] = corrections_validation
            task_scores.append(corrections_validation["score"])
        else:
            validation_result["overall_issues"].append("Missing corrections data")
        
        if extracted_data.get("playbook_data"):
            playbook_validation = self._validate_playbook_completeness(extracted_data["playbook_data"])
            validation_result["task_validations"]["playbook"] = playbook_validation
            task_scores.append(playbook_validation["score"])
        else:
            validation_result["overall_issues"].append("Missing playbook data")
        
        # Calculate overall metrics
        if task_scores:
            validation_result["quality_score"] = sum(task_scores) / len(task_scores)
            validation_result["completeness_percentage"] = min(100, (len(task_scores) / 4) * 100)
            validation_result["is_complete"] = len(task_scores) >= 3 and validation_result["quality_score"] >= 60
        
        # Calculate data richness
        validation_result["data_richness"] = self._calculate_data_richness(extracted_data)
        
        return validation_result
    
    def _validate_scenario_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate scenario data completeness"""
        required_fields = ["company_name", "industry", "product_service", "target_audience"]
        quality_fields = ["marketing_objectives", "sustainability_context", "preliminary_claims"]
        
        score = 0
        issues = []
        strengths = []
        
        for field in required_fields:
            if field in data and data[field]:
                score += 20
                if len(str(data[field])) > 50:
                    strengths.append(f"Detailed {field}")
            else:
                issues.append(f"Missing {field}")
        
        for field in quality_fields:
            if field in data and data[field]:
                score += 5
                if isinstance(data[field], list) and len(data[field]) > 2:
                    strengths.append(f"Rich {field}")
        
        return {"score": min(100, score), "issues": issues, "strengths": strengths}
    
    def _validate_mistakes_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate problematic messages completeness"""
        score = 0
        issues = []
        strengths = []
        
        if "problematic_messages" in data:
            messages = data["problematic_messages"]
            if len(messages) >= 3:  # Adjusted to match actual data
                score += 40
                strengths.append(f"{len(messages)} problematic messages")
            else:
                issues.append(f"Only {len(messages)} messages (need 3+)")
            
            # Check message detail
            detailed_messages = 0
            for msg in messages:
                if all(field in msg for field in ["message", "why_problematic", "problems_identified"]):
                    detailed_messages += 1
            
            score += (detailed_messages * 15)  # Increased weight for detailed messages
            if detailed_messages == len(messages):
                strengths.append("All messages have detailed analysis")
        else:
            issues.append("No problematic messages found")
        
        return {"score": min(100, score), "issues": issues, "strengths": strengths}
    
    def _validate_corrections_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate corrections completeness"""
        score = 0
        issues = []
        strengths = []
        
        if "corrected_messages" in data:
            corrections = data["corrected_messages"]
            if len(corrections) >= 3:  # Adjusted to match actual data
                score += 40
                strengths.append(f"{len(corrections)} corrections provided")
            else:
                issues.append(f"Only {len(corrections)} corrections")
            
            # Check correction detail
            detailed_corrections = 0
            for correction in corrections:
                if all(field in correction for field in ["corrected_message", "changes_made", "compliance_notes"]):
                    detailed_corrections += 1
            
            score += (detailed_corrections * 15)  # Increased weight
            if detailed_corrections == len(corrections):
                strengths.append("All corrections have detailed explanations")
        else:
            issues.append("No corrections found")
        
        return {"score": min(100, score), "issues": issues, "strengths": strengths}
    
    def _validate_playbook_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate playbook completeness"""
        score = 0
        issues = []
        strengths = []
        
        essential_sections = ["dos_and_donts", "greenwashing_patterns", "claim_to_proof_framework", "compliance_checklist"]
        for section in essential_sections:
            if section in data and data[section]:
                score += 20
                strengths.append(f"Complete {section}")
            else:
                issues.append(f"Missing {section}")
        
        # Check framework detail
        if "claim_to_proof_framework" in data:
            framework = data["claim_to_proof_framework"]
            if isinstance(framework, dict) and "steps" in framework:
                score += 10
                strengths.append("Detailed framework")
        
        return {"score": min(100, score), "issues": issues, "strengths": strengths}
    
    def _calculate_data_richness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall data richness metrics"""
        richness = {
            "total_characters": 0,
            "total_fields": 0,
            "nested_structures": 0,
            "list_items": 0
        }
        
        def count_structure(obj, path=""):
            if isinstance(obj, dict):
                richness["total_fields"] += len(obj)
                if len(obj) > 5:
                    richness["nested_structures"] += 1
                for key, value in obj.items():
                    count_structure(value, f"{path}.{key}")
            elif isinstance(obj, list):
                richness["list_items"] += len(obj)
                for item in obj:
                    count_structure(item, f"{path}[]")
            elif isinstance(obj, str):
                richness["total_characters"] += len(obj)
        
        for task_data in data.values():
            if task_data:
                count_structure(task_data)
        
        return richness

class DataIntegrator:
    """Integrates data across tasks to ensure consistency and cross-references"""
    
    def __init__(self):
        self.integration_log = []
    
    def integrate_task_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate data across all tasks"""
        integrated_data = {
            "scenario_context": {},
            "integrated_messages": [],
            "cross_references": {},
            "integration_quality": {}
        }
        
        # Extract scenario context
        if extracted_data.get("scenario_data"):
            integrated_data["scenario_context"] = self._extract_scenario_context(extracted_data["scenario_data"])
        
        # Integrate problematic and corrected messages
        if extracted_data.get("problematic_messages") and extracted_data.get("corrected_messages"):
            integrated_data["integrated_messages"] = self._integrate_message_pairs(
                extracted_data["problematic_messages"],
                extracted_data["corrected_messages"]
            )
        
        # Create cross-references
        integrated_data["cross_references"] = self._create_cross_references(extracted_data)
        
        # Assess integration quality
        integrated_data["integration_quality"] = self._assess_integration_quality(integrated_data, extracted_data)
        
        return integrated_data
    
    def _extract_scenario_context(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key context from scenario for cross-referencing"""
        return {
            "company_name": scenario_data.get("company_name", ""),
            "industry": scenario_data.get("industry", ""),
            "regulatory_context": scenario_data.get("regulatory_context", ""),
            "sustainability_focus": scenario_data.get("sustainability_context", ""),
            "target_claims": scenario_data.get("preliminary_claims", [])
        }
    
    def _integrate_message_pairs(self, problematic_data: Dict[str, Any], corrected_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Integrate problematic messages with their corrections"""
        integrated_pairs = []
        
        problematic_messages = problematic_data.get("problematic_messages", [])
        corrected_messages = corrected_data.get("corrected_messages", [])
        
        # Create mapping of corrections to problematic messages
        correction_map = {}
        for correction in corrected_messages:
            original_id = correction.get("original_message_id", "")
            if original_id:
                correction_map[original_id] = correction
        
        # Integrate pairs
        for i, problematic in enumerate(problematic_messages):
            message_id = problematic.get("id", str(i+1))
            correction = correction_map.get(message_id)
            
            integrated_pair = {
                "pair_id": message_id,
                "problematic": problematic,
                "correction": correction,
                "has_correction": correction is not None,
                "integration_complete": self._validate_message_pair(problematic, correction)
            }
            
            integrated_pairs.append(integrated_pair)
        
        return integrated_pairs
    
    def _validate_message_pair(self, problematic: Dict[str, Any], correction: Optional[Dict[str, Any]]) -> bool:
        """Validate that a problematic message has a proper correction"""
        if not correction:
            return False
        
        # Check that correction addresses the problems
        problematic_issues = problematic.get("problems_identified", [])
        changes_made = correction.get("changes_made", [])
        
        return len(changes_made) > 0 and len(problematic_issues) > 0
    
    def _create_cross_references(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create cross-references between different data sections"""
        cross_refs = {
            "scenario_to_messages": {},
            "regulatory_consistency": {},
            "industry_alignment": {}
        }
        
        scenario = extracted_data.get("scenario_data", {})
        company_name = scenario.get("company_name", "")
        industry = scenario.get("industry", "")
        
        # Check if problematic messages reference the scenario
        if extracted_data.get("problematic_messages"):
            messages_data = extracted_data["problematic_messages"]
            scenario_ref = messages_data.get("scenario_reference", "")
            cross_refs["scenario_to_messages"] = {
                "referenced": company_name.lower() in scenario_ref.lower() if scenario_ref else False,
                "company_mentioned": company_name,
                "reference_text": scenario_ref
            }
        
        return cross_refs
    
    def _assess_integration_quality(self, integrated_data: Dict[str, Any], original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of data integration"""
        quality_metrics = {
            "cross_reference_score": 0,
            "consistency_score": 0,
            "completeness_score": 0,
            "issues": [],
            "strengths": []
        }
        
        # Check cross-references
        if integrated_data["cross_references"]["scenario_to_messages"].get("referenced"):
            quality_metrics["cross_reference_score"] += 50
            quality_metrics["strengths"].append("Messages properly reference scenario")
        else:
            quality_metrics["issues"].append("Messages don't reference scenario context")
        
        # Check message pair completeness
        message_pairs = integrated_data.get("integrated_messages", [])
        complete_pairs = sum(1 for pair in message_pairs if pair["integration_complete"])
        
        if message_pairs:
            pair_ratio = complete_pairs / len(message_pairs)
            quality_metrics["completeness_score"] = int(pair_ratio * 100)
            
            if pair_ratio > 0.8:
                quality_metrics["strengths"].append("Most messages have proper corrections")
            else:
                quality_metrics["issues"].append("Some messages lack proper corrections")
        
        return quality_metrics

class SessionDataExtractor:
    """Main class for extracting and processing all session data"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.log_parser = LogParser(session_id)
        self.validator = DataValidator()
        self.integrator = DataIntegrator()
        self.extraction_summary = {}
    
    def extract_complete_session_data(self, log_file_path: str) -> Dict[str, Any]:
        """Extract complete session data with validation and integration"""
        print(f"🔍 Starting multi-line JSON extraction for session {self.session_id}")
        
        # Step 1: Parse log file with multi-line support
        print(f"📄 Parsing log file: {log_file_path}")
        extracted_data = self.log_parser.parse_session_log(log_file_path)
        
        # Step 2: Validate extracted data
        print(f"✅ Validating extracted data...")
        validation_result = self.validator.validate_complete_dataset(extracted_data)
        
        # Step 3: Integrate data across tasks
        print(f"🔗 Integrating data across tasks...")
        integration_result = self.integrator.integrate_task_data(extracted_data)
        
        # Step 4: Create comprehensive result
        comprehensive_result = {
            "session_id": self.session_id,
            "extraction_timestamp": datetime.now().isoformat(),
            "raw_data": extracted_data,
            "validation": validation_result,
            "integration": integration_result,
            "extraction_summary": self._create_extraction_summary(extracted_data, validation_result)
        }
        
        print(f"🎉 Multi-line extraction complete: {validation_result['quality_score']:.1f}/100 quality score")
        
        return comprehensive_result
    
    def _create_extraction_summary(self, data: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of extraction results"""
        return {
            "tasks_extracted": data["total_tasks_found"],
            "overall_quality": validation["quality_score"],
            "data_completeness": validation["completeness_percentage"],
            "total_characters": sum(len(str(task_data)) for task_data in [
                data.get("scenario_data"),
                data.get("problematic_messages"),
                data.get("corrected_messages"),
                data.get("playbook_data")
            ] if task_data),
            "extraction_success": validation["is_complete"]
        }

def extract_session_data(session_id: str, log_file_path: str) -> Dict[str, Any]:
    """Main function to extract all session data"""
    extractor = SessionDataExtractor(session_id)
    return extractor.extract_complete_session_data(log_file_path)

def extract_from_backup_files(session_id: str, backup_directory: str) -> Dict[str, Any]:
    """Fallback extraction from backup files"""
    backup_data = {
        "scenario_data": None,
        "problematic_messages": None,
        "corrected_messages": None,
        "playbook_data": None,
        "extraction_log": ["Using backup file extraction"],
        "parsing_success": False,
        "total_tasks_found": 0
    }
    
    backup_dir = Path(backup_directory)
    if not backup_dir.exists():
        backup_data["extraction_log"].append("❌ Backup directory not found")
        return backup_data
    
    # Look for backup files
    task_files = {
        "scenario": "scenario_creation_task_backup.json",
        "mistake": "mistake_generation_task_backup.json", 
        "best_practice": "best_practice_transformation_task_backup.json",
        "playbook": "playbook_task_backup.json"
    }
    
    for task_type, filename in task_files.items():
        file_path = backup_dir / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    backup_file_data = json.load(f)
                    task_data = backup_file_data.get("data", {})
                    
                    if task_type == "scenario":
                        backup_data["scenario_data"] = task_data
                    elif task_type == "mistake":
                        backup_data["problematic_messages"] = task_data
                    elif task_type == "best_practice":
                        backup_data["corrected_messages"] = task_data
                    elif task_type == "playbook":
                        backup_data["playbook_data"] = task_data
                    
                    backup_data["total_tasks_found"] += 1
                    backup_data["extraction_log"].append(f"✅ Loaded {task_type} from backup")
                    
            except Exception as e:
                backup_data["extraction_log"].append(f"❌ Failed to load {task_type} backup: {str(e)}")
    
    backup_data["parsing_success"] = backup_data["total_tasks_found"] >= 3
    return backup_data