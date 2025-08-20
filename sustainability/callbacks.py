from typing import Optional, Callable, Any, Dict
from crewai.tasks.task_output import TaskOutput
from datetime import datetime
import json

class PanelCallbackHandler:
    """Callback handler to bridge CrewAI outputs to Panel ChatInterface"""
    
    def __init__(self):
        self.chat_interface: Optional[Any] = None
        self.session_id: Optional[str] = None
        self.active_agent: Optional[str] = None
        self.task_count: int = 0
        self.completed_tasks: int = 0
        
    def register_chat_interface(self, chat_interface: Any):
        """Register the Panel ChatInterface to send messages to"""
        self.chat_interface = chat_interface
        
    def set_session_id(self, session_id: str):
        """Set the current training session ID"""
        self.session_id = session_id
        
    def send_message(self, message: str, user: str = "System", message_type: str = "info"):
        """Send a message to the Panel chat interface"""
        if self.chat_interface is None:
            print(f"[{user}] {message}")  # Fallback to console
            return
            
        # Format message with timestamp and type
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add emoji and formatting based on message type
        if message_type == "agent_start":
            formatted_message = f"🤖 **{user}** [{timestamp}]\n{message}"
        elif message_type == "agent_thinking":
            formatted_message = f"💭 **{user}** [{timestamp}]\n{message}"
        elif message_type == "tool_use":
            formatted_message = f"🛠️ **{user}** [{timestamp}]\n{message}"
        elif message_type == "task_complete":
            formatted_message = f"✅ **{user}** [{timestamp}]\n{message}"
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
            
        # Send to Panel chat
        try:
            self.chat_interface.send(formatted_message, user=user, respond=False)
        except Exception as e:
            print(f"Error sending to chat: {e}")
            print(f"[{user}] {message}")  # Fallback
    
    def on_agent_start(self, agent_name: str, task_description: str):
        """Called when an agent starts working on a task"""
        self.active_agent = agent_name
        self.task_count += 1
        
        # Format task description nicely
        clean_description = task_description[:200] + "..." if len(task_description) > 200 else task_description
        message = f"Starting work on: {clean_description}"
        self.send_message(message, user=agent_name, message_type="agent_start")
        
        # Send progress update
        progress_msg = f"Task {self.task_count} of 4: {agent_name} is working..."
        self.send_message(progress_msg, user="System", message_type="progress")
    
    def on_agent_thinking(self, agent_name: str, thought: str):
        """Called when an agent is thinking/reasoning"""
        # Only show brief thinking messages to avoid spam
        clean_thought = thought[:150] + "..." if len(thought) > 150 else thought
        message = f"Analyzing: {clean_thought}"
        self.send_message(message, user=agent_name, message_type="agent_thinking")
    
    def on_tool_use(self, agent_name: str, tool_name: str, tool_input: str, tool_output: str):
        """Called when an agent uses a tool"""
        if tool_name == "SerperDevTool":
            # Format search results nicely
            clean_input = tool_input[:100] + "..." if len(tool_input) > 100 else tool_input
            clean_output = tool_output[:300] + "..." if len(tool_output) > 300 else tool_output
            message = f"🔍 Searching for: {clean_input}\n📋 Found relevant information about sustainability regulations and best practices"
            self.send_message(message, user=agent_name, message_type="search")
        else:
            # Other tools
            clean_input = tool_input[:100] + "..." if len(tool_input) > 100 else tool_input
            clean_output = tool_output[:200] + "..." if len(tool_output) > 200 else tool_output
            message = f"Using {tool_name}\n🔍 Input: {clean_input}\n📋 Result: {clean_output}"
            self.send_message(message, user=agent_name, message_type="tool_use")
    
    def on_task_complete(self, agent_name: str, task_output: str):
        """Called when a task is completed"""
        self.completed_tasks += 1
        
        # Show brief completion message
        message = f"Task completed successfully! ✨\n📊 Progress: {self.completed_tasks}/4 tasks finished"
        self.send_message(message, user=agent_name, message_type="task_complete")
        
        # Show task summary based on agent
        if "scenario" in agent_name.lower():
            summary = "✅ Business scenario created with realistic context and regulatory requirements"
        elif "mistake" in agent_name.lower():
            summary = "✅ Problematic messaging examples identified with detailed compliance analysis"
        elif "practice" in agent_name.lower():
            summary = "✅ Best practice corrections provided with regulatory guidance"
        elif "playbook" in agent_name.lower():
            summary = "✅ Comprehensive sustainability messaging playbook generated with practical frameworks"
        else:
            summary = "✅ Analysis completed successfully"
            
        self.send_message(summary, user="System", message_type="info")
    
    def on_error(self, agent_name: str, error_message: str):
        """Called when an error occurs"""
        clean_error = error_message[:300] + "..." if len(error_message) > 300 else error_message
        message = f"⚠️ Issue encountered: {clean_error}"
        self.send_message(message, user=agent_name, message_type="error")
    
    def on_session_start(self, session_info: Dict[str, Any]):
        """Called when a training session starts"""
        self.session_id = session_info.get('session_id', 'Unknown')
        self.task_count = 0
        self.completed_tasks = 0
        
        message = f"""🌱 **Sustainability Training Session Started**

**Session ID:** {self.session_id}
**Industry Focus:** {session_info.get('user_industry', 'N/A')}
**Regulatory Framework:** {session_info.get('regional_regulations', 'N/A')}
**Difficulty Level:** {session_info.get('difficulty_level', 'N/A')}

**Training Plan:**
1. 🏢 Create realistic business scenario
2. ⚠️ Identify problematic messaging patterns  
3. ✅ Develop compliant alternatives
4. 📚 Generate practical messaging playbook

Please wait while our AI agents work together to create your personalized sustainability messaging playbook..."""
        
        self.send_message(message, user="System", message_type="session")
    
    def on_session_complete(self, results: Any):
        """Called when the entire training session is complete"""
        message = f"""🎉 **Training Session Completed Successfully!**

📊 **Session Summary:**
- ✅ All 4 training modules completed
- 📚 Comprehensive messaging playbook generated
- 🛠️ Practical frameworks and tools provided
- ✅ Real-world case studies included

**Your Playbook Includes:**
- 📋 Do's and Don'ts checklist
- 🚨 Greenwashing patterns to avoid
- 🔄 Claim-to-proof validation framework
- ✅ Quick compliance checklist
- 📖 Case study examples
- 📄 Regulatory references

**Next Steps:**
1. Review the detailed playbook above
2. Use the download buttons to save your playbook
3. Share with your marketing team
4. Implement the frameworks and checklists

Thank you for using our AI-powered sustainability training system! 🌱"""
        
        self.send_message(message, user="System", message_type="task_complete")

# Global instance that can be used across the application
panel_callback_handler = PanelCallbackHandler()

def print_task_output(task_output: TaskOutput) -> TaskOutput:
    """Callback function for CrewAI tasks - SIMPLIFIED VERSION FOR API"""
    # Just print to console for now - the main.py handles progress updates
    if task_output.agent:
        agent_name = task_output.agent
        print(f"✅ Task completed by {agent_name}")
    
    return task_output

def get_panel_callback_handler() -> PanelCallbackHandler:
    """Get the global callback handler instance"""
    return panel_callback_handler