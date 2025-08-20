from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool, SerperDevTool
from pydantic import BaseModel, Field
from typing import List
import os
from datetime import datetime

# Add Panel callback imports
from .callbacks import print_task_output, get_panel_callback_handler

# Pydantic Models for Structured Outputs
class SustainabilityScenario(BaseModel):
    """A realistic business scenario for sustainability messaging training"""
    company_name: str = Field(description="Company name")
    industry: str = Field(description="Industry sector")
    company_size: str = Field(description="Company size (startup, SME, large corporation)")
    location: str = Field(description="Company location/market")
    product_service: str = Field(description="Main product or service offered")
    target_audience: str = Field(description="Primary target audience for marketing")
    marketing_objectives: List[str] = Field(description="Key marketing objectives")
    sustainability_context: str = Field(description="Current sustainability challenges and context")
    preliminary_claims: List[str] = Field(description="Initial sustainability claims the company wants to make")
    regulatory_context: str = Field(description="Relevant regulatory requirements (EU directives, etc.)")
    market_research_sources: List[str] = Field(description="Sources used to create this scenario")

class ProblematicMessage(BaseModel):
    """A problematic sustainability message with detailed analysis"""
    id: str = Field(description="Unique identifier for this message")
    message: str = Field(description="The problematic sustainability message")
    problems_identified: List[str] = Field(description="Specific problems with this message")
    regulatory_violations: List[str] = Field(description="Specific regulations this violates")
    greenwashing_patterns: List[str] = Field(description="Greenwashing patterns demonstrated")
    real_world_examples: List[str] = Field(description="Real companies/cases that made similar mistakes")
    why_problematic: str = Field(description="Detailed explanation of why this message is problematic")
    potential_consequences: List[str] = Field(description="Potential legal/reputational consequences")

class ProblematicMessageAnalysis(BaseModel):
    """Complete analysis of problematic sustainability messages"""
    scenario_reference: str = Field(description="Reference to the business scenario")
    problematic_messages: List[ProblematicMessage] = Field(description="List of problematic messages with analysis")
    general_patterns_found: List[str] = Field(description="Common greenwashing patterns identified")
    regulatory_landscape: str = Field(description="Current regulatory landscape overview")
    research_sources: List[str] = Field(description="Sources used for real-world examples")

class CorrectedMessage(BaseModel):
    """A corrected sustainability message with best practices"""
    original_message_id: str = Field(description="Reference to the original problematic message")
    corrected_message: str = Field(description="The improved, compliant message")
    changes_made: List[str] = Field(description="Specific changes made to fix the problems")
    compliance_notes: str = Field(description="How this message ensures regulatory compliance")
    best_practices_applied: List[str] = Field(description="Best practices applied in the correction")
    real_world_examples: List[str] = Field(description="Companies that use similar effective messaging")
    effectiveness_rationale: str = Field(description="Why this corrected message is effective")

class BestPracticeGuidance(BaseModel):
    """Complete best practice guidance for sustainability messaging"""
    scenario_reference: str = Field(description="Reference to the business scenario")
    corrected_messages: List[CorrectedMessage] = Field(description="List of corrected messages")
    general_guidelines: List[str] = Field(description="General guidelines for compliant messaging")
    key_principles: List[str] = Field(description="Key principles for effective sustainability communication")
    regulatory_compliance_tips: List[str] = Field(description="Tips for ensuring regulatory compliance")
    industry_specific_advice: str = Field(description="Advice specific to the industry in the scenario")
    research_sources: List[str] = Field(description="Sources for best practices and examples")

class CaseStudySnapshot(BaseModel):
    """A case study example in the playbook"""
    title: str = Field(description="Case study title")
    company_name: str = Field(description="Company name (can be anonymized)")
    message_type: str = Field(description="good_example or bad_example")
    original_message: str = Field(description="The original sustainability message")
    analysis: str = Field(description="Analysis of why it works or doesn't work")
    key_lesson: str = Field(description="Key takeaway from this example")
    regulatory_context: str = Field(description="Relevant regulatory considerations")

class ClaimToProofFramework(BaseModel):
    """Framework for transforming claims into credible messages"""
    framework_name: str = Field(description="Name of the framework")
    steps: List[str] = Field(description="Step-by-step process for claim validation")
    validation_questions: List[str] = Field(description="Questions to ask when validating claims")
    proof_requirements: List[str] = Field(description="Types of proof needed for different claims")
    common_pitfalls: List[str] = Field(description="Common mistakes to avoid")
    examples: List[str] = Field(description="Example applications of the framework")

class ComplianceChecklist(BaseModel):
    """Quick compliance validation checklist"""
    checklist_name: str = Field(description="Name of the checklist")
    categories: List[str] = Field(description="Main categories to check")
    questions: List[str] = Field(description="Specific validation questions")
    red_flags: List[str] = Field(description="Warning signs to watch for")
    approval_criteria: List[str] = Field(description="Criteria for message approval")

class SustainabilityMessagingPlaybook(BaseModel):
    """Complete sustainability messaging playbook"""
    playbook_title: str = Field(description="Title of the playbook")
    creation_date: str = Field(description="Date the playbook was created")
    target_audience: str = Field(description="Intended audience for this playbook")
    
    # Core Content Sections
    executive_summary: str = Field(description="Executive summary of key points")
    dos_and_donts: List[str] = Field(description="Clear do's and don'ts for sustainability messaging")
    greenwashing_patterns: List[str] = Field(description="Common greenwashing patterns to avoid")
    
    # Frameworks and Tools
    claim_to_proof_framework: ClaimToProofFramework = Field(description="Framework for validating claims")
    compliance_checklist: ComplianceChecklist = Field(description="Quick validation checklist")
    
    # Case Studies and Examples
    case_study_snapshots: List[CaseStudySnapshot] = Field(description="Real-world examples")
    
    # Reference Materials
    regulatory_references: List[str] = Field(description="Key regulatory requirements and sources")
    additional_resources: List[str] = Field(description="Additional learning resources")
    
    # Implementation Guide
    quick_start_guide: List[str] = Field(description="Steps to start implementing the playbook")
    team_training_tips: List[str] = Field(description="Tips for training marketing teams")
    
    # Appendices
    glossary_terms: List[str] = Field(description="Key terms and definitions")
    contact_resources: List[str] = Field(description="Who to contact for help")

@CrewBase
class Sustainability():
    """Sustainability Messaging Training Crew"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self) -> None:
        self.user_preferences = self._load_user_preferences()
        self._ensure_output_directory()
        # Initialize search tool
        self.search_tool = SerperDevTool()
        
    def _load_user_preferences(self):
        """Load user preferences from knowledge folder"""
        try:
            with open('knowledge/user_preference.txt', 'r') as file:
                return file.read()
        except FileNotFoundError:
            return "No user preferences found"
    
    def _ensure_output_directory(self):
        """Create outputs directory if it doesn't exist"""
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
    
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
        return Task(
            config=self.tasks_config['scenario_creation_task'],
            agent=self.scenario_builder(),
            output_pydantic=SustainabilityScenario,
            callback=print_task_output
        )
    
    @task
    def mistake_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config['mistake_generation_task'],
            agent=self.mistake_illustrator(),
            output_pydantic=ProblematicMessageAnalysis,
            callback=print_task_output
        )
    
    @task
    def best_practice_transformation_task(self) -> Task:
        return Task(
            config=self.tasks_config['best_practice_transformation_task'],
            agent=self.best_practice_coach(),
            output_pydantic=BestPracticeGuidance,
            callback=print_task_output
        )
    
    @task
    def playbook_task(self) -> Task:
        return Task(
            config=self.tasks_config['playbook_task'],
            agent=self.playbook_creator(),
            output_pydantic=SustainabilityMessagingPlaybook,
            output_file='outputs/sustainability_messaging_playbook.json',
            callback=print_task_output
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Sustainability Training crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False,  # Disabled to avoid ChromaDB warnings for MVP
            output_log_file="outputs/training_session.log"
        )