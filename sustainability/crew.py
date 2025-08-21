from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool, SerperDevTool
from datetime import datetime
import os
import json
from pathlib import Path

@CrewBase
class Sustainability():
    """Clean Sustainability Messaging Training Crew with direct artifact generation"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self, session_id: str = None, artifact_directory: str = None) -> None:
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.artifact_directory = artifact_directory or f"outputs/{self.session_id}"
        self.user_preferences = self._load_user_preferences()
        self.search_tool = SerperDevTool()
        
        # Ensure artifact directory exists
        Path(self.artifact_directory).mkdir(parents=True, exist_ok=True)
        
    def _load_user_preferences(self):
        """Load user preferences from knowledge folder"""
        try:
            with open('knowledge/user_preference.txt', 'r') as file:
                return file.read()
        except FileNotFoundError:
            return "No user preferences found"
    
    def _write_artifact(self, filename: str, data: dict) -> bool:
        """Write data to artifact file with validation"""
        try:
            artifact_path = Path(self.artifact_directory) / filename
            
            # Write to temporary file first (atomic write)
            temp_path = artifact_path.with_suffix('.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Rename to final file (atomic operation)
            temp_path.rename(artifact_path)
            
            print(f"✅ Artifact written successfully: {artifact_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to write artifact {filename}: {str(e)}")
            return False
    
    def _validate_scenario_artifact(self, data: dict) -> bool:
        """Validate scenario artifact has required fields"""
        required_fields = [
            'company_name', 'industry', 'company_size', 'location', 
            'product_service', 'target_audience', 'marketing_objectives',
            'sustainability_context', 'preliminary_claims', 'regulatory_context'
        ]
        
        for field in required_fields:
            if field not in data or not data[field]:
                print(f"❌ Scenario validation failed: Missing {field}")
                return False
        
        # Validate marketing objectives has at least 3 items
        if len(data.get('marketing_objectives', [])) < 3:
            print(f"❌ Scenario validation failed: Need at least 3 marketing objectives")
            return False
            
        return True
    
    def _validate_problems_artifact(self, data: dict) -> bool:
        """Validate problems artifact has exactly 4 complete messages"""
        if 'problematic_messages' not in data:
            print(f"❌ Problems validation failed: Missing problematic_messages")
            return False
        
        messages = data['problematic_messages']
        if len(messages) != 4:
            print(f"❌ Problems validation failed: Need exactly 4 messages, got {len(messages)}")
            return False
        
        required_msg_fields = ['id', 'message', 'problems_identified', 'regulatory_violations', 'why_problematic']
        for i, msg in enumerate(messages):
            for field in required_msg_fields:
                if field not in msg or not msg[field]:
                    print(f"❌ Problems validation failed: Message {i+1} missing {field}")
                    return False
        
        return True
    
    def _validate_corrections_artifact(self, data: dict) -> bool:
        """Validate corrections artifact has 4 complete corrections"""
        if 'corrected_messages' not in data:
            print(f"❌ Corrections validation failed: Missing corrected_messages")
            return False
        
        corrections = data['corrected_messages']
        if len(corrections) != 4:
            print(f"❌ Corrections validation failed: Need exactly 4 corrections, got {len(corrections)}")
            return False
        
        required_fields = ['original_message_id', 'corrected_message', 'changes_made', 'compliance_notes']
        for i, correction in enumerate(corrections):
            for field in required_fields:
                if field not in correction or not correction[field]:
                    print(f"❌ Corrections validation failed: Correction {i+1} missing {field}")
                    return False
        
        return True
    
    def _validate_implementation_artifact(self, data: dict) -> bool:
        """Validate implementation artifact has sufficient content"""
        required_sections = ['implementation_roadmap', 'success_metrics']
        
        for section in required_sections:
            if section not in data or not data[section]:
                print(f"❌ Implementation validation failed: Missing {section}")
                return False
            
            # Check minimum content
            if len(data[section]) < 3:
                print(f"❌ Implementation validation failed: {section} needs at least 3 items")
                return False
        
        return True
    
    @agent
    def scenario_builder(self) -> Agent:
        return Agent(
            config=self.agents_config['scenario_builder'],
            tools=[
                FileReadTool(file_path='knowledge/user_preference.txt'),
                self.search_tool
            ],
            verbose=True
        )
    
    @agent
    def mistake_illustrator(self) -> Agent:
        return Agent(
            config=self.agents_config['mistake_illustrator'],
            tools=[self.search_tool],
            verbose=True
        )
    
    @agent
    def best_practice_coach(self) -> Agent:
        return Agent(
            config=self.agents_config['best_practice_coach'],
            tools=[self.search_tool],
            verbose=True
        )
    
    @agent
    def playbook_creator(self) -> Agent:
        return Agent(
            config=self.agents_config['playbook_creator'],
            tools=[self.search_tool],
            verbose=True
        )
    
    @task
    def scenario_creation_task(self) -> Task:
        def write_scenario_artifact(task_output):
            """Write scenario data directly to JSON file"""
            try:
                # Extract structured data from task output
                if hasattr(task_output, 'raw'):
                    # Try to parse JSON from raw output
                    import re
                    json_match = re.search(r'\{.*\}', task_output.raw, re.DOTALL)
                    if json_match:
                        scenario_data = json.loads(json_match.group())
                    else:
                        raise Exception("No JSON found in task output")
                else:
                    raise Exception("No raw output available")
                
                # Validate the data
                if not self._validate_scenario_artifact(scenario_data):
                    raise Exception("Scenario validation failed")
                
                # Write to artifact file
                if not self._write_artifact('scenario.json', scenario_data):
                    raise Exception("Failed to write scenario artifact")
                
                print(f"✅ Scenario artifact created successfully")
                return task_output
                
            except Exception as e:
                print(f"❌ Scenario task failed: {str(e)}")
                raise Exception(f"Scenario creation failed: {str(e)}")
        
        return Task(
            config=self.tasks_config['scenario_creation_task'],
            agent=self.scenario_builder(),
            callback=write_scenario_artifact
        )
    
    @task
    def mistake_generation_task(self) -> Task:
        def write_problems_artifact(task_output):
            """Write problems data directly to JSON file"""
            try:
                # Extract structured data from task output
                if hasattr(task_output, 'raw'):
                    import re
                    json_match = re.search(r'\{.*\}', task_output.raw, re.DOTALL)
                    if json_match:
                        problems_data = json.loads(json_match.group())
                    else:
                        raise Exception("No JSON found in task output")
                else:
                    raise Exception("No raw output available")
                
                # Validate the data
                if not self._validate_problems_artifact(problems_data):
                    raise Exception("Problems validation failed")
                
                # Write to artifact file
                if not self._write_artifact('problems.json', problems_data):
                    raise Exception("Failed to write problems artifact")
                
                print(f"✅ Problems artifact created successfully")
                return task_output
                
            except Exception as e:
                print(f"❌ Problems task failed: {str(e)}")
                raise Exception(f"Problems generation failed: {str(e)}")
        
        return Task(
            config=self.tasks_config['mistake_generation_task'],
            agent=self.mistake_illustrator(),
            callback=write_problems_artifact
        )
    
    @task
    def best_practice_transformation_task(self) -> Task:
        def write_corrections_artifact(task_output):
            """Write corrections data directly to JSON file"""
            try:
                # Extract structured data from task output
                if hasattr(task_output, 'raw'):
                    import re
                    json_match = re.search(r'\{.*\}', task_output.raw, re.DOTALL)
                    if json_match:
                        corrections_data = json.loads(json_match.group())
                    else:
                        raise Exception("No JSON found in task output")
                else:
                    raise Exception("No raw output available")
                
                # Validate the data
                if not self._validate_corrections_artifact(corrections_data):
                    raise Exception("Corrections validation failed")
                
                # Write to artifact file
                if not self._write_artifact('corrections.json', corrections_data):
                    raise Exception("Failed to write corrections artifact")
                
                print(f"✅ Corrections artifact created successfully")
                return task_output
                
            except Exception as e:
                print(f"❌ Corrections task failed: {str(e)}")
                raise Exception(f"Corrections generation failed: {str(e)}")
        
        return Task(
            config=self.tasks_config['best_practice_transformation_task'],
            agent=self.best_practice_coach(),
            callback=write_corrections_artifact
        )
    
    @task
    def implementation_task(self) -> Task:
        def write_implementation_artifact(task_output):
            """Write implementation data directly to JSON file"""
            try:
                # Extract structured data from task output
                if hasattr(task_output, 'raw'):
                    import re
                    json_match = re.search(r'\{.*\}', task_output.raw, re.DOTALL)
                    if json_match:
                        implementation_data = json.loads(json_match.group())
                    else:
                        raise Exception("No JSON found in task output")
                else:
                    raise Exception("No raw output available")
                
                # Validate the data
                if not self._validate_implementation_artifact(implementation_data):
                    raise Exception("Implementation validation failed")
                
                # Write to artifact file
                if not self._write_artifact('implementation.json', implementation_data):
                    raise Exception("Failed to write implementation artifact")
                
                print(f"✅ Implementation artifact created successfully")
                return task_output
                
            except Exception as e:
                print(f"❌ Implementation task failed: {str(e)}")
                raise Exception(f"Implementation generation failed: {str(e)}")
        
        return Task(
            config=self.tasks_config['implementation_task'],
            agent=self.playbook_creator(),
            callback=write_implementation_artifact
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the clean Sustainability Training crew with direct artifact generation"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False
        )