"""
Markdown Builder - Build comprehensive playbooks exclusively from JSON artifacts
Reads validated artifacts and generates rich, detailed markdown playbooks
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from sustainability.artifact_writer import read_artifact, artifact_exists
from sustainability.validators import validate_all_artifacts, get_validation_summary


class MarkdownBuilderError(Exception):
    """Custom exception for markdown building failures"""
    pass


def build_playbook_from_artifacts(artifact_directory: str, 
                                 output_file: str, 
                                 training_request: Dict[str, Any], 
                                 session_id: str) -> bool:
    """
    Build comprehensive markdown playbook from validated artifacts
    
    Args:
        artifact_directory: Directory containing the artifacts
        output_file: Path to write the markdown file
        training_request: Original training request data
        session_id: Session identifier
        
    Returns:
        bool: True if successful
        
    Raises:
        MarkdownBuilderError: If building fails
    """
    try:
        print(f"🔨 Building markdown playbook from artifacts...")
        
        # Validate all artifacts exist and are valid
        validation_results = validate_all_artifacts(artifact_directory)
        
        if not validation_results["all_valid"]:
            error_msg = get_validation_summary(validation_results)
            raise MarkdownBuilderError(f"Artifact validation failed:\n{error_msg}")
        
        # Read all artifacts
        scenario_data = read_artifact(artifact_directory, 'scenario.json')
        problems_data = read_artifact(artifact_directory, 'problems.json')
        corrections_data = read_artifact(artifact_directory, 'corrections.json')
        implementation_data = read_artifact(artifact_directory, 'implementation.json')
        
        # Verify all artifacts loaded
        if not all([scenario_data, problems_data, corrections_data, implementation_data]):
            raise MarkdownBuilderError("Failed to load one or more artifact files")
        
        print(f"✅ All artifacts loaded successfully")
        print(f"   Scenario: {len(str(scenario_data)):,} chars")
        print(f"   Problems: {len(str(problems_data)):,} chars")
        print(f"   Corrections: {len(str(corrections_data)):,} chars")
        print(f"   Implementation: {len(str(implementation_data)):,} chars")
        
        # Build comprehensive markdown
        markdown_builder = ComprehensiveMarkdownBuilder(
            scenario_data=scenario_data,
            problems_data=problems_data,
            corrections_data=corrections_data,
            implementation_data=implementation_data,
            training_request=training_request,
            session_id=session_id
        )
        
        markdown_content = markdown_builder.build_complete_playbook()
        
        # Write markdown file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Verify file was created
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise MarkdownBuilderError("Failed to create markdown file")
        
        file_size = output_path.stat().st_size
        char_count = len(markdown_content)
        line_count = markdown_content.count('\n')
        
        print(f"✅ Comprehensive playbook created successfully:")
        print(f"   File: {output_file}")
        print(f"   Size: {file_size:,} bytes")
        print(f"   Content: {char_count:,} characters, {line_count:,} lines")
        
        return True
        
    except Exception as e:
        error_msg = f"Failed to build markdown playbook: {str(e)}"
        print(f"❌ {error_msg}")
        raise MarkdownBuilderError(error_msg)


class ComprehensiveMarkdownBuilder:
    """Builds rich, detailed markdown from validated artifacts"""
    
    def __init__(self, 
                 scenario_data: Dict[str, Any],
                 problems_data: Dict[str, Any], 
                 corrections_data: Dict[str, Any],
                 implementation_data: Dict[str, Any],
                 training_request: Dict[str, Any],
                 session_id: str):
        self.scenario = scenario_data
        self.problems = problems_data
        self.corrections = corrections_data
        self.implementation = implementation_data
        self.training_request = training_request
        self.session_id = session_id
        self.generation_time = datetime.now()
        
        # Extract key info for consistent reference
        self.company_name = scenario_data.get('company_name', 'Your Organization')
        self.industry = scenario_data.get('industry', 'Business')
        self.regulatory_framework = training_request.get('regulatory_framework', 'Global')
        
    def build_complete_playbook(self) -> str:
        """Build comprehensive markdown playbook"""
        sections = []
        
        # Header and metadata
        sections.append(self._build_header())
        
        # Table of contents
        sections.append(self._build_table_of_contents())
        
        # Executive summary
        sections.append(self._build_executive_summary())
        
        # Detailed business scenario
        sections.append(self._build_business_scenario())
        
        # Problematic messaging analysis
        sections.append(self._build_problematic_messaging_analysis())
        
        # Best practice corrections
        sections.append(self._build_corrections_analysis())
        
        # Before/after message comparisons
        sections.append(self._build_message_transformations())
        
        # Implementation roadmap
        sections.append(self._build_implementation_roadmap())
        
        # Success metrics and monitoring
        sections.append(self._build_success_metrics())
        
        # Regulatory compliance guide
        sections.append(self._build_regulatory_guide())
        
        # Quick reference tools
        sections.append(self._build_quick_reference())
        
        # Session metadata and quality info
        sections.append(self._build_session_info())
        
        return "\n\n".join(sections)
    
    def _build_header(self) -> str:
        """Build document header with company and regulatory context"""
        framework_flags = {"EU": "🇪🇺", "USA": "🇺🇸", "UK": "🇬🇧", "Global": "🌍"}
        flag = framework_flags.get(self.regulatory_framework, "🌍")
        
        return f"""# 🌱 Comprehensive Sustainability Messaging Playbook
## {self.company_name} - Strategic Communication Guide

**🏢 Company:** {self.company_name}  
**🏭 Industry:** {self.industry}  
**{flag} Regulatory Framework:** {self.regulatory_framework}  
**📊 Training Level:** {self.training_request.get('training_level', 'Intermediate')}  
**📅 Generated:** {self.generation_time.strftime('%Y-%m-%d %H:%M:%S')}  
**🆔 Session ID:** {self.session_id}  

---

> **🎯 AI-Powered Sustainability Communications Training**  
> This comprehensive playbook provides {self.company_name} with detailed, industry-specific guidance for creating compliant sustainability messaging that meets current {self.regulatory_framework} regulatory requirements while maintaining marketing effectiveness.

---"""

    def _build_table_of_contents(self) -> str:
        """Build dynamic table of contents"""
        return """## 📋 Table of Contents

1. [📊 Executive Summary](#-executive-summary)
2. [🏢 Business Scenario & Context](#-business-scenario--context)
3. [🚨 Problematic Messaging Analysis](#-problematic-messaging-analysis)
4. [✅ Best Practice Corrections](#-best-practice-corrections)
5. [🔄 Message Transformations](#-message-transformations)
6. [🚀 Implementation Roadmap](#-implementation-roadmap)
7. [📈 Success Metrics & Monitoring](#-success-metrics--monitoring)
8. [⚖️ Regulatory Compliance Guide](#-regulatory-compliance-guide)
9. [📚 Quick Reference Tools](#-quick-reference-tools)
10. [📋 Session Information](#-session-information)

---"""

    def _build_executive_summary(self) -> str:
        """Build comprehensive executive summary"""
        total_objectives = len(self.scenario.get('marketing_objectives', []))
        total_claims = len(self.scenario.get('preliminary_claims', []))
        problematic_count = len(self.problems.get('problematic_messages', []))
        correction_count = len(self.corrections.get('corrected_messages', []))
        roadmap_steps = len(self.implementation.get('implementation_roadmap', []))
        
        return f"""## 📊 Executive Summary

### 🎯 Training Overview for {self.company_name}

This comprehensive playbook addresses the sustainability messaging needs of **{self.company_name}**, a {self.scenario.get('company_size', 'sized')} organization in the {self.industry} sector, operating under {self.regulatory_framework} regulatory framework.

**Business Context:**
- **Location:** {self.scenario.get('location', 'Not specified')}
- **Target Market:** {self.scenario.get('target_audience', 'Not specified')}
- **Current Focus:** {self.scenario.get('sustainability_context', 'Not specified')[:200]}...

### 📋 Training Content Delivered

- ✅ **{total_objectives} Marketing Objectives** analyzed for sustainability implications
- ✅ **{total_claims} Preliminary Claims** reviewed for compliance risks
- ✅ **{problematic_count} Problematic Messages** identified with detailed regulatory analysis
- ✅ **{correction_count} Corrected Alternatives** provided with compliance guidance
- ✅ **{roadmap_steps}-Step Implementation Roadmap** with practical next actions

### 🎯 Key Outcomes & Benefits

1. **Risk Mitigation** - Identified specific greenwashing patterns that could impact {self.company_name}
2. **Compliance Assurance** - Provided {self.regulatory_framework}-specific guidance for all messaging
3. **Marketing Effectiveness** - Maintained promotional impact while ensuring regulatory compliance
4. **Team Readiness** - Delivered practical tools and frameworks for immediate implementation
5. **Competitive Advantage** - Positioned {self.company_name} as a leader in transparent sustainability communication

### ⚡ Immediate Action Items

1. **Review all {problematic_count} problematic message examples** to understand regulatory risks
2. **Implement the {correction_count} corrected message alternatives** in current marketing materials
3. **Deploy the validation frameworks** provided for ongoing message development
4. **Train marketing team** using the specific guidelines and tools included
5. **Establish monitoring processes** to ensure ongoing compliance and effectiveness

---"""

    def _build_business_scenario(self) -> str:
        """Build detailed business scenario section"""
        return f"""## 🏢 Business Scenario & Context
### {self.company_name} - Complete Business Profile

#### 🏪 Company Overview

**Organization Name:** {self.company_name}  
**Industry Sector:** {self.scenario.get('industry', 'Not specified')}  
**Company Size:** {self.scenario.get('company_size', 'Not specified')}  
**Geographic Location:** {self.scenario.get('location', 'Not specified')}  

#### 🎯 Products & Services

{self.scenario.get('product_service', 'Product and service information not available')}

#### 👥 Target Market Analysis

**Primary Audience Profile:**
{self.scenario.get('target_audience', 'Target audience profile not specified')}

#### 📈 Strategic Marketing Objectives

{self.company_name} has identified the following key marketing objectives:

{self._format_numbered_list(self.scenario.get('marketing_objectives', []))}

#### 🌱 Current Sustainability Context

**Sustainability Challenges & Opportunities:**
{self.scenario.get('sustainability_context', 'Sustainability context not provided')}

**Current Sustainability Practices:**
{self._format_bullet_list(self.scenario.get('current_practices', []))}

**Key Challenges Being Addressed:**
{self._format_bullet_list(self.scenario.get('challenges_faced', []))}

#### 📋 Preliminary Sustainability Claims Under Review

The following sustainability claims have been identified for regulatory compliance review:

{self._format_bullet_list(self.scenario.get('preliminary_claims', []), "⚠️")}

#### ⚖️ Regulatory Compliance Context

**{self.regulatory_framework} Regulatory Environment:**
{self.scenario.get('regulatory_context', 'Regulatory context not specified')}

#### 🏆 Competitive Landscape

**Market Positioning & Competition:**
{self.scenario.get('competitive_landscape', 'Competitive analysis not provided')}

#### 📚 Research Foundation

This scenario was developed using the following market research sources:
{self._format_bullet_list(self.scenario.get('market_research_sources', []), "🔗")}

---"""

    def _build_problematic_messaging_analysis(self) -> str:
        """Build comprehensive problematic messaging analysis"""
        content = f"""## 🚨 Problematic Messaging Analysis
### Critical Risk Assessment for {self.company_name}

#### 🌍 Current Regulatory Landscape

**{self.regulatory_framework} Regulatory Environment:**
{self.problems.get('regulatory_landscape', 'Regulatory landscape information not available')}

**Industry-Specific Insights for {self.industry}:**
{self.problems.get('industry_specific_insights', 'Industry insights not available')}

**Current Enforcement Trends:**
{self._format_bullet_list(self.problems.get('enforcement_trends', []), "⚡")}

#### 🔍 Identified Greenwashing Patterns

The following problematic patterns were identified in current market communications:
{self._format_bullet_list(self.problems.get('general_patterns_found', []), "🚫")}

### ⚠️ Detailed Message Risk Analysis

The following section analyzes specific problematic messaging examples relevant to {self.company_name}'s context:
"""
        
        # Add each problematic message with full analysis
        problematic_messages = self.problems.get('problematic_messages', [])
        
        for i, message in enumerate(problematic_messages, 1):
            message_id = message.get('id', f'msg{i}')
            content += f"""

#### ❌ Problematic Message #{i} (ID: {message_id})

**Problematic Statement:**
> "{message.get('message', 'Message not available')}"

**🔍 Problems Identified:**
{self._format_bullet_list(message.get('problems_identified', []), "🔸")}

**⚖️ Regulatory Violations:**
{self._format_bullet_list(message.get('regulatory_violations', []), "⚖️")}

**🚫 Greenwashing Patterns Demonstrated:**
{self._format_bullet_list(message.get('greenwashing_patterns', []), "🚫")}

**📰 Real-World Enforcement Examples:**
{self._format_bullet_list(message.get('real_world_examples', []), "📰")}

**📋 Detailed Risk Analysis:**
{message.get('why_problematic', 'Analysis not available')}

**⚠️ Potential Legal & Reputational Consequences:**
{self._format_bullet_list(message.get('potential_consequences', []), "⚠️")}

**🎯 Specific Risks for {self.company_name}:**
{message.get('context_specific_issues', 'Context-specific analysis not available')}

**💡 Initial Improvement Directions:**
{self._format_bullet_list(message.get('alternative_approaches', []), "💡")}"""
        
        content += f"""

#### 📚 Analysis Sources & References

This analysis was conducted using the following current sources:
{self._format_bullet_list(self.problems.get('research_sources', []), "🔗")}

---"""
        
        return content

    def _build_corrections_analysis(self) -> str:
        """Build comprehensive corrections analysis"""
        content = f"""## ✅ Best Practice Corrections
### Transforming Risk into Compliance for {self.company_name}

#### 🎯 Correction Methodology

This section provides specific, validated improvements to the problematic messages identified above, ensuring full compliance with {self.regulatory_framework} regulations while maintaining marketing effectiveness for {self.company_name}.

**General Compliance Guidelines:**
{self._format_bullet_list(self.corrections.get('general_guidelines', []), "✅")}

**Key Communication Principles:**
{self._format_bullet_list(self.corrections.get('key_principles', []), "🌟")}

**{self.regulatory_framework} Compliance Tips:**
{self._format_bullet_list(self.corrections.get('regulatory_compliance_tips', []), "⚖️")}

**Industry-Specific Advice for {self.industry}:**
{self.corrections.get('industry_specific_advice', 'Industry-specific guidance not provided')}

### 🔧 Detailed Message Corrections

The following corrections address each problematic message with specific improvements:
"""
        
        # Add each correction with full detail
        corrected_messages = self.corrections.get('corrected_messages', [])
        
        for i, correction in enumerate(corrected_messages, 1):
            original_id = correction.get('original_message_id', f'msg{i}')
            
            content += f"""

#### ✅ Correction #{i} (Original ID: {original_id})

**🔄 Improved Compliant Message:**
> "{correction.get('corrected_message', 'Corrected message not available')}"

**🛠️ Specific Changes Made:**
{self._format_bullet_list(correction.get('changes_made', []), "🔧")}

**⚖️ Compliance Assurance:**
{correction.get('compliance_notes', 'Compliance information not available')}

**⭐ Best Practices Applied:**
{self._format_bullet_list(correction.get('best_practices_applied', []), "⭐")}

**📈 Companies Successfully Using Similar Messaging:**
{self._format_bullet_list(correction.get('real_world_examples', []), "📈")}

**🎯 Why This Correction Works:**
{correction.get('effectiveness_rationale', 'Effectiveness explanation not available')}

**📊 Evidence Required to Support This Claim:**
{self._format_bullet_list(correction.get('evidence_required', []), "📋")}

**📊 Monitoring & Measurement Recommendations:**
{self._format_bullet_list(correction.get('monitoring_suggestions', []), "📊")}"""
        
        content += f"""

#### 📚 Best Practice Sources

These corrections are based on current industry best practices from:
{self._format_bullet_list(self.corrections.get('research_sources', []), "🔗")}

---"""
        
        return content

    def _build_message_transformations(self) -> str:
        """Build before/after message comparison section"""
        content = f"""## 🔄 Message Transformations
### Before & After: Complete Compliance Journey

This section demonstrates the complete transformation from problematic messaging to compliant alternatives, showing exactly how {self.company_name} can maintain marketing impact while ensuring regulatory compliance.

"""
        
        # Create message pairs
        problematic_messages = {msg.get('id'): msg for msg in self.problems.get('problematic_messages', [])}
        corrected_messages = {corr.get('original_message_id'): corr for corr in self.corrections.get('corrected_messages', [])}
        
        for msg_id in ['msg1', 'msg2', 'msg3', 'msg4']:
            if msg_id in problematic_messages and msg_id in corrected_messages:
                problem = problematic_messages[msg_id]
                correction = corrected_messages[msg_id]
                
                content += f"""### 🔄 Transformation #{msg_id.replace('msg', '')}

#### ❌ BEFORE: Problematic Version

**Original Message:**
> "{problem.get('message', 'Not available')}"

**Key Issues:**
{self._format_bullet_list(problem.get('problems_identified', [])[:3], "🔸")}

**Regulatory Risk Level:** 🔴 High Risk

#### ✅ AFTER: Compliant Version

**Improved Message:**
> "{correction.get('corrected_message', 'Not available')}"

**Key Improvements:**
{self._format_bullet_list(correction.get('changes_made', [])[:3], "✅")}

**Regulatory Risk Level:** 🟢 Compliant

**Evidence Needed:**
{self._format_bullet_list(correction.get('evidence_required', [])[:2], "📋")}

---

"""
        
        return content

    def _build_implementation_roadmap(self) -> str:
        """Build comprehensive implementation roadmap"""
        return f"""## 🚀 Implementation Roadmap
### Practical Deployment Guide for {self.company_name}

#### 🗺️ Step-by-Step Implementation Plan

{self._format_numbered_list(self.implementation.get('implementation_roadmap', []))}

#### 📅 Timeline & Milestones

**Implementation Schedule:**
{self._format_bullet_list(self.implementation.get('timeline_milestones', []), "📅")}

#### 👥 Team Training Requirements

**Staff Development Needs:**
{self._format_bullet_list(self.implementation.get('team_training_requirements', []), "👨‍🏫")}

#### 🛠️ Required Tools & Resources

**Implementation Tools:**
{self._format_bullet_list(self.implementation.get('tools_and_resources', []), "🔧")}

#### ⚠️ Risk Management

**Potential Risks & Mitigation Strategies:**
{self._format_bullet_list(self.implementation.get('risk_mitigation', []), "🛡️")}

#### 🏭 Industry-Specific Considerations

**Special Considerations for {self.industry}:**
{self.implementation.get('industry_specific_considerations', 'Industry considerations not provided')}

#### 💰 Budget & Resource Planning

**Financial Considerations:**
{self.implementation.get('budget_considerations', 'Budget information not provided')}

---"""

    def _build_success_metrics(self) -> str:
        """Build success metrics and monitoring section"""
        return f"""## 📈 Success Metrics & Monitoring
### Measuring Impact & Ensuring Ongoing Compliance

#### 📊 Key Performance Indicators

The following metrics will help {self.company_name} track the success of improved sustainability messaging:

{self._format_numbered_list(self.implementation.get('success_metrics', []))}

#### ⚖️ Compliance Monitoring Schedule

**Ongoing Compliance Activities:**
{self.implementation.get('regulatory_compliance_schedule', 'Compliance schedule not provided')}

#### 📋 Regular Review Process

**Recommended Review Frequency:**
- **Weekly:** Message approval and validation
- **Monthly:** Compliance audit and risk assessment  
- **Quarterly:** Full messaging strategy review
- **Annually:** Regulatory update and training refresh

#### 🎯 Success Indicators

**Signs of Effective Implementation:**
- ✅ Zero regulatory inquiries or penalties
- ✅ Increased consumer trust and engagement
- ✅ Positive stakeholder feedback on transparency
- ✅ Successful third-party audits
- ✅ Team confidence in messaging decisions

---"""

    def _build_regulatory_guide(self) -> str:
        """Build regulatory compliance reference guide"""
        framework_details = {
            "EU": {
                "key_regulations": "EU Green Claims Directive, CSRD, EU Taxonomy Regulation",
                "focus": "Substantiation requirements, corporate transparency, taxonomy alignment"
            },
            "USA": {
                "key_regulations": "FTC Green Guides, SEC Climate Disclosure Rules",
                "focus": "Truthful advertising standards, climate risk disclosure"
            },
            "UK": {
                "key_regulations": "CMA Green Claims Code, FCA Sustainability Requirements",
                "focus": "Consumer protection, financial product transparency"
            },
            "Global": {
                "key_regulations": "ISO 14021, GRI Standards, TCFD Recommendations",
                "focus": "International standards, voluntary best practices"
            }
        }
        
        details = framework_details.get(self.regulatory_framework, framework_details["Global"])
        
        return f"""## ⚖️ Regulatory Compliance Guide
### {self.regulatory_framework} Requirements for Sustainability Messaging

#### 📋 Key Regulations

**Primary Regulatory Framework:**
{details["key_regulations"]}

**Enforcement Focus:**
{details["focus"]}

#### ✅ Compliance Checklist

**Before Publishing Any Sustainability Message:**

1. **📊 Evidence Check**
   - [ ] All claims backed by verifiable data
   - [ ] Third-party certifications current and valid
   - [ ] Methodologies transparent and documented

2. **🔍 Language Review**
   - [ ] No vague or absolute terms without justification
   - [ ] Clear scope and context provided
   - [ ] Technical terms properly defined

3. **⚖️ Regulatory Alignment**
   - [ ] Complies with current {self.regulatory_framework} requirements
   - [ ] No misleading implications or omissions
   - [ ] Appropriate disclaimers included

4. **👥 Stakeholder Impact**
   - [ ] Message clear to target audience
   - [ ] No potential for consumer confusion
   - [ ] Aligns with company's actual practices

#### 🚨 Red Flags to Avoid

- **Absolute Claims:** "100% sustainable", "completely eco-friendly"
- **Vague Terms:** "Environmentally friendly", "natural", "green"
- **Future Promises:** Without clear interim milestones and accountability
- **Selective Disclosure:** Highlighting positives while hiding negatives
- **Unsubstantiated Comparisons:** "More sustainable than competitors"

#### 📞 When to Seek Help

**Escalate to Legal/Compliance if:**
- Uncertain about claim substantiation
- Competitor challenges your messaging
- Regulatory inquiry received
- New product category or claim type
- Significant marketing campaign launch

---"""

    def _build_quick_reference(self) -> str:
        """Build quick reference tools section"""
        return f"""## 📚 Quick Reference Tools
### Essential Resources for Daily Use

#### 🔄 Message Validation Framework

**Step 1: CLAIM** - What specific sustainability benefit are you claiming?
**Step 2: EVIDENCE** - What proof do you have to support this claim?
**Step 3: SCOPE** - What are the boundaries and limitations?
**Step 4: VERIFY** - Has this been independently validated?
**Step 5: COMMUNICATE** - Is the message clear and not misleading?

#### ⚡ 30-Second Compliance Check

1. **Can I prove this claim with data?** (Yes/No)
2. **Would a reasonable consumer understand the scope?** (Yes/No)  
3. **Does this comply with {self.regulatory_framework} rules?** (Yes/No)
4. **Have I avoided absolute terms without justification?** (Yes/No)

If any answer is "No" - **STOP** and revise the message.

#### 📝 Common Approved Language Patterns

**Instead of:** "100% sustainable"  
**Use:** "Certified sustainable by [specific certification]"

**Instead of:** "Eco-friendly packaging"  
**Use:** "Packaging made from 80% recycled materials, recyclable in municipal programs"

**Instead of:** "Carbon neutral"  
**Use:** "Carbon neutral for Scope 1 and 2 emissions, verified by [third party]"

**Instead of:** "Natural ingredients"  
**Use:** "Contains 95% naturally-derived ingredients as defined by [standard]"

#### 🆘 Emergency Contacts

**Internal Escalation:**
- Legal/Compliance Team
- Sustainability Officer  
- Marketing Director

**External Resources:**
- Regulatory consultant
- Sustainability certification bodies
- Industry associations

#### 📖 Recommended Reading

- {self.regulatory_framework} Green Claims Guidelines
- Industry-specific sustainability standards
- Competitor analysis reports
- Consumer research on sustainability messaging

---"""

    def _build_session_info(self) -> str:
        """Build session metadata and quality information"""
        return f"""## 📋 Session Information
### Training Session Details & Quality Metrics

#### 🎯 Session Summary

**Session ID:** {self.session_id}  
**Generation Date:** {self.generation_time.strftime('%Y-%m-%d %H:%M:%S')}  
**Company:** {self.company_name}  
**Industry:** {self.industry}  
**Regulatory Framework:** {self.regulatory_framework}  
**Training Level:** {self.training_request.get('training_level', 'Not specified')}

#### 📊 Content Quality Metrics

**Business Scenario:**
- ✅ Company profile: Complete
- ✅ Marketing objectives: {len(self.scenario.get('marketing_objectives', []))} identified  
- ✅ Sustainability context: Detailed analysis provided
- ✅ Regulatory environment: {self.regulatory_framework}-specific guidance

**Risk Analysis:**
- ✅ Problematic messages: {len(self.problems.get('problematic_messages', []))} analyzed
- ✅ Regulatory violations: Comprehensive coverage
- ✅ Real-world examples: Current market cases included
- ✅ Context-specific risks: {self.company_name}-focused analysis

**Solutions Provided:**
- ✅ Corrected messages: {len(self.corrections.get('corrected_messages', []))} alternatives provided
- ✅ Compliance validation: {self.regulatory_framework} requirements addressed
- ✅ Evidence requirements: Specific documentation identified
- ✅ Best practices: Current industry standards applied

**Implementation Support:**
- ✅ Roadmap steps: {len(self.implementation.get('implementation_roadmap', []))} actionable items
- ✅ Success metrics: {len(self.implementation.get('success_metrics', []))} KPIs defined
- ✅ Team training: Requirements and resources specified
- ✅ Risk mitigation: Strategies for common challenges

#### 🔧 Technical Details

**Data Sources:** AI-powered analysis of current regulations, market examples, and industry best practices  
**Validation Method:** Multi-layer compliance checking against {self.regulatory_framework} requirements  
**Content Type:** Company-specific guidance based on actual business context  
**Update Frequency:** Recommendations should be reviewed quarterly or when regulations change

#### 📞 Support & Updates

**For Questions About This Playbook:**
- Review the specific sections relevant to your immediate needs
- Use the Quick Reference Tools for daily messaging decisions
- Consult your legal/compliance team for regulatory interpretation

**For Updated Guidance:**
- Monitor {self.regulatory_framework} regulatory changes
- Subscribe to industry sustainability communications updates
- Consider annual training refreshers as regulations evolve

---

**🌱 Thank you for using AI-Powered Sustainability Training!**

*This playbook was generated specifically for {self.company_name} using advanced AI analysis of current regulations, market trends, and industry best practices. All content is tailored to your business context and regulatory environment.*

**Generated by:** Sustainability Training AI  
**Session:** {self.session_id}  
**Date:** {self.generation_time.strftime('%Y-%m-%d %H:%M:%S')}"""

    def _format_bullet_list(self, items: List[str], bullet: str = "•") -> str:
        """Format list items as bulleted markdown"""
        if not items:
            return "*No items available*"
        
        formatted_items = []
        for item in items:
            if isinstance(item, str) and item.strip():
                formatted_items.append(f"{bullet} {item}")
        
        return "\n".join(formatted_items) if formatted_items else "*No valid items available*"

    def _format_numbered_list(self, items: List[str]) -> str:
        """Format items as numbered markdown list"""
        if not items:
            return "*No items available*"
        
        formatted_items = []
        for i, item in enumerate(items, 1):
            if isinstance(item, str) and item.strip():
                formatted_items.append(f"{i}. {item}")
        
        return "\n".join(formatted_items) if formatted_items else "*No valid items available*"