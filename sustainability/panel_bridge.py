#!/usr/bin/env python
"""
Panel Bridge for Sustainability Training Application
"""

import panel as pn
import asyncio
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Configure Panel
pn.extension()

def is_web_environment():
    """Detect if running in web deployment vs local development"""
    return bool(os.environ.get('PORT'))

class SustainabilityPanelApp:
    """Panel application wrapper for Sustainability Training"""
    
    def __init__(self):
        self.setup_components()
        self.latest_results = None
        self.training_in_progress = False
        
        # Configure for web if needed
        if is_web_environment():
            pn.config.autoreload = False
            pn.config.dev = False
        else:
            pn.config.autoreload = True
        
    def setup_components(self):
        """Setup Panel components"""
        
        # Header
        self.header = pn.pane.Markdown("""
        # 🌱 Sustainability Training AI
        
        **AI-Powered Training for Compliant Sustainability Communications**
        
        Get personalized training scenarios, identify greenwashing risks, and learn best practices 
        for creating compliant sustainability messages that meet current EU regulations.
        """, sizing_mode="stretch_width")
        
        # Chat interface for real-time feedback
        self.chat_interface = pn.chat.ChatInterface(
            callback=self.handle_chat_message,
            height=400,
            sizing_mode="stretch_width",
            placeholder_text="Ask questions about sustainability messaging or start a training session..."
        )
        
        # Industry selection
        self.industry_select = pn.widgets.Select(
            name="Industry Focus",
            value="Marketing Agency",
            options=[
                "Marketing Agency", 
                "Fashion & Retail", 
                "Food & Beverage", 
                "Technology", 
                "Financial Services",
                "Real Estate",
                "Manufacturing",
                "Other"
            ],
            sizing_mode="stretch_width"
        )
        
        # Regulatory framework selection
        self.regulatory_select = pn.widgets.Select(
            name="Regulatory Framework",
            value="EU",
            options=[
                "EU",
                "USA", 
                "UK",
                "Global"
            ],
            sizing_mode="stretch_width"
        )
        
        # Difficulty level
        self.difficulty_select = pn.widgets.Select(
            name="Training Level",
            value="Intermediate",
            options=["Beginner", "Intermediate", "Advanced"],
            sizing_mode="stretch_width"
        )
        
        # Start training button
        self.start_button = pn.widgets.Button(
            name="🚀 Start Training Session",
            button_type="primary",
            sizing_mode="stretch_width",
            height=50
        )
        self.start_button.on_click(self.start_training)
        
        # Download buttons (initially disabled)
        self.download_md_button = pn.widgets.Button(
            name="📚 Download Playbook (Markdown)",
            button_type="default",
            sizing_mode="stretch_width",
            disabled=True
        )
        self.download_md_button.on_click(self.download_markdown_playbook)
        
        self.download_pdf_button = pn.widgets.Button(
            name="📑 PDF Instructions",
            button_type="default",
            sizing_mode="stretch_width",
            disabled=True
        )
        self.download_pdf_button.on_click(self.download_pdf_instructions)
        
        # Status indicator
        self.status_indicator = pn.pane.Markdown(
            "**Status:** Ready to start training 🟢",
            sizing_mode="stretch_width"
        )
        
        # Progress indicator
        self.progress_bar = pn.indicators.Progress(
            name="Training Progress",
            value=0,
            max=100,
            sizing_mode="stretch_width",
            visible=False
        )
    
    def get_regulatory_details(self, region: str) -> Dict[str, str]:
        """Get regulatory details based on selected region"""
        regulatory_frameworks = {
            "EU": {
                "regulations": "EU Green Claims Directive, CSRD, EU Taxonomy Regulation",
                "description": "European Union sustainability regulations focusing on green claims substantiation and corporate reporting",
                "key_authorities": "European Commission, National Consumer Authorities",
                "enforcement_focus": "Substantiation of environmental claims, mandatory sustainability reporting"
            },
            "USA": {
                "regulations": "FTC Green Guides, SEC Climate Disclosure Rules, EPA Green Power Partnership",
                "description": "US federal guidance and rules for environmental marketing claims and climate disclosures",
                "key_authorities": "FTC, SEC, EPA",
                "enforcement_focus": "Truthful advertising, material climate risk disclosure, renewable energy claims"
            },
            "UK": {
                "regulations": "CMA Green Claims Code, FCA Sustainability Disclosure Requirements, ASA CAP Code",
                "description": "UK-specific guidance for environmental claims and financial sustainability disclosures",
                "key_authorities": "CMA, FCA, ASA",
                "enforcement_focus": "Consumer protection, greenwashing prevention, financial product sustainability"
            },
            "Global": {
                "regulations": "ISO 14021, GRI Standards, TCFD Recommendations, ISSB Standards",
                "description": "International standards and frameworks for sustainability communication and reporting",
                "key_authorities": "ISO, GRI, TCFD, ISSB",
                "enforcement_focus": "Standardized reporting, voluntary compliance, best practice adoption"
            }
        }
        
        return regulatory_frameworks.get(region, regulatory_frameworks["Global"])
    
    def handle_chat_message(self, contents: str, user: str, instance):
        """Handle chat messages from user"""
        if not self.training_in_progress:
            # Provide helpful responses when not training
            if "start" in contents.lower() or "training" in contents.lower():
                return "Click the '🚀 Start Training Session' button to begin your personalized sustainability training!"
            elif "help" in contents.lower():
                return """**Available Actions:**
                
🚀 **Start Training** - Click the button to begin
🏢 **Select Industry** - Choose your industry focus
🌍 **Pick Regulations** - Select your regulatory framework (EU, USA, UK, Global)
📊 **Set Level** - Pick your difficulty level
❓ **Ask Questions** - I can help with sustainability messaging topics

**Regulatory Frameworks Available:**
- 🇪🇺 **EU**: Green Claims Directive, CSRD, EU Taxonomy
- 🇺🇸 **USA**: FTC Green Guides, SEC Climate Rules
- 🇬🇧 **UK**: CMA Green Claims Code, FCA Requirements  
- 🌍 **Global**: ISO 14021, GRI Standards, TCFD

**What you'll get:**
- Realistic business scenarios
- Problematic messaging examples  
- Best practice corrections
- Comprehensive messaging playbook
- Downloadable frameworks and checklists"""
            else:
                return "I'm here to help with sustainability training! Click 'Start Training Session' to begin, or ask me about sustainability messaging best practices."
        else:
            return "Training session in progress... Please wait for completion before asking questions."
    
    def start_training(self, event):
        """Start the training session"""
        if self.training_in_progress:
            self.chat_interface.send("⚠️ Training already in progress. Please wait for completion.", user="System", respond=False)
            return
        
        # Set up training session
        self.training_in_progress = True
        self.progress_bar.visible = True
        self.progress_bar.value = 0
        self.start_button.disabled = True
        self.start_button.name = "🔄 Training in Progress..."
        self.status_indicator.object = "**Status:** Training session starting... 🟡"
        
        # Send welcome message
        regulatory_details = self.get_regulatory_details(self.regulatory_select.value)
        
        session_info = {
            'session_id': f"TRAIN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'user_industry': self.industry_select.value,
            'regulatory_region': self.regulatory_select.value,
            'regional_regulations': regulatory_details['regulations'],
            'regulatory_description': regulatory_details['description'],
            'difficulty_level': self.difficulty_select.value
        }
        
        # Format regulatory region with flag emoji
        region_flags = {"EU": "🇪🇺", "USA": "🇺🇸", "UK": "🇬🇧", "Global": "🌍"}
        region_display = f"{region_flags.get(self.regulatory_select.value, '🌍')} {self.regulatory_select.value}"
        
        self.chat_interface.send(f"""🌱 **Sustainability Training Session Started**

**Session ID:** {session_info['session_id']}
**Industry Focus:** {session_info['user_industry']}
**Regulatory Framework:** {region_display}
**Key Regulations:** {regulatory_details['regulations']}
**Training Level:** {session_info['difficulty_level']}

**Regulatory Focus:**
{regulatory_details['description']}

**Training Plan:**
1. 🏢 Create realistic business scenario
2. ⚠️ Identify problematic messaging patterns  
3. ✅ Develop compliant alternatives
4. 📚 Generate practical messaging playbook

Please wait while our AI agents work together to create your personalized sustainability messaging playbook...""", user="System", respond=False)
        
        # Start the actual training asynchronously
        asyncio.create_task(self.run_training_async(session_info))
    
    async def run_training_async(self, session_info: Dict[str, Any]):
        """Run the training session asynchronously"""
        try:
            # Import crew
            from .crew import Sustainability
            from .callbacks import get_panel_callback_handler
            
            # Register chat interface with callback handler
            callback_handler = get_panel_callback_handler()
            callback_handler.register_chat_interface(self.chat_interface)
            callback_handler.on_session_start(session_info)
            
            # Update progress
            self.progress_bar.value = 10
            self.status_indicator.object = "**Status:** Initializing AI agents... 🟡"
            
            # Create and run crew
            crew = Sustainability().crew()
            
            inputs = {
                'user_industry': session_info['user_industry'],
                'regulatory_region': session_info['regulatory_region'],
                'regional_regulations': session_info['regional_regulations'],
                'regulatory_description': session_info['regulatory_description'],
                'current_year': str(datetime.now().year),
                'session_id': session_info['session_id']
            }
            
            self.progress_bar.value = 25
            self.status_indicator.object = "**Status:** AI agents working together... 🟡"
            
            self.chat_interface.send("🤖 **AI Agents Starting Work:**", user="System", respond=False)
            self.chat_interface.send("📋 Scenario Builder is researching your industry...", user="Scenario Builder", respond=False)
            
            # Run the training
            result = crew.kickoff(inputs=inputs)
            
            self.progress_bar.value = 100
            self.status_indicator.object = "**Status:** Training completed successfully! 🟢"
            
            # Store results
            self.latest_results = result
            
            # Enable download buttons
            self.download_md_button.disabled = False
            self.download_pdf_button.disabled = False
            
            # Send completion message via callback
            callback_handler.on_session_complete(result)
            
        except Exception as e:
            self.progress_bar.value = 0
            self.status_indicator.object = f"**Status:** Training failed ❌"
            self.chat_interface.send(f"❌ **Training Error:** {str(e)}\n\nPlease check your API keys and try again.", user="System", respond=False)
            
        finally:
            # Reset UI state
            self.training_in_progress = False
            self.start_button.disabled = False
            self.start_button.name = "🚀 Start Training Session"
            self.progress_bar.visible = False
    
    def download_markdown_playbook(self, event):
        """Download the messaging playbook as markdown - Web optimized"""
        if not self.latest_results:
            self.chat_interface.send("No playbook available for download.", user="System", respond=False)
            return
        
        try:
            # Get the structured data
            if hasattr(self.latest_results, 'tasks_output') and self.latest_results.tasks_output:
                final_task = self.latest_results.tasks_output[-1]
                if hasattr(final_task, 'pydantic') and final_task.pydantic:
                    data = final_task.pydantic.model_dump()
                    markdown_content = self.format_playbook_as_markdown(data)
                    
                    # Create download filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"sustainability_messaging_playbook_{timestamp}.md"
                    
                    if is_web_environment():
                        # Web-only download using JavaScript
                        import urllib.parse
                        
                        # Encode content safely for JavaScript
                        encoded_content = urllib.parse.quote(markdown_content)
                        
                        download_html = f"""
                        <div style="margin: 20px 0; padding: 20px; border: 2px solid #28a745; border-radius: 10px; background-color: #f8f9fa; text-align: center;">
                            <h3 style="color: #28a745; margin-bottom: 15px;">📚 Messaging Playbook Ready!</h3>
                            <p style="margin-bottom: 20px;">Click the button below to download your comprehensive sustainability messaging playbook.</p>
                            <button onclick="downloadPlaybook()" 
                                    style="background-color: #28a745; color: white; padding: 15px 30px; 
                                           border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold;
                                           box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: background-color 0.3s;">
                                📚 Download {filename}
                            </button>
                            <p style="margin-top: 15px; font-size: 14px; color: #666;">
                                File size: ~{len(markdown_content):,} characters | Format: Markdown (.md)
                            </p>
                        </div>
                        <script>
                        function downloadPlaybook() {{
                            try {{
                                const content = decodeURIComponent(`{encoded_content}`);
                                const blob = new Blob([content], {{ type: 'text/markdown;charset=utf-8' }});
                                const url = window.URL.createObjectURL(blob);
                                const link = document.createElement('a');
                                link.href = url;
                                link.download = '{filename}';
                                link.style.display = 'none';
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                                window.URL.revokeObjectURL(url);
                                
                                // Show success message
                                alert('✅ Download started! Check your Downloads folder for {filename}');
                            }} catch (error) {{
                                console.error('Download error:', error);
                                alert('❌ Download failed. Please try again or contact support.');
                            }}
                        }}
                        </script>
                        """
                        
                        download_widget = pn.pane.HTML(download_html, sizing_mode="stretch_width")
                        
                        self.chat_interface.send("📚 **Messaging Playbook Generated Successfully!**", user="System", respond=False)
                        self.chat_interface.send(download_widget, user="Download", respond=False)
                    else:
                        # Local development - save to outputs directory
                        if not os.path.exists('outputs'):
                            os.makedirs('outputs')
                        
                        filepath = f'outputs/{filename}'
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(markdown_content)
                        
                        self.chat_interface.send(f"📚 **Playbook Saved!** File saved to: `{filepath}`", user="System", respond=False)
                        
        except Exception as e:
            self.chat_interface.send(f"Error preparing playbook download: {str(e)}", user="System", respond=False)
    
    def download_pdf_instructions(self, event):
        """Download instructions for PDF conversion - Web optimized"""
        self.chat_interface.send(
            """📑 **PDF Conversion Instructions:**

**Step 1:** First download the Markdown playbook using the button above

**Step 2:** Convert to PDF using any of these methods:

🌐 **Online Conversion (Easiest):**
• Go to **pandoc.org/try**
• Upload your .md file  
• Select "PDF" as output format
• Download the converted PDF

💻 **Local Conversion:**
• Install Pandoc: `brew install pandoc` (Mac) or `apt install pandoc` (Linux)
• Run: `pandoc your_playbook.md -o messaging_playbook.pdf`

📝 **Alternative Tools:**
• **Typora** - Markdown editor with PDF export
• **Mark Text** - Free markdown editor  
• **VS Code** - With "Markdown PDF" extension

Your playbook contains professional formatting with frameworks, checklists, and case studies that will look great as a PDF! 🎯""", 
            user="PDF Help", 
            respond=False
        )
    
    def format_playbook_as_markdown(self, data: Dict[str, Any]) -> str:
        """Format the playbook data as a comprehensive markdown document"""
        
        # Extract main sections
        playbook_title = data.get('playbook_title', 'Sustainability Messaging Playbook')
        creation_date = data.get('creation_date', datetime.now().strftime('%Y-%m-%d'))
        target_audience = data.get('target_audience', 'Marketing Teams')
        
        markdown_content = f"""# {playbook_title}

**Created:** {creation_date}  
**Target Audience:** {target_audience}  
**Version:** 1.0

---

## Executive Summary

{data.get('executive_summary', 'Comprehensive guide for creating compliant sustainability messaging.')}

---

## 📋 Do's and Don'ts

{self.format_list_section(data.get('dos_and_donts', []))}

---

## 🚨 Common Greenwashing Patterns to Avoid

{self.format_list_section(data.get('greenwashing_patterns', []))}

---

## 🔄 Claim-to-Proof Framework

{self.format_framework_section(data.get('claim_to_proof_framework', {}))}

---

## ✅ Quick Compliance Checklist

{self.format_checklist_section(data.get('compliance_checklist', {}))}

---

## 📖 Case Study Examples

{self.format_case_studies_section(data.get('case_study_snapshots', []))}

---

## 📄 Regulatory References

{self.format_list_section(data.get('regulatory_references', []))}

---

## 🚀 Quick Start Implementation Guide

{self.format_list_section(data.get('quick_start_guide', []))}

---

## 👥 Team Training Tips

{self.format_list_section(data.get('team_training_tips', []))}

---

## 📚 Additional Resources

{self.format_list_section(data.get('additional_resources', []))}

---

## 📞 Contact Resources

{self.format_list_section(data.get('contact_resources', []))}

---

## 📖 Glossary

{self.format_list_section(data.get('glossary_terms', []))}

---

*Generated by Sustainability Training AI - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return markdown_content
    
    def format_list_section(self, items: list) -> str:
        """Format a list of items as markdown"""
        if not items:
            return "*No items available*"
        
        formatted_items = []
        for item in items:
            if isinstance(item, str):
                formatted_items.append(f"• {item}")
            else:
                formatted_items.append(f"• {str(item)}")
        
        return "\n".join(formatted_items)
    
    def format_framework_section(self, framework: dict) -> str:
        """Format the framework section"""
        if not framework:
            return "*Framework not available*"
        
        content = f"""### {framework.get('framework_name', 'Validation Framework')}

**Steps:**
{self.format_list_section(framework.get('steps', []))}

**Validation Questions:**
{self.format_list_section(framework.get('validation_questions', []))}

**Proof Requirements:**
{self.format_list_section(framework.get('proof_requirements', []))}

**Common Pitfalls:**
{self.format_list_section(framework.get('common_pitfalls', []))}
"""
        return content
    
    def format_checklist_section(self, checklist: dict) -> str:
        """Format the checklist section"""
        if not checklist:
            return "*Checklist not available*"
        
        content = f"""### {checklist.get('checklist_name', 'Compliance Checklist')}

**Categories to Check:**
{self.format_list_section(checklist.get('categories', []))}

**Validation Questions:**
{self.format_list_section(checklist.get('questions', []))}

**Red Flags to Watch For:**
{self.format_list_section(checklist.get('red_flags', []))}

**Approval Criteria:**
{self.format_list_section(checklist.get('approval_criteria', []))}
"""
        return content
    
    def format_case_studies_section(self, case_studies: list) -> str:
        """Format case studies section"""
        if not case_studies:
            return "*No case studies available*"
        
        content = ""
        for i, case in enumerate(case_studies, 1):
            content += f"""### Case Study {i}: {case.get('title', 'Untitled')}

**Company:** {case.get('company_name', 'Anonymous')}  
**Type:** {case.get('message_type', 'example').replace('_', ' ').title()}

**Original Message:**
> {case.get('original_message', 'Not provided')}

**Analysis:**
{case.get('analysis', 'No analysis provided')}

**Key Lesson:**
{case.get('key_lesson', 'No lesson provided')}

**Regulatory Context:**
{case.get('regulatory_context', 'No context provided')}

---

"""
        return content
    
    @property
    def layout(self):
        """Create the main layout"""
        
        # Sidebar with controls
        sidebar = pn.Column(
            "## ⚙️ Training Setup",
            self.industry_select,
            self.regulatory_select,
            self.difficulty_select,
            "---",
            self.start_button,
            "---", 
            "## 📚 Downloads",
            self.download_md_button,
            self.download_pdf_button,
            "---",
            self.status_indicator,
            self.progress_bar,
            width=350,
            height=800,
            scroll=True
        )
        
        # Main content area
        main_content = pn.Column(
            self.header,
            self.chat_interface,
            sizing_mode="stretch_both"
        )
        
        # Complete layout
        layout = pn.Row(
            sidebar,
            main_content,
            sizing_mode="stretch_width",
            height=800
        )
        
        return layout
    
    def servable(self):
        """Return the servable Panel application - Web optimized"""
        return self.layout

def create_sustainability_app():
    """Factory function to create the sustainability app"""
    return SustainabilityPanelApp()