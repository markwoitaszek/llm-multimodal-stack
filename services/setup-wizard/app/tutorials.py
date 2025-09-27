"""
Tutorial system for setup wizard
"""

import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TutorialCategory(str, Enum):
    """Tutorial categories"""
    GETTING_STARTED = "getting_started"
    BASIC_USAGE = "basic_usage"
    ADVANCED_FEATURES = "advanced_features"
    TROUBLESHOOTING = "troubleshooting"
    API_USAGE = "api_usage"


class TutorialStep(BaseModel):
    """Individual tutorial step"""
    id: str
    title: str
    description: str
    content: str
    code_examples: List[str] = []
    expected_outcome: str = ""
    tips: List[str] = []
    video_url: Optional[str] = None


class Tutorial(BaseModel):
    """Complete tutorial"""
    id: str
    title: str
    description: str
    category: TutorialCategory
    difficulty: str  # beginner, intermediate, advanced
    estimated_time_minutes: int
    prerequisites: List[str] = []
    steps: List[TutorialStep] = []
    completion_reward: str = ""


class TutorialManager:
    """Manage tutorials and progress"""
    
    def __init__(self):
        self.tutorials = self._initialize_tutorials()
        self.user_progress = {}  # In production, store in database
    
    def _initialize_tutorials(self) -> List[Tutorial]:
        """Initialize available tutorials"""
        return [
            self._create_getting_started_tutorial(),
            self._create_basic_chat_tutorial(),
            self._create_api_integration_tutorial(),
            self._create_multimodal_tutorial(),
            self._create_troubleshooting_tutorial()
        ]
    
    def _create_getting_started_tutorial(self) -> Tutorial:
        """Create getting started tutorial"""
        return Tutorial(
            id="getting_started",
            title="Getting Started with Your AI Stack",
            description="Learn the basics of your new Multimodal LLM Stack",
            category=TutorialCategory.GETTING_STARTED,
            difficulty="beginner",
            estimated_time_minutes=15,
            prerequisites=[],
            steps=[
                TutorialStep(
                    id="welcome",
                    title="Welcome to Your AI Stack",
                    description="Overview of what you've built",
                    content="""
                    <h3>🎉 Congratulations!</h3>
                    <p>You now have a complete AI stack running on your machine with:</p>
                    <ul>
                        <li>🤖 <strong>AI Chat Interface</strong> - Talk to your AI at <code>http://localhost:3030</code></li>
                        <li>🔌 <strong>API Endpoint</strong> - Use OpenAI-compatible API at <code>http://localhost:4000</code></li>
                        <li>📊 <strong>Monitoring</strong> - Check system health and performance</li>
                        <li>🔍 <strong>Vector Search</strong> - Intelligent search across your data</li>
                    </ul>
                    """,
                    tips=[
                        "Bookmark the web interface URL for easy access",
                        "Check the system status regularly using the health check scripts"
                    ]
                ),
                TutorialStep(
                    id="access_interface",
                    title="Access Your AI Interface",
                    description="Open and explore the web interface",
                    content="""
                    <h3>🌐 Access Your AI Interface</h3>
                    <p>Your AI chat interface is now running at:</p>
                    <div style="background: #f5f5f7; padding: 15px; border-radius: 8px; margin: 10px 0;">
                        <strong>http://localhost:3030</strong>
                    </div>
                    <p>Open this URL in your browser to start chatting with your AI!</p>
                    """,
                    code_examples=[
                        "# Open in browser\nopen http://localhost:3030"
                    ],
                    expected_outcome="You should see the OpenWebUI interface with a chat interface",
                    tips=[
                        "If the page doesn't load, wait a few minutes for all services to start",
                        "Check the health status if you encounter any issues"
                    ]
                ),
                TutorialStep(
                    id="first_chat",
                    title="Your First AI Conversation",
                    description="Have your first conversation with your AI",
                    content="""
                    <h3>💬 Your First AI Conversation</h3>
                    <p>Try these example prompts to get started:</p>
                    <ul>
                        <li><strong>"Hello! Can you introduce yourself?"</strong></li>
                        <li><strong>"Explain what machine learning is in simple terms"</strong></li>
                        <li><strong>"Help me write a Python function to calculate fibonacci numbers"</strong></li>
                        <li><strong>"What are the benefits of using vector databases?"</strong></li>
                    </ul>
                    """,
                    expected_outcome="You should receive intelligent, contextual responses from your AI",
                    tips=[
                        "Experiment with different types of questions",
                        "Try asking for code examples, explanations, or creative writing"
                    ]
                )
            ],
            completion_reward="🎯 You've successfully completed your first AI interaction!"
        )
    
    def _create_basic_chat_tutorial(self) -> Tutorial:
        """Create basic chat tutorial"""
        return Tutorial(
            id="basic_chat",
            title="Mastering AI Conversations",
            description="Learn how to have effective conversations with your AI",
            category=TutorialCategory.BASIC_USAGE,
            difficulty="beginner",
            estimated_time_minutes=20,
            prerequisites=["getting_started"],
            steps=[
                TutorialStep(
                    id="prompt_engineering",
                    title="Effective Prompt Engineering",
                    description="Learn how to write better prompts",
                    content="""
                    <h3>🎯 Prompt Engineering Basics</h3>
                    <p>Good prompts lead to better AI responses. Here are key principles:</p>
                    
                    <h4>1. Be Specific</h4>
                    <p><strong>Bad:</strong> "Write code"</p>
                    <p><strong>Good:</strong> "Write a Python function that sorts a list of numbers in ascending order"</p>
                    
                    <h4>2. Provide Context</h4>
                    <p><strong>Bad:</strong> "Fix this error"</p>
                    <p><strong>Good:</strong> "I'm getting a 'list index out of range' error in my Python code. Here's the code: [paste code]"</p>
                    
                    <h4>3. Set the Tone</h4>
                    <p><strong>Bad:</strong> "Explain quantum computing"</p>
                    <p><strong>Good:</strong> "Explain quantum computing like I'm a high school student"</p>
                    """,
                    tips=[
                        "Use examples to clarify what you want",
                        "Break complex requests into smaller parts",
                        "Specify the output format you need"
                    ]
                ),
                TutorialStep(
                    id="conversation_flow",
                    title="Managing Conversation Flow",
                    description="Keep conversations organized and productive",
                    content="""
                    <h3>🔄 Conversation Flow Management</h3>
                    <p>Your AI remembers the conversation context. Use this to your advantage:</p>
                    
                    <h4>Building on Previous Messages</h4>
                    <p>You can reference earlier parts of the conversation:</p>
                    <ul>
                        <li>"Can you modify the function we discussed earlier to handle edge cases?"</li>
                        <li>"Based on the explanation you gave, what would happen if..."</li>
                    </ul>
                    
                    <h4>Starting Fresh Topics</h4>
                    <p>When switching to a completely different topic, consider starting a new conversation</p>
                    
                    <h4>Using System Instructions</h4>
                    <p>You can set context for the entire conversation:</p>
                    <div style="background: #f5f5f7; padding: 10px; border-radius: 6px;">
                        "You are a helpful coding assistant. Always provide code examples and explain your reasoning."
                    </div>
                    """,
                    tips=[
                        "Use the conversation history to build on previous ideas",
                        "Start new conversations for completely different topics",
                        "Be clear about what you want to achieve"
                    ]
                )
            ],
            completion_reward="🧠 You're now a prompt engineering expert!"
        )
    
    def _create_api_integration_tutorial(self) -> Tutorial:
        """Create API integration tutorial"""
        return Tutorial(
            id="api_integration",
            title="API Integration Guide",
            description="Learn how to use the OpenAI-compatible API",
            category=TutorialCategory.API_USAGE,
            difficulty="intermediate",
            estimated_time_minutes=30,
            prerequisites=["getting_started"],
            steps=[
                TutorialStep(
                    id="api_basics",
                    title="API Basics",
                    description="Understanding the API endpoint",
                    content="""
                    <h3>🔌 API Endpoint Overview</h3>
                    <p>Your stack provides an OpenAI-compatible API at:</p>
                    <div style="background: #f5f5f7; padding: 15px; border-radius: 8px;">
                        <strong>Base URL:</strong> <code>http://localhost:4000/v1</code>
                    </div>
                    
                    <h4>Available Endpoints:</h4>
                    <ul>
                        <li><code>POST /v1/chat/completions</code> - Chat completions</li>
                        <li><code>GET /v1/models</code> - List available models</li>
                        <li><code>POST /v1/embeddings</code> - Generate embeddings</li>
                    </ul>
                    """,
                    tips=[
                        "The API is compatible with OpenAI's Python library",
                        "Use the same code patterns you'd use with OpenAI"
                    ]
                ),
                TutorialStep(
                    id="python_example",
                    title="Python Integration Example",
                    description="Basic Python integration",
                    content="""
                    <h3>🐍 Python Integration Example</h3>
                    <p>Here's how to use the API with Python:</p>
                    """,
                    code_examples=[
                        """import openai

# Configure for your local stack
openai.api_base = "http://localhost:4000/v1"
openai.api_key = "dummy-key"  # Not required for local use

# Chat completion
response = openai.ChatCompletion.create(
    model="microsoft/DialoGPT-medium",
    messages=[
        {"role": "user", "content": "Explain machine learning"}
    ],
    max_tokens=150,
    temperature=0.7
)

print(response.choices[0].message.content)"""
                    ],
                    expected_outcome="You should see an AI-generated explanation of machine learning",
                    tips=[
                        "Install the openai package: pip install openai",
                        "Adjust max_tokens and temperature based on your needs"
                    ]
                ),
                TutorialStep(
                    id="curl_example",
                    title="cURL Integration Example",
                    description="Using the API with cURL",
                    content="""
                    <h3>🌐 cURL Integration Example</h3>
                    <p>You can also use the API directly with cURL:</p>
                    """,
                    code_examples=[
                        """curl -X POST http://localhost:4000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer dummy-key" \\
  -d '{
    "model": "microsoft/DialoGPT-medium",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 100
  }'"""
                    ],
                    expected_outcome="You should receive a JSON response with the AI's reply",
                    tips=[
                        "Use tools like Postman or Insomnia for easier API testing",
                        "Check the response format to understand the structure"
                    ]
                )
            ],
            completion_reward="🚀 You can now integrate AI into your applications!"
        )
    
    def _create_multimodal_tutorial(self) -> Tutorial:
        """Create multimodal tutorial"""
        return Tutorial(
            id="multimodal_features",
            title="Multimodal AI Features",
            description="Learn about image and video processing capabilities",
            category=TutorialCategory.ADVANCED_FEATURES,
            difficulty="intermediate",
            estimated_time_minutes=25,
            prerequisites=["getting_started"],
            steps=[
                TutorialStep(
                    id="multimodal_overview",
                    title="Multimodal Capabilities Overview",
                    description="Understanding what your stack can do with images and videos",
                    content="""
                    <h3>🎨 Multimodal Capabilities</h3>
                    <p>Your stack includes advanced multimodal processing:</p>
                    
                    <h4>Image Processing:</h4>
                    <ul>
                        <li><strong>CLIP Embeddings</strong> - Generate semantic embeddings for images</li>
                        <li><strong>BLIP-2 Captioning</strong> - Automatic image captioning</li>
                        <li><strong>Visual Search</strong> - Find similar images using vector search</li>
                    </ul>
                    
                    <h4>Video Processing:</h4>
                    <ul>
                        <li><strong>Whisper Transcription</strong> - Extract text from audio/video</li>
                        <li><strong>Frame Analysis</strong> - Process video frames for insights</li>
                    </ul>
                    
                    <h4>Unified Search:</h4>
                    <p>Search across text, images, and videos with the Retrieval Proxy</p>
                    """,
                    tips=[
                        "These features are available through the API endpoints",
                        "Check the API documentation for detailed usage examples"
                    ]
                ),
                TutorialStep(
                    id="image_processing",
                    title="Image Processing Example",
                    description="Process and analyze images",
                    content="""
                    <h3>📸 Image Processing Example</h3>
                    <p>Here's how to process images with your stack:</p>
                    """,
                    code_examples=[
                        """import requests

# Process an image
with open('your_image.jpg', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8001/api/v1/process/image',
        files=files,
        data={'document_name': 'my_image.jpg'}
    )

result = response.json()
print(f"Caption: {result.get('caption', 'No caption')}")
print(f"Embedding shape: {len(result.get('embedding', []))}")"""
                    ],
                    expected_outcome="You should get a caption and embedding for your image",
                    tips=[
                        "Supported formats: JPG, PNG, GIF",
                        "Large images are automatically resized for processing"
                    ]
                )
            ],
            completion_reward="🎭 You can now work with multimodal AI features!"
        )
    
    def _create_troubleshooting_tutorial(self) -> Tutorial:
        """Create troubleshooting tutorial"""
        return Tutorial(
            id="troubleshooting",
            title="Troubleshooting Guide",
            description="Common issues and how to fix them",
            category=TutorialCategory.TROUBLESHOOTING,
            difficulty="beginner",
            estimated_time_minutes=20,
            prerequisites=[],
            steps=[
                TutorialStep(
                    id="health_checks",
                    title="Health Checks and Diagnostics",
                    description="Check if everything is working properly",
                    content="""
                    <h3>🔍 Health Checks</h3>
                    <p>Use these commands to check your stack health:</p>
                    """,
                    code_examples=[
                        "# Quick health check\n./scripts/health-check.sh\n\n# Comprehensive check\n./scripts/comprehensive-health-check.sh\n\n# Check specific service\ncurl http://localhost:4000/health"
                    ],
                    tips=[
                        "Run health checks after any configuration changes",
                        "Check logs if services are not responding"
                    ]
                ),
                TutorialStep(
                    id="common_issues",
                    title="Common Issues and Solutions",
                    description="Frequent problems and how to solve them",
                    content="""
                    <h3>🛠️ Common Issues</h3>
                    
                    <h4>Services Won't Start</h4>
                    <ul>
                        <li><strong>Port conflicts:</strong> Check if ports are already in use</li>
                        <li><strong>Memory issues:</strong> Ensure you have enough RAM</li>
                        <li><strong>Docker issues:</strong> Restart Docker daemon</li>
                    </ul>
                    
                    <h4>Slow Performance</h4>
                    <ul>
                        <li><strong>No GPU:</strong> Check NVIDIA Docker runtime</li>
                        <li><strong>Large models:</strong> Try smaller models first</li>
                        <li><strong>Storage:</strong> Use NVMe storage if available</li>
                    </ul>
                    
                    <h4>API Not Responding</h4>
                    <ul>
                        <li><strong>Wrong endpoint:</strong> Use http://localhost:4000/v1</li>
                        <li><strong>Authentication:</strong> Include Authorization header</li>
                        <li><strong>Model loading:</strong> Wait for model to load completely</li>
                    </ul>
                    """,
                    tips=[
                        "Check the logs for detailed error messages",
                        "Use the troubleshooting guide in the docs folder"
                    ]
                )
            ],
            completion_reward="🔧 You're now equipped to troubleshoot any issues!"
        )
    
    def get_tutorial(self, tutorial_id: str) -> Optional[Tutorial]:
        """Get tutorial by ID"""
        for tutorial in self.tutorials:
            if tutorial.id == tutorial_id:
                return tutorial
        return None
    
    def get_tutorials_by_category(self, category: TutorialCategory) -> List[Tutorial]:
        """Get tutorials by category"""
        return [t for t in self.tutorials if t.category == category]
    
    def get_beginner_tutorials(self) -> List[Tutorial]:
        """Get tutorials suitable for beginners"""
        return [t for t in self.tutorials if t.difficulty == "beginner"]
    
    def get_tutorial_progress(self, user_id: str, tutorial_id: str) -> Dict[str, Any]:
        """Get user's progress on a tutorial"""
        progress_key = f"{user_id}_{tutorial_id}"
        return self.user_progress.get(progress_key, {
            "completed_steps": [],
            "current_step": 0,
            "completed": False
        })
    
    def update_tutorial_progress(self, user_id: str, tutorial_id: str, step_id: str) -> bool:
        """Update tutorial progress"""
        progress_key = f"{user_id}_{tutorial_id}"
        
        if progress_key not in self.user_progress:
            self.user_progress[progress_key] = {
                "completed_steps": [],
                "current_step": 0,
                "completed": False
            }
        
        tutorial = self.get_tutorial(tutorial_id)
        if not tutorial:
            return False
        
        progress = self.user_progress[progress_key]
        
        if step_id not in progress["completed_steps"]:
            progress["completed_steps"].append(step_id)
        
        # Check if tutorial is completed
        if len(progress["completed_steps"]) >= len(tutorial.steps):
            progress["completed"] = True
        
        return True
