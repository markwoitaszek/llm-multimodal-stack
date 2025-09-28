"""
Pre-built agent templates for common use cases
"""
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class AgentTemplate:
    """Agent template definition"""
    name: str
    description: str
    goal: str
    tools: List[str]
    memory_window: int
    category: str
    use_cases: List[str]

class AgentTemplates:
    """Collection of pre-built agent templates"""
    
    @staticmethod
    def get_all_templates() -> Dict[str, AgentTemplate]:
        """Get all available agent templates"""
        return {
            "research_assistant": AgentTemplate(
                name="Research Assistant",
                description="Autonomous research agent that can search, analyze, and synthesize information from multiple sources",
                goal="Help users research topics by searching through content, analyzing information, and providing comprehensive summaries",
                tools=["search_content", "generate_text", "web_search"],
                memory_window=15,
                category="research",
                use_cases=[
                    "Academic research",
                    "Market analysis", 
                    "Competitive intelligence",
                    "Fact checking",
                    "Content discovery"
                ]
            ),
            
            "content_analyzer": AgentTemplate(
                name="Content Analyzer",
                description="Multimodal content analysis agent that can process images, videos, and text to extract insights",
                goal="Analyze various types of content including images, videos, and text to extract meaningful insights and summaries",
                tools=["analyze_image", "search_content", "generate_text"],
                memory_window=10,
                category="analysis",
                use_cases=[
                    "Image analysis and captioning",
                    "Video content understanding",
                    "Document summarization",
                    "Media monitoring",
                    "Content moderation"
                ]
            ),
            
            "creative_writer": AgentTemplate(
                name="Creative Writer",
                description="AI writing assistant that can generate creative content, stories, and marketing copy",
                goal="Help users create engaging written content including stories, articles, marketing copy, and creative pieces",
                tools=["generate_text", "search_content"],
                memory_window=20,
                category="creative",
                use_cases=[
                    "Story writing",
                    "Marketing copy",
                    "Blog posts",
                    "Creative writing",
                    "Content ideation"
                ]
            ),
            
            "customer_service": AgentTemplate(
                name="Customer Service Agent",
                description="Intelligent customer service agent that can answer questions and resolve issues",
                goal="Provide helpful customer service by answering questions, resolving issues, and maintaining a friendly conversation",
                tools=["search_content", "generate_text"],
                memory_window=25,
                category="support",
                use_cases=[
                    "FAQ responses",
                    "Issue resolution",
                    "Product information",
                    "Order support",
                    "General inquiries"
                ]
            ),
            
            "data_researcher": AgentTemplate(
                name="Data Researcher",
                description="Specialized agent for finding and analyzing data across different sources",
                goal="Help users find, analyze, and interpret data from various sources to support decision-making",
                tools=["search_content", "generate_text", "web_search"],
                memory_window=12,
                category="data",
                use_cases=[
                    "Data discovery",
                    "Trend analysis",
                    "Statistical insights",
                    "Report generation",
                    "Data validation"
                ]
            ),
            
            "learning_tutor": AgentTemplate(
                name="Learning Tutor",
                description="Educational agent that can explain concepts, answer questions, and provide learning guidance",
                goal="Help users learn by explaining concepts, answering questions, and providing educational guidance",
                tools=["search_content", "generate_text"],
                memory_window=30,
                category="education",
                use_cases=[
                    "Concept explanation",
                    "Homework help",
                    "Study guidance",
                    "Skill development",
                    "Knowledge assessment"
                ]
            ),
            
            "project_manager": AgentTemplate(
                name="Project Manager",
                description="Project management assistant that can help plan, organize, and track project progress",
                goal="Assist with project management by helping plan tasks, track progress, and coordinate team activities",
                tools=["search_content", "generate_text"],
                memory_window=20,
                category="productivity",
                use_cases=[
                    "Task planning",
                    "Progress tracking",
                    "Resource coordination",
                    "Timeline management",
                    "Status reporting"
                ]
            )
        }
    
    @staticmethod
    def get_template_by_category(category: str) -> Dict[str, AgentTemplate]:
        """Get templates by category"""
        all_templates = AgentTemplates.get_all_templates()
        return {
            name: template 
            for name, template in all_templates.items() 
            if template.category == category
        }
    
    @staticmethod
    def get_template(template_name: str) -> AgentTemplate:
        """Get a specific template by name"""
        templates = AgentTemplates.get_all_templates()
        if template_name not in templates:
            raise ValueError(f"Template '{template_name}' not found")
        return templates[template_name]
    
    @staticmethod
    def get_categories() -> List[str]:
        """Get all available categories"""
        templates = AgentTemplates.get_all_templates()
        categories = set(template.category for template in templates.values())
        return sorted(list(categories))
    
    @staticmethod
    def search_templates(query: str) -> Dict[str, AgentTemplate]:
        """Search templates by name, description, or use cases"""
        query_lower = query.lower()
        templates = AgentTemplates.get_all_templates()
        
        results = {}
        for name, template in templates.items():
            # Search in name, description, goal, and use cases
            searchable_text = f"{template.name} {template.description} {template.goal} {' '.join(template.use_cases)}".lower()
            
            if query_lower in searchable_text:
                results[name] = template
        
        return results

# Convenience functions for easy access
def get_all_templates() -> Dict[str, AgentTemplate]:
    """Get all available agent templates"""
    return AgentTemplates.get_all_templates()

def get_template(template_name: str) -> AgentTemplate:
    """Get a specific template by name"""
    return AgentTemplates.get_template(template_name)

def get_templates_by_category(category: str) -> Dict[str, AgentTemplate]:
    """Get templates by category"""
    return AgentTemplates.get_template_by_category(category)

def search_templates(query: str) -> Dict[str, AgentTemplate]:
    """Search templates by query"""
    return AgentTemplates.search_templates(query)
