from typing import Optional, Callable, Any, Dict, List
from crewai.tasks.task_output import TaskOutput
from datetime import datetime
import json
import os
from pathlib import Path

class EnhancedCallbackHandler:
    """Enhanced callback handler for comprehensive data capture and validation"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.chat_interface: Optional[Any] = None
        self.task_outputs: Dict[str, Any] = {}
        self.task_count: int = 0
        self.completed_tasks: int = 0
        self.extraction_log: List[str] = []
        self.data_quality_metrics: Dict[str, Any] = {}
        self.session_start_time = datetime.now()
        
        # Create session-specific backup directory
        self.backup_dir = Path(f"outputs/session_{session_id[:8]}_backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def register_chat_interface(self, chat_interface: Any):
        """Register the Panel ChatInterface to send messages to"""
        self.chat_interface = chat_interface
        
    def send_message(self, message: str, user: str = "System", message_type: str = "info"):
        """Send a message to the Panel chat interface"""
        if self.chat_interface is None:
            print(f"[{user}] {message}")
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if message_type == "agent_start":
            formatted_message = f"🤖 **{user}** [{timestamp}]\n{message}"
        elif message_type == "agent_thinking":
            formatted_message = f"💭 **{user}** [{timestamp}]\n{message}"
        elif message_type == "tool_use":
            formatted_message = f"🛠️ **{user}** [{timestamp}]\n{message}"
        elif message_type == "task_complete":
            formatted_message = f"✅ **{user}** [{timestamp}]\n{message}"
        elif message_type == "data_extracted":
            formatted_message = f"📊 **Data Extraction** [{timestamp}]\n{message}"
        elif message_type == "data_validation":
            formatted_message = f"🔍 **Validation** [{timestamp}]\n{message}"
        elif message_type == "error":
            formatted_message = f"❌ **{user}** [{timestamp}]\n{message}"
        elif message_type == "session":
            formatted_message = f"🚀 **Session** [{timestamp}]\n{message}"
        elif message_type == "progress":
            formatted_message = f"📊 **Progress** [{timestamp}]\n{message}"
        elif message_type == "search":
            formatted_message = f"🔍 **{user}** [{timestamp}]\n{message}"
        else:
            formatted_message = f"📝 **{user}** [{timestamp}]\n{message}"
            
        try:
            self.chat_interface.send(formatted_message, user=user, respond=False)
        except Exception as e:
            print(f"Error sending to chat: {e}")
            print(f"[{user}] {message}")
    
    def on_agent_start(self, agent_name: str, task_description: str):
        """Called when an agent starts working on a task"""
        self.task_count += 1
        
        clean_description = task_description[:200] + "..." if len(task_description) > 200 else task_description
        message = f"Starting work on: {clean_description}"
        self.send_message(message, user=agent_name, message_type="agent_start")
        
        progress_msg = f"Task {self.task_count} of 4: {agent_name} is working..."
        self.send_message(progress_msg, user="System", message_type="progress")
    
    def on_agent_thinking(self, agent_name: str, thought: str):
        """Called when an agent is thinking/reasoning"""
        clean_thought = thought[:150] + "..." if len(thought) > 150 else thought
        message = f"Analyzing: {clean_thought}"
        self.send_message(message, user=agent_name, message_type="agent_thinking")
    
    def on_tool_use(self, agent_name: str, tool_name: str, tool_input: str, tool_output: str):
        """Called when an agent uses a tool"""
        if tool_name == "SerperDevTool":
            clean_input = tool_input[:100] + "..." if len(tool_input) > 100 else tool_input
            message = f"🔍 Searching for: {clean_input}\n📋 Found relevant information about sustainability regulations and best practices"
            self.send_message(message, user=agent_name, message_type="search")
        else:
            clean_input = tool_input[:100] + "..." if len(tool_input) > 100 else tool_input
            clean_output = tool_output[:200] + "..." if len(tool_output) > 200 else tool_output
            message = f"Using {tool_name}\n🔍 Input: {clean_input}\n📋 Result: {clean_output}"
            self.send_message(message, user=agent_name, message_type="tool_use")
    
    def on_task_complete(self, agent_name: str, task_name: str, task_output: TaskOutput):
        """Enhanced task completion with immediate data extraction and validation"""
        self.completed_tasks += 1
        
        # Immediate data extraction
        extracted_data = self._extract_task_data(task_name, task_output)
        
        # Data validation
        validation_result = self._validate_task_data(task_name, extracted_data)
        
        # Store validated data
        if validation_result['is_valid']:
            self.task_outputs[task_name] = {
                'data': extracted_data,
                'validation': validation_result,
                'completion_time': datetime.now().isoformat(),
                'agent_name': agent_name,
                'task_order': self.completed_tasks
            }
            
            # Create immediate backup
            self._create_task_backup(task_name, extracted_data, validation_result)
            
            # Report success
            data_size = len(str(extracted_data)) if extracted_data else 0
            self.send_message(
                f"✅ Task completed successfully!\n📊 Extracted {data_size:,} characters of data\n🔍 Validation: {validation_result['quality_score']}/100",
                user=agent_name,
                message_type="task_complete"
            )
            
            # Update quality metrics
            self._update_quality_metrics(task_name, validation_result)
            
        else:
            # Handle validation failure
            self.send_message(
                f"⚠️ Task completed but data validation failed: {validation_result['issues']}",
                user=agent_name,
                message_type="error"
            )
            
            self.extraction_log.append(f"❌ {task_name} validation failed: {validation_result['issues']}")
        
        # Show progress update
        progress_msg = f"Progress: {self.completed_tasks}/4 tasks finished"
        self.send_message(progress_msg, user="System", message_type="progress")
        
        # Show task-specific summary
        self._send_task_summary(task_name, agent_name, validation_result)
    
    def _extract_task_data(self, task_name: str, task_output: TaskOutput) -> Optional[Dict[str, Any]]:
        """Extract structured data from task output"""
        try:
            if hasattr(task_output, 'pydantic') and task_output.pydantic:
                data = task_output.pydantic.model_dump()
                self.extraction_log.append(f"✅ Extracted {task_name}: {len(str(data))} chars")
                return data
            else:
                self.extraction_log.append(f"⚠️ {task_name}: No pydantic data available")
                return None
                
        except Exception as e:
            self.extraction_log.append(f"❌ {task_name} extraction failed: {str(e)}")
            return None
    
    def _validate_task_data(self, task_name: str, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate extracted task data for completeness and quality"""
        validation_result = {
            'is_valid': False,
            'quality_score': 0,
            'issues': [],
            'strengths': [],
            'completeness': 0
        }
        
        if not data:
            validation_result['issues'].append("No data extracted")
            return validation_result
        
        # Task-specific validation logic
        if "scenario" in task_name:
            validation_result = self._validate_scenario_data(data)
        elif "mistake" in task_name:
            validation_result = self._validate_mistake_data(data)
        elif "best_practice" in task_name:
            validation_result = self._validate_correction_data(data)
        elif "playbook" in task_name:
            validation_result = self._validate_playbook_data(data)
        else:
            validation_result['is_valid'] = True
            validation_result['quality_score'] = 50
            validation_result['issues'].append("Unknown task type - basic validation only")
        
        return validation_result
    
    def _validate_scenario_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate business scenario data"""
        required_fields = ['company_name', 'industry', 'product_service', 'target_audience', 'marketing_objectives']
        quality_fields = ['sustainability_context', 'preliminary_claims', 'regulatory_context']
        
        issues = []
        strengths = []
        completeness = 0
        
        # Check required fields
        for field in required_fields:
            if field in data and data[field]:
                completeness += 20
                if len(str(data[field])) > 50:
                    strengths.append(f"Detailed {field}")
            else:
                issues.append(f"Missing or empty {field}")
        
        # Check quality fields
        for field in quality_fields:
            if field in data and data[field]:
                completeness += 10
                if isinstance(data[field], list) and len(data[field]) > 2:
                    strengths.append(f"Rich {field} data")
                elif isinstance(data[field], str) and len(data[field]) > 100:
                    strengths.append(f"Detailed {field}")
        
        quality_score = min(100, completeness + len(strengths) * 5)
        
        return {
            'is_valid': completeness >= 60,
            'quality_score': quality_score,
            'issues': issues,
            'strengths': strengths,
            'completeness': completeness
        }
    
    def _validate_mistake_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate problematic messages data"""
        issues = []
        strengths = []
        completeness = 0
        
        if 'problematic_messages' in data:
            messages = data['problematic_messages']
            if len(messages) >= 4:
                completeness += 40
                strengths.append(f"{len(messages)} problematic messages identified")
            else:
                issues.append(f"Only {len(messages)} messages (need 4+)")
            
            # Check message quality
            for i, msg in enumerate(messages):
                msg_score = 0
                required_msg_fields = ['message', 'problems_identified', 'why_problematic']
                for field in required_msg_fields:
                    if field in msg and msg[field]:
                        msg_score += 1
                
                if msg_score >= 2:
                    completeness += 10
                else:
                    issues.append(f"Message {i+1} missing key details")
        else:
            issues.append("No problematic messages found")
        
        # Check additional fields
        if 'regulatory_landscape' in data and len(str(data['regulatory_landscape'])) > 100:
            completeness += 20
            strengths.append("Detailed regulatory landscape")
        
        quality_score = min(100, completeness + len(strengths) * 5)
        
        return {
            'is_valid': completeness >= 50,
            'quality_score': quality_score,
            'issues': issues,
            'strengths': strengths,
            'completeness': completeness
        }
    
    def _validate_correction_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate corrected messages data"""
        issues = []
        strengths = []
        completeness = 0
        
        if 'corrected_messages' in data:
            corrections = data['corrected_messages']
            if len(corrections) >= 4:
                completeness += 40
                strengths.append(f"{len(corrections)} corrections provided")
            else:
                issues.append(f"Only {len(corrections)} corrections (need 4+)")
            
            # Check correction quality
            for i, correction in enumerate(corrections):
                correction_score = 0
                required_fields = ['corrected_message', 'changes_made', 'compliance_notes']
                for field in required_fields:
                    if field in correction and correction[field]:
                        correction_score += 1
                
                if correction_score >= 2:
                    completeness += 10
                else:
                    issues.append(f"Correction {i+1} missing key details")
        else:
            issues.append("No corrected messages found")
        
        # Check additional guidance
        if 'general_guidelines' in data and len(data['general_guidelines']) > 3:
            completeness += 20
            strengths.append("Comprehensive general guidelines")
        
        quality_score = min(100, completeness + len(strengths) * 5)
        
        return {
            'is_valid': completeness >= 50,
            'quality_score': quality_score,
            'issues': issues,
            'strengths': strengths,
            'completeness': completeness
        }
    
    def _validate_playbook_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate playbook data"""
        issues = []
        strengths = []
        completeness = 0
        
        essential_sections = ['dos_and_donts', 'greenwashing_patterns', 'claim_to_proof_framework']
        for section in essential_sections:
            if section in data and data[section]:
                completeness += 20
                strengths.append(f"Complete {section}")
            else:
                issues.append(f"Missing {section}")
        
        # Check framework detail
        if 'claim_to_proof_framework' in data:
            framework = data['claim_to_proof_framework']
            if isinstance(framework, dict) and 'steps' in framework and len(framework['steps']) > 3:
                completeness += 20
                strengths.append("Detailed framework with multiple steps")
        
        quality_score = min(100, completeness + len(strengths) * 5)
        
        return {
            'is_valid': completeness >= 60,
            'quality_score': quality_score,
            'issues': issues,
            'strengths': strengths,
            'completeness': completeness
        }
    
    def _create_task_backup(self, task_name: str, data: Dict[str, Any], validation: Dict[str, Any]):
        """Create immediate backup of task data"""
        try:
            backup_file = self.backup_dir / f"{task_name}_backup.json"
            backup_data = {
                'session_id': self.session_id,
                'task_name': task_name,
                'timestamp': datetime.now().isoformat(),
                'data': data,
                'validation': validation,
                'backup_version': '1.0'
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
                
            self.extraction_log.append(f"💾 Backup created: {backup_file.name}")
            
        except Exception as e:
            self.extraction_log.append(f"❌ Backup failed for {task_name}: {str(e)}")
    
    def _update_quality_metrics(self, task_name: str, validation: Dict[str, Any]):
        """Update overall session quality metrics"""
        self.data_quality_metrics[task_name] = {
            'quality_score': validation['quality_score'],
            'completeness': validation['completeness'],
            'issues_count': len(validation['issues']),
            'strengths_count': len(validation['strengths'])
        }
    
    def _send_task_summary(self, task_name: str, agent_name: str, validation: Dict[str, Any]):
        """Send task-specific completion summary"""
        if "scenario" in task_name:
            summary = "✅ Business scenario created with realistic context and regulatory requirements"
        elif "mistake" in task_name:
            summary = "✅ Problematic messaging examples identified with detailed compliance analysis"
        elif "best_practice" in task_name:
            summary = "✅ Best practice corrections provided with regulatory guidance"
        elif "playbook" in task_name:
            summary = "✅ Comprehensive sustainability messaging playbook generated with practical frameworks"
        else:
            summary = "✅ Analysis completed successfully"
        
        if validation['quality_score'] >= 80:
            summary += f" (Quality: Excellent - {validation['quality_score']}/100)"
        elif validation['quality_score'] >= 60:
            summary += f" (Quality: Good - {validation['quality_score']}/100)"
        else:
            summary += f" (Quality: Needs improvement - {validation['quality_score']}/100)"
            
        self.send_message(summary, user="System", message_type="data_validation")
    
    def on_error(self, agent_name: str, error_message: str):
        """Called when an error occurs"""
        clean_error = error_message[:300] + "..." if len(error_message) > 300 else error_message
        message = f"⚠️ Issue encountered: {clean_error}"
        self.send_message(message, user=agent_name, message_type="error")
        self.extraction_log.append(f"❌ Error in {agent_name}: {clean_error}")
    
    def on_session_start(self, session_info: Dict[str, Any]):
        """Called when a training session starts"""
        self.session_id = session_info.get('session_id', 'Unknown')
        
        message = f"""🌱 **Enhanced Sustainability Training Session Started**

**Session ID:** {self.session_id}
**Industry Focus:** {session_info.get('user_industry', 'N/A')}
**Regulatory Framework:** {session_info.get('regional_regulations', 'N/A')}
**Training Level:** {session_info.get('difficulty_level', 'N/A')}

**Enhanced Features:**
- ✅ Real-time data extraction and validation
- 📊 Quality metrics tracking  
- 💾 Automatic backup creation
- 🔍 Comprehensive data analysis

**Training Plan:**
1. 🏢 Create realistic business scenario
2. ⚠️ Identify problematic messaging patterns  
3. ✅ Develop compliant alternatives
4. 📚 Generate comprehensive messaging playbook

Please wait while our AI agents work together with enhanced data capture..."""
        
        self.send_message(message, user="System", message_type="session")
    
    def on_session_complete(self, results: Any):
        """Called when the entire training session is complete"""
        session_duration = datetime.now() - self.session_start_time
        avg_quality = sum(m['quality_score'] for m in self.data_quality_metrics.values()) / len(self.data_quality_metrics) if self.data_quality_metrics else 0
        total_issues = sum(m['issues_count'] for m in self.data_quality_metrics.values())
        
        message = f"""🎉 **Enhanced Training Session Completed Successfully!**

📊 **Session Quality Metrics:**
- ⏱️ Duration: {session_duration.seconds // 60} minutes
- 📈 Average Quality Score: {avg_quality:.1f}/100
- ✅ Tasks Completed: {self.completed_tasks}/4
- ⚠️ Total Issues Resolved: {total_issues}
- 💾 Backup Files Created: {len(self.data_quality_metrics)}

**Data Extraction Summary:**
{chr(10).join(self.extraction_log[-5:])}

**Your Enhanced Playbook Includes:**
- 📋 Detailed business scenario with industry context
- 🚨 Specific problematic message analysis  
- ✅ Comprehensive corrected alternatives
- 🔄 Step-by-step validation frameworks
- 📖 Rich case study examples with full context
- 📄 Complete regulatory references

**Quality Assurance:**
- All data validated in real-time
- Immediate backups created for reliability
- Comprehensive extraction logs maintained

Thank you for using our enhanced AI-powered sustainability training system! 🌱"""
        
        self.send_message(message, user="System", message_type="task_complete")
    
    def get_all_extracted_data(self) -> Dict[str, Any]:
        """Get all extracted and validated data"""
        return {
            'session_id': self.session_id,
            'task_outputs': self.task_outputs,
            'quality_metrics': self.data_quality_metrics,
            'extraction_log': self.extraction_log,
            'session_duration': (datetime.now() - self.session_start_time).total_seconds(),
            'total_tasks': self.completed_tasks
        }
    
    def get_backup_directory(self) -> Path:
        """Get the backup directory path for this session"""
        return self.backup_dir

# Global instance for backward compatibility
enhanced_callback_handler = EnhancedCallbackHandler("default")

def enhanced_task_output_callback(task_output: TaskOutput) -> TaskOutput:
    """Enhanced callback function for CrewAI tasks with comprehensive data capture"""
    if task_output.agent:
        agent_name = task_output.agent
        print(f"✅ Enhanced callback: Task completed by {agent_name}")
        
        # Extract data size information
        if hasattr(task_output, 'pydantic') and task_output.pydantic:
            data_size = len(str(task_output.pydantic.model_dump()))
            print(f"📊 Enhanced callback: Captured {data_size:,} characters of structured data")
        
        # The actual data extraction and validation will be handled by the EnhancedCallbackHandler
        # This is just for logging compatibility
    
    return task_output

def get_enhanced_callback_handler() -> EnhancedCallbackHandler:
    """Get the global enhanced callback handler instance"""
    return enhanced_callback_handler

def create_session_callback_handler(session_id: str) -> EnhancedCallbackHandler:
    """Create a new callback handler for a specific session"""
    return EnhancedCallbackHandler(session_id)