#!/usr/bin/env python
import sys
import warnings
import os
import json
from datetime import datetime
from sustainability.crew import Sustainability

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

def save_simple_report(result, session_id):
    """Save a simple report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create outputs directory
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
    
    # Save as text file
    txt_file = f'outputs/training_report_{timestamp}.txt'
    with open(txt_file, 'w') as f:
        f.write(f"Sustainability Training Report\n")
        f.write(f"Session: {session_id}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*50 + "\n\n")
        f.write(str(result))
    
    # Try to save structured data if available
    try:
        if hasattr(result, 'tasks_output') and result.tasks_output:
            last_task = result.tasks_output[-1]
            if hasattr(last_task, 'pydantic') and last_task.pydantic:
                json_file = f'outputs/structured_data_{timestamp}.json'
                with open(json_file, 'w') as f:
                    json.dump(last_task.pydantic.dict(), f, indent=2)
                print(f"📊 Structured data saved: {json_file}")
    except Exception as e:
        print(f"⚠️ Could not save structured data: {e}")
    
    print(f"📄 Report saved: {txt_file}")
    return txt_file

def run():
    """Run the crew."""
    session_id = f"TRAIN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    inputs = {
        'user_industry': 'Marketing Agency',
        'regional_regulations': 'EU Green Claims Directive, CSRD',
        'current_year': str(datetime.now().year),
        'session_id': session_id
    }
    
    try:
        print("🌱 Starting Sustainability Training...")
        print(f"Session: {session_id}")
        
        result = Sustainability().crew().kickoff(inputs=inputs)
        
        print("✅ Training completed!")
        save_simple_report(result, session_id)
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise Exception(f"An error occurred while running the crew: {e}")

