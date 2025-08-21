# 🌱 AI-Powered Sustainability Messaging Training

An intelligent training platform that generates comprehensive, compliance-focused sustainability messaging playbooks for businesses using multi-agent AI workflows.

## 🎯 What This Does

This application creates **customized sustainability messaging training content** for companies that need to communicate their environmental efforts while avoiding greenwashing and ensuring regulatory compliance.

### Key Features

- 🤖 **AI-Generated Business Scenarios** - Creates realistic company profiles and sustainability contexts
- 🚨 **Greenwashing Detection** - Identifies problematic messaging patterns with real-world examples  
- ✅ **Compliance Corrections** - Provides regulatory-compliant alternatives to risky messaging
- 🗺️ **Implementation Roadmaps** - Step-by-step deployment guides with success metrics
- 📚 **Comprehensive Playbooks** - Rich markdown training materials ready for team use
- 🌍 **Multi-Regional Support** - EU, USA, UK, and Global regulatory frameworks

## 🏗️ Architecture

Built using **CrewAI** multi-agent workflows with specialized AI agents:

- **Scenario Builder** - Creates realistic business contexts
- **Greenwashing Detector** - Identifies problematic messaging patterns  
- **Best Practice Coach** - Develops compliant alternatives
- **Implementation Planner** - Creates deployment roadmaps

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key (or compatible LLM service)
- Serper API key (for web research)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd sustainability-training
   ```

2. **Set up Python environment**
   ```bash
   pyenv local 3.11.9  # or your preferred Python 3.11+
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   uv sync
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # OPENAI_API_KEY=your_openai_key_here
   # SERPER_API_KEY=your_serper_key_here
   ```

5. **Start the server**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## 📊 Training Parameters

- **industry_focus**: Target industry (e.g., "Technology", "Agriculture", "Fashion")
- **regulatory_framework**: Compliance region ("EU", "USA", "UK", "Global") 
- **training_level**: Complexity ("Beginner", "Intermediate", "Advanced")

## 🗂️ Generated Content

Each training session produces:

### JSON Artifacts
- `scenario.json` - Detailed business scenario and context
- `problems.json` - Problematic messaging examples with analysis
- `corrections.json` - Compliant alternatives with explanations  
- `implementation.json` - Deployment roadmap and success metrics

### Comprehensive Playbook
- Executive summary and business context
- Detailed problematic message analysis
- Best practice corrections with regulatory guidance
- Before/after message transformations
- Implementation roadmap with timelines
- Success metrics and monitoring frameworks
- Quick reference tools and compliance checklists

## 🛠️ Development

### Project Structure
```
├── main.py                 # FastAPI server
├── sustainability/         # Core AI workflows
│   ├── crew.py            # CrewAI agent definitions
│   ├── config/            # Agent and task configurations
│   ├── artifact_writer.py # JSON artifact management
│   ├── markdown_builder.py # Playbook generation
│   └── validators.py      # Content validation
├── knowledge/             # Training data and preferences
├── outputs/               # Generated artifacts and playbooks
└── requirements.txt       # Dependencies
```
## 📚 Example Output

The system generates comprehensive training materials like this **Technology company playbook for EU compliance**:

- ✅ 5 marketing objectives analyzed for sustainability implications
- ✅ 4 preliminary claims reviewed for compliance risks  
- ✅ 4 problematic messages identified with detailed regulatory analysis
- ✅ 4 corrected alternatives provided with compliance guidance
- ✅ 6-step implementation roadmap with practical next actions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

**🌱 Built with sustainability and compliance in mind** • Powered by CrewAI and OpenAI

## 👩‍💻 About the Author

Hi, I’m **Cristina Rodriguez** — a full-stack software engineer and technical curriculum developer with over 20 years of experience in project management, communications, and content creation, and more than 3 years specializing in software engineering education.  

I build tools and learning experiences at the intersection of **technology and social impact**, focusing on making complex technical concepts accessible to beginners and empowering underrepresented groups in tech.  

Some of my recent work includes:
- Running **TechConMe**, a live workshop series teaching Next.js and modern web development
- Creating **AI-powered training tools** for sustainability and compliance
- Designing **technical curricula** for organizations like Techtonica and ELM Learning  

🌐 Learn more about my projects at [yosola.co](https://yosola.co)  
📫 Connect with me on [LinkedIn](https://www.linkedin.com/in/crissrodriguez)
