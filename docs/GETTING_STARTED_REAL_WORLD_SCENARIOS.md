# Getting Started: Real-World Scenarios with LLM Multimodal Stack

This guide provides practical, real-world scenarios to help you get started with the LLM Multimodal Stack. Each scenario demonstrates different capabilities and use cases.

## 🚀 **Quick Setup**

Before diving into scenarios, ensure you have the stack running:

```bash
# 1. Generate secrets and environment files
python3 setup_secrets.py

# 2. Start the development environment
./start-environment.sh dev

# 3. Verify all services are running
docker compose ps
```

## 📚 **Scenario 1: Erotic Fiction Writing Assistant**

Create an intelligent chatbot that helps writers craft compelling erotic fiction while maintaining appropriate boundaries and creative guidance.

### **What You'll Build**
- A specialized AI agent for creative writing assistance
- Content filtering and safety mechanisms
- Character development and plot progression tools
- Writing style analysis and improvement suggestions

### **Implementation Steps**

#### **Step 1: Create the Writing Agent**

```python
# Create a new agent for erotic fiction writing
from multimodal_llm_client import MultimodalLLMClient

client = MultimodalLLMClient()

# Create specialized writing agent
writing_agent = client.ai_agents.create_agent(
    name="Erotic Fiction Assistant",
    goal="Help writers create compelling erotic fiction with appropriate boundaries and creative guidance",
    tools=["web_search", "text_analysis", "character_development"],
    memory_window=20,
    user_id="writer_001"
)

print(f"Created agent: {writing_agent['agent_id']}")
```

#### **Step 2: Set Up Content Guidelines**

```python
# Define writing guidelines and safety parameters
guidelines = {
    "content_boundaries": {
        "explicit_content": "allowed_with_consent",
        "violence": "minimal_and_consensual",
        "age_restrictions": "18+_only"
    },
    "writing_principles": [
        "Character development over explicit scenes",
        "Emotional connection and tension building",
        "Consent and communication themes",
        "Literary quality and prose style"
    ],
    "safety_checks": [
        "Age verification",
        "Content warnings",
        "Consent themes validation"
    ]
}

# Store guidelines in the memory system
memory_result = client.ai_agents.execute_agent_task(
    agent_id=writing_agent['agent_id'],
    task=f"Store writing guidelines: {guidelines}"
)
```

#### **Step 3: Create Character Development Tool**

```python
# Process character development request
character_request = """
Create a character profile for a protagonist in an erotic romance novel:
- Name: Alex
- Background: Successful architect
- Personality: Confident but emotionally guarded
- Physical description: Tall, athletic build, striking eyes
- Character arc: Learning to trust and open up emotionally
"""

character_response = client.ai_agents.execute_agent_task(
    agent_id=writing_agent['agent_id'],
    task=f"Develop character profile: {character_request}"
)

print("Character Development:", character_response)
```

#### **Step 4: Writing Style Analysis**

```python
# Analyze writing style and provide feedback
sample_text = """
The moonlight filtered through the curtains, casting shadows across the room. 
Alex stood by the window, lost in thought about the day's events. 
The tension between them had been building for weeks, unspoken but palpable.
"""

style_analysis = client.multimodal_worker.process_text(
    text=sample_text,
    document_name="writing_sample_analysis",
    metadata={
        "analysis_type": "writing_style",
        "genre": "erotic_romance",
        "focus": "tension_building"
    }
)

print("Style Analysis:", style_analysis)
```

#### **Step 5: Create n8n Workflow for Content Review**

```json
{
  "name": "Erotic Fiction Content Review",
  "nodes": [
    {
      "name": "Content Input",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "fiction-review",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Content Analysis",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://multimodal-worker:8001/api/v1/process/text",
        "method": "POST",
        "body": {
          "text": "={{ $json.content }}",
          "metadata": {
            "analysis_type": "content_review",
            "genre": "erotic_fiction"
          }
        }
      }
    },
    {
      "name": "Safety Check",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "// Check content against safety guidelines\nconst content = $input.first().json;\nconst safetyScore = analyzeContentSafety(content);\nreturn { safety_score: safetyScore, approved: safetyScore > 0.8 };"
      }
    },
    {
      "name": "Send Feedback",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://ai-agents:8003/api/v1/agents/{{ $json.agent_id }}/execute",
        "method": "POST",
        "body": {
          "task": "Provide writing feedback and suggestions"
        }
      }
    }
  ]
}
```

### **Advanced Features**

#### **Real-time Collaboration**
```python
# Enable real-time collaboration for writing sessions
collaboration_session = client.ai_agents.execute_agent_task(
    agent_id=writing_agent['agent_id'],
    task="Start collaborative writing session with real-time feedback"
)
```

#### **Content Search and Reference**
```python
# Search for similar content and references
search_query = "romantic tension building techniques in literature"
search_results = client.retrieval_proxy.search(
    query=search_query,
    modalities=["text"],
    limit=10,
    filters={"genre": "romance", "technique": "tension"}
)
```

---

## 📸 **Scenario 2: Intelligent Photo Analysis Workflow**

Build an automated photo analysis system that reviews photo collections, rates photos, enhances the best ones, and integrates with PhotoPrism.

### **What You'll Build**
- Automated photo quality assessment
- AI-powered photo enhancement
- Intelligent categorization and tagging
- PhotoPrism integration for photo management

### **Implementation Steps**

#### **Step 1: Set Up Photo Analysis Agent**

```python
# Create photo analysis agent
photo_agent = client.ai_agents.create_agent(
    name="Photo Analysis Expert",
    goal="Analyze photo collections, rate quality, enhance best photos, and organize them intelligently",
    tools=["image_analysis", "photo_enhancement", "categorization"],
    memory_window=50,
    user_id="photographer_001"
)
```

#### **Step 2: Create Photo Analysis Function**

```python
def analyze_photo_collection(photo_paths):
    """Analyze a collection of photos"""
    results = []
    
    for photo_path in photo_paths:
        # Process each photo
        analysis = client.multimodal_worker.process_image(
            image_path=photo_path,
            document_name=f"photo_analysis_{photo_path.split('/')[-1]}",
            metadata={
                "analysis_type": "quality_assessment",
                "collection": "vacation_photos_2024"
            }
        )
        
        # Extract quality metrics
        quality_score = analysis.get('quality_score', 0)
        composition_score = analysis.get('composition_score', 0)
        lighting_score = analysis.get('lighting_score', 0)
        sharpness_score = analysis.get('sharpness_score', 0)
        
        # Calculate overall rating
        overall_rating = (quality_score + composition_score + lighting_score + sharpness_score) / 4
        
        results.append({
            'photo_path': photo_path,
            'overall_rating': overall_rating,
            'quality_score': quality_score,
            'composition_score': composition_score,
            'lighting_score': lighting_score,
            'sharpness_score': sharpness_score,
            'analysis': analysis
        })
    
    return results

# Analyze photo collection
photo_paths = [
    "/photos/vacation/sunset_beach.jpg",
    "/photos/vacation/family_portrait.jpg",
    "/photos/vacation/landscape_mountain.jpg"
]

photo_analysis_results = analyze_photo_collection(photo_paths)
```

#### **Step 3: Create n8n Photo Processing Workflow**

```json
{
  "name": "Photo Analysis and Enhancement Pipeline",
  "nodes": [
    {
      "name": "Photo Input",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "photo-upload",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Analyze Photo Quality",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://multimodal-worker:8001/api/v1/process/image",
        "method": "POST",
        "body": {
          "image_path": "={{ $json.photo_path }}",
          "metadata": {
            "analysis_type": "comprehensive_quality"
          }
        }
      }
    },
    {
      "name": "Rate Photo",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "// Rate photo based on analysis\nconst analysis = $input.first().json;\nconst rating = calculatePhotoRating(analysis);\nreturn { rating: rating, enhancement_needed: rating < 0.7 };"
      }
    },
    {
      "name": "Enhance Photo",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.enhancement_needed }}",
              "operation": "equal",
              "value2": "true"
            }
          ]
        }
      }
    },
    {
      "name": "Apply Enhancements",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://multimodal-worker:8001/api/v1/enhance/image",
        "method": "POST",
        "body": {
          "image_path": "={{ $json.photo_path }}",
          "enhancements": ["brightness", "contrast", "sharpness", "color_correction"]
        }
      }
    },
    {
      "name": "Generate Tags",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://ai-agents:8003/api/v1/agents/{{ $json.agent_id }}/execute",
        "method": "POST",
        "body": {
          "task": "Generate descriptive tags and categories for this photo"
        }
      }
    },
    {
      "name": "Upload to PhotoPrism",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://photoprism:2342/api/v1/photos",
        "method": "POST",
        "body": {
          "file": "={{ $json.enhanced_photo }}",
          "tags": "={{ $json.tags }}",
          "rating": "={{ $json.rating }}"
        }
      }
    }
  ]
}
```

#### **Step 4: Batch Photo Processing**

```python
def process_photo_batch(photo_directory):
    """Process a batch of photos"""
    import os
    
    photo_files = [f for f in os.listdir(photo_directory) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    for photo_file in photo_files:
        photo_path = os.path.join(photo_directory, photo_file)
        
        # Analyze photo
        analysis_task = client.ai_agents.execute_agent_task(
            agent_id=photo_agent['agent_id'],
            task=f"Analyze photo quality and suggest enhancements for: {photo_path}"
        )
        
        # Generate tags and categories
        tagging_task = client.ai_agents.execute_agent_task(
            agent_id=photo_agent['agent_id'],
            task=f"Generate descriptive tags and categories for: {photo_path}"
        )
        
        print(f"Processed {photo_file}: {analysis_task}, {tagging_task}")
```

#### **Step 5: PhotoPrism Integration**

```python
def upload_to_photoprism(photo_data, tags, rating):
    """Upload processed photo to PhotoPrism"""
    import requests
    
    photoprism_url = "http://localhost:2342/api/v1/photos"
    
    payload = {
        "file": photo_data,
        "tags": tags,
        "rating": rating,
        "quality": "high"
    }
    
    response = requests.post(photoprism_url, json=payload)
    return response.json()
```

---

## 📄 **Scenario 3: Personal Document Repository with AI Understanding**

Create an intelligent document repository that understands your personal universe of ideas, makes connections, and answers questions about your knowledge base.

### **What You'll Build**
- Intelligent document ingestion and processing
- Semantic search across your personal knowledge base
- AI-powered connection discovery between ideas
- Question-answering system for your documents

### **Implementation Steps**

#### **Step 1: Create Knowledge Management Agent**

```python
# Create knowledge management agent
knowledge_agent = client.ai_agents.create_agent(
    name="Personal Knowledge Assistant",
    goal="Understand, organize, and make connections within personal document collections",
    tools=["document_analysis", "semantic_search", "connection_discovery"],
    memory_window=100,
    user_id="knowledge_worker_001"
)
```

#### **Step 2: Document Ingestion System**

```python
def ingest_document(document_path, document_type="general"):
    """Ingest a document into the knowledge base"""
    
    # Process the document based on type
    if document_type == "pdf":
        # Extract text from PDF
        text_content = extract_pdf_text(document_path)
    elif document_type == "markdown":
        # Read markdown file
        with open(document_path, 'r') as f:
            text_content = f.read()
    else:
        # Process as text
        with open(document_path, 'r') as f:
            text_content = f.read()
    
    # Process with multimodal worker
    processing_result = client.multimodal_worker.process_text(
        text=text_content,
        document_name=document_path.split('/')[-1],
        metadata={
            "document_type": document_type,
            "ingestion_date": "2024-01-15",
            "source": "personal_knowledge_base"
        }
    )
    
    # Store in knowledge base
    knowledge_task = client.ai_agents.execute_agent_task(
        agent_id=knowledge_agent['agent_id'],
        task=f"Store and analyze document: {document_path}. Extract key concepts, themes, and connections."
    )
    
    return processing_result, knowledge_task

# Ingest sample documents
documents = [
    ("/docs/research/ai_ethics_paper.pdf", "pdf"),
    ("/docs/notes/meeting_notes_2024.md", "markdown"),
    ("/docs/ideas/startup_concepts.txt", "text")
]

for doc_path, doc_type in documents:
    result = ingest_document(doc_path, doc_type)
    print(f"Ingested {doc_path}: {result}")
```

#### **Step 3: Semantic Search System**

```python
def search_knowledge_base(query, search_type="semantic"):
    """Search the knowledge base semantically"""
    
    # Perform semantic search
    search_results = client.retrieval_proxy.search(
        query=query,
        modalities=["text"],
        limit=20,
        filters={"source": "personal_knowledge_base"},
        score_threshold=0.7
    )
    
    # Get context bundle for better understanding
    if search_results.get('results'):
        session_id = search_results['session_id']
        context_bundle = client.retrieval_proxy.get_context_bundle(
            session_id=session_id,
            format="markdown"
        )
        
        # Analyze connections
        connection_analysis = client.ai_agents.execute_agent_task(
            agent_id=knowledge_agent['agent_id'],
            task=f"Analyze connections between search results for query: {query}. Identify patterns and relationships."
        )
        
        return {
            'search_results': search_results,
            'context_bundle': context_bundle,
            'connections': connection_analysis
        }
    
    return search_results

# Example searches
queries = [
    "artificial intelligence ethics",
    "startup funding strategies",
    "machine learning applications"
]

for query in queries:
    results = search_knowledge_base(query)
    print(f"Search results for '{query}': {len(results.get('search_results', {}).get('results', []))} documents found")
```

#### **Step 4: Question Answering System**

```python
def answer_question(question, context_documents=None):
    """Answer questions about the knowledge base"""
    
    # Search for relevant documents
    search_results = search_knowledge_base(question)
    
    # Prepare context
    context = ""
    if context_documents:
        context = "\n".join(context_documents)
    elif search_results.get('context_bundle'):
        context = search_results['context_bundle'].get('content', '')
    
    # Generate answer using AI agent
    answer_task = client.ai_agents.execute_agent_task(
        agent_id=knowledge_agent['agent_id'],
        task=f"Answer this question based on the knowledge base: {question}. Context: {context[:2000]}"
    )
    
    return {
        'question': question,
        'answer': answer_task,
        'source_documents': search_results.get('search_results', {}).get('results', []),
        'confidence': search_results.get('search_results', {}).get('confidence', 0)
    }

# Example questions
questions = [
    "What are the main ethical concerns with AI development?",
    "How can I improve my startup's funding strategy?",
    "What connections exist between my research on AI and my business ideas?"
]

for question in questions:
    answer = answer_question(question)
    print(f"Q: {question}")
    print(f"A: {answer['answer']}")
    print(f"Sources: {len(answer['source_documents'])} documents")
    print("---")
```

#### **Step 5: Connection Discovery**

```python
def discover_connections(topic, depth=2):
    """Discover connections between ideas in the knowledge base"""
    
    # Search for the topic
    initial_search = search_knowledge_base(topic)
    
    # Find related concepts
    related_concepts = client.ai_agents.execute_agent_task(
        agent_id=knowledge_agent['agent_id'],
        task=f"Find related concepts and ideas connected to: {topic}. Look for patterns, themes, and relationships."
    )
    
    # Build connection map
    connection_map = {
        'central_topic': topic,
        'related_concepts': related_concepts,
        'connections': [],
        'insights': []
    }
    
    # Discover deeper connections
    for concept in related_concepts.get('concepts', []):
        concept_search = search_knowledge_base(concept)
        connection_map['connections'].append({
            'concept': concept,
            'relevance': concept_search.get('search_results', {}).get('confidence', 0),
            'documents': concept_search.get('search_results', {}).get('results', [])
        })
    
    # Generate insights
    insights = client.ai_agents.execute_agent_task(
        agent_id=knowledge_agent['agent_id'],
        task=f"Generate insights about the connections between: {topic} and related concepts. What patterns emerge?"
    )
    
    connection_map['insights'] = insights
    
    return connection_map

# Discover connections
connection_analysis = discover_connections("artificial intelligence")
print("Connection Analysis:", connection_analysis)
```

---

## 🎵 **Scenario 4: Emotional Analysis Environment Control**

Build a system that analyzes human emotions and automatically adjusts environment factors like mood lighting and background music.

### **What You'll Build**
- Real-time emotion detection from voice and facial expressions
- Environment control system for lighting and music
- Mood-based automation workflows
- Personalized environment preferences

### **Implementation Steps**

#### **Step 1: Create Emotion Analysis Agent**

```python
# Create emotion analysis agent
emotion_agent = client.ai_agents.create_agent(
    name="Emotion Environment Controller",
    goal="Analyze human emotions and automatically adjust environment factors like lighting and music",
    tools=["emotion_analysis", "environment_control", "music_selection"],
    memory_window=30,
    user_id="user_001"
)
```

#### **Step 2: Real-time Emotion Detection**

```python
def analyze_emotion_from_audio(audio_file_path):
    """Analyze emotions from audio input"""
    
    # Process audio for emotion analysis
    emotion_analysis = client.multimodal_worker.process_audio(
        audio_path=audio_file_path,
        document_name=f"emotion_analysis_{audio_file_path.split('/')[-1]}",
        metadata={
            "analysis_type": "emotion_detection",
            "modality": "audio",
            "real_time": True
        }
    )
    
    # Extract emotion data
    emotions = emotion_analysis.get('emotions', {})
    dominant_emotion = max(emotions.items(), key=lambda x: x[1]) if emotions else ('neutral', 0.5)
    
    return {
        'emotions': emotions,
        'dominant_emotion': dominant_emotion[0],
        'confidence': dominant_emotion[1],
        'analysis': emotion_analysis
    }

def analyze_emotion_from_video(video_file_path):
    """Analyze emotions from video input"""
    
    # Process video for emotion analysis
    emotion_analysis = client.multimodal_worker.process_video(
        video_path=video_file_path,
        document_name=f"emotion_analysis_{video_file_path.split('/')[-1]}",
        metadata={
            "analysis_type": "emotion_detection",
            "modality": "video",
            "real_time": True
        }
    )
    
    # Extract facial emotion data
    facial_emotions = emotion_analysis.get('facial_emotions', {})
    dominant_emotion = max(facial_emotions.items(), key=lambda x: x[1]) if facial_emotions else ('neutral', 0.5)
    
    return {
        'facial_emotions': facial_emotions,
        'dominant_emotion': dominant_emotion[0],
        'confidence': dominant_emotion[1],
        'analysis': emotion_analysis
    }
```

#### **Step 3: Environment Control System**

```python
class EnvironmentController:
    def __init__(self):
        self.lighting_systems = {
            'philips_hue': 'http://192.168.1.100/api',
            'lifx': 'http://192.168.1.101/api',
            'smart_things': 'http://192.168.1.102/api'
        }
        self.music_systems = {
            'spotify': 'http://localhost:8080/api',
            'sonos': 'http://192.168.1.200/api',
            'airplay': 'http://localhost:5000/api'
        }
    
    def adjust_lighting(self, emotion, intensity=0.7):
        """Adjust lighting based on emotion"""
        lighting_presets = {
            'happy': {'color': 'warm_white', 'brightness': 80, 'temperature': 3000},
            'sad': {'color': 'soft_blue', 'brightness': 40, 'temperature': 4000},
            'angry': {'color': 'red', 'brightness': 60, 'temperature': 2000},
            'calm': {'color': 'cool_white', 'brightness': 50, 'temperature': 5000},
            'excited': {'color': 'dynamic_colors', 'brightness': 90, 'temperature': 3500},
            'neutral': {'color': 'daylight', 'brightness': 70, 'temperature': 4000}
        }
        
        preset = lighting_presets.get(emotion, lighting_presets['neutral'])
        
        # Apply lighting changes
        for system, api_url in self.lighting_systems.items():
            self._set_lighting(system, api_url, preset, intensity)
    
    def _set_lighting(self, system, api_url, preset, intensity):
        """Set lighting for specific system"""
        import requests
        
        payload = {
            'color': preset['color'],
            'brightness': int(preset['brightness'] * intensity),
            'temperature': preset['temperature']
        }
        
        try:
            response = requests.post(f"{api_url}/lights/set", json=payload)
            return response.json()
        except Exception as e:
            print(f"Error setting lighting for {system}: {e}")
    
    def adjust_music(self, emotion, volume=0.6):
        """Adjust music based on emotion"""
        music_presets = {
            'happy': {'genre': 'upbeat', 'tempo': 'fast', 'mood': 'energetic'},
            'sad': {'genre': 'melancholic', 'tempo': 'slow', 'mood': 'soothing'},
            'angry': {'genre': 'aggressive', 'tempo': 'fast', 'mood': 'intense'},
            'calm': {'genre': 'ambient', 'tempo': 'slow', 'mood': 'peaceful'},
            'excited': {'genre': 'electronic', 'tempo': 'fast', 'mood': 'energetic'},
            'neutral': {'genre': 'instrumental', 'tempo': 'medium', 'mood': 'relaxed'}
        }
        
        preset = music_presets.get(emotion, music_presets['neutral'])
        
        # Apply music changes
        for system, api_url in self.music_systems.items():
            self._set_music(system, api_url, preset, volume)
    
    def _set_music(self, system, api_url, preset, volume):
        """Set music for specific system"""
        import requests
        
        payload = {
            'genre': preset['genre'],
            'tempo': preset['tempo'],
            'mood': preset['mood'],
            'volume': volume
        }
        
        try:
            response = requests.post(f"{api_url}/music/play", json=payload)
            return response.json()
        except Exception as e:
            print(f"Error setting music for {system}: {e}")

# Initialize environment controller
env_controller = EnvironmentController()
```

#### **Step 4: Create n8n Emotion Control Workflow**

```json
{
  "name": "Emotion-Based Environment Control",
  "nodes": [
    {
      "name": "Emotion Input",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "emotion-detection",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Analyze Emotion",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://multimodal-worker:8001/api/v1/process/audio",
        "method": "POST",
        "body": {
          "audio_path": "={{ $json.audio_path }}",
          "metadata": {
            "analysis_type": "emotion_detection"
          }
        }
      }
    },
    {
      "name": "Determine Environment Settings",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "// Determine environment settings based on emotion\nconst emotion = $input.first().json.emotions;\nconst dominantEmotion = Object.keys(emotion).reduce((a, b) => emotion[a] > emotion[b] ? a : b);\n\nconst environmentSettings = {\n  'happy': { lighting: 'warm', music: 'upbeat', intensity: 0.8 },\n  'sad': { lighting: 'soft', music: 'melancholic', intensity: 0.4 },\n  'angry': { lighting: 'red', music: 'aggressive', intensity: 0.6 },\n  'calm': { lighting: 'cool', music: 'ambient', intensity: 0.5 },\n  'excited': { lighting: 'dynamic', music: 'electronic', intensity: 0.9 }\n};\n\nreturn {\n  emotion: dominantEmotion,\n  settings: environmentSettings[dominantEmotion] || environmentSettings['calm']\n};"
      }
    },
    {
      "name": "Adjust Lighting",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://192.168.1.100/api/lights/set",
        "method": "POST",
        "body": {
          "color": "={{ $json.settings.lighting }}",
          "intensity": "={{ $json.settings.intensity }}"
        }
      }
    },
    {
      "name": "Adjust Music",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8080/api/music/play",
        "method": "POST",
        "body": {
          "genre": "={{ $json.settings.music }}",
          "volume": "={{ $json.settings.intensity }}"
        }
      }
    },
    {
      "name": "Log Environment Change",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://ai-agents:8003/api/v1/agents/{{ $json.agent_id }}/execute",
        "method": "POST",
        "body": {
          "task": "Log environment change based on emotion detection"
        }
      }
    }
  ]
}
```

#### **Step 5: Real-time Emotion Monitoring**

```python
def start_emotion_monitoring():
    """Start real-time emotion monitoring"""
    import time
    import cv2
    import numpy as np
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    while True:
        # Capture frame
        ret, frame = cap.read()
        if not ret:
            break
        
        # Save frame for analysis
        frame_path = "/tmp/current_frame.jpg"
        cv2.imwrite(frame_path, frame)
        
        # Analyze emotion from video
        emotion_result = analyze_emotion_from_video(frame_path)
        
        # Adjust environment based on emotion
        dominant_emotion = emotion_result['dominant_emotion']
        confidence = emotion_result['confidence']
        
        if confidence > 0.7:  # Only adjust if confident
            env_controller.adjust_lighting(dominant_emotion)
            env_controller.adjust_music(dominant_emotion)
            
            # Log emotion detection
            client.ai_agents.execute_agent_task(
                agent_id=emotion_agent['agent_id'],
                task=f"Detected emotion: {dominant_emotion} with confidence {confidence}. Adjusted environment accordingly."
            )
        
        # Display emotion on frame
        cv2.putText(frame, f"Emotion: {dominant_emotion} ({confidence:.2f})", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow('Emotion Detection', frame)
        
        # Break on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        time.sleep(1)  # Analyze every second
    
    cap.release()
    cv2.destroyAllWindows()

# Start monitoring
start_emotion_monitoring()
```

#### **Step 6: Personalized Environment Learning**

```python
def learn_user_preferences():
    """Learn user preferences for different emotions"""
    
    # Collect user feedback
    feedback_task = client.ai_agents.execute_agent_task(
        agent_id=emotion_agent['agent_id'],
        task="Learn user preferences for environment settings. Ask user to rate different lighting and music combinations for each emotion."
    )
    
    # Store preferences in memory system
    preferences = {
        'happy': {'lighting': 'warm_white', 'music': 'upbeat_pop', 'intensity': 0.8},
        'sad': {'lighting': 'soft_blue', 'music': 'melancholic_jazz', 'intensity': 0.4},
        'angry': {'lighting': 'red', 'music': 'aggressive_rock', 'intensity': 0.6},
        'calm': {'lighting': 'cool_white', 'music': 'ambient_nature', 'intensity': 0.5},
        'excited': {'lighting': 'dynamic_colors', 'music': 'electronic_dance', 'intensity': 0.9}
    }
    
    # Store in memory system
    memory_result = client.ai_agents.execute_agent_task(
        agent_id=emotion_agent['agent_id'],
        task=f"Store user environment preferences: {preferences}"
    )
    
    return preferences

# Learn preferences
user_preferences = learn_user_preferences()
print("Learned user preferences:", user_preferences)
```

---

## 🚀 **Advanced Integration Examples**

### **Cross-Scenario Integration**

```python
def create_unified_ai_assistant():
    """Create a unified AI assistant that combines all scenarios"""
    
    # Create master agent
    master_agent = client.ai_agents.create_agent(
        name="Unified AI Assistant",
        goal="Provide comprehensive AI assistance across writing, photo analysis, knowledge management, and environment control",
        tools=["writing_assistance", "photo_analysis", "knowledge_search", "emotion_control"],
        memory_window=200,
        user_id="master_user_001"
    )
    
    # Create workflow that connects all scenarios
    unified_workflow = {
        "name": "Unified AI Assistant Workflow",
        "description": "Connects all AI capabilities in a seamless experience",
        "triggers": [
            "voice_command",
            "text_input",
            "photo_upload",
            "document_upload",
            "emotion_detection"
        ],
        "capabilities": [
            "creative_writing_assistance",
            "photo_analysis_and_enhancement",
            "knowledge_base_search",
            "environment_control",
            "cross_scenario_insights"
        ]
    }
    
    return master_agent, unified_workflow

# Create unified assistant
master_agent, workflow = create_unified_ai_assistant()
print("Created unified AI assistant:", master_agent['agent_id'])
```

### **Real-time Collaboration**

```python
def enable_real_time_collaboration():
    """Enable real-time collaboration across all scenarios"""
    
    # Set up WebSocket connections for real-time updates
    collaboration_config = {
        "websocket_url": "ws://localhost:8000/ws/collaboration",
        "channels": [
            "writing_session",
            "photo_analysis",
            "knowledge_sharing",
            "environment_control"
        ],
        "features": [
            "live_editing",
            "real_time_feedback",
            "shared_workspace",
            "presence_indicators"
        ]
    }
    
    return collaboration_config

# Enable collaboration
collab_config = enable_real_time_collaboration()
print("Collaboration enabled:", collab_config)
```

---

## 📋 **Next Steps**

1. **Customize Scenarios**: Adapt these scenarios to your specific needs
2. **Extend Functionality**: Add more features and integrations
3. **Scale Up**: Deploy to production with proper security and monitoring
4. **Create New Scenarios**: Build your own unique AI-powered applications

## 🔧 **Troubleshooting**

### **Common Issues**

1. **Service Not Starting**: Check Docker logs with `docker compose logs [service_name]`
2. **API Connection Errors**: Verify service URLs and ports
3. **Memory Issues**: Increase Docker memory limits
4. **Permission Errors**: Check file permissions and Docker access

### **Getting Help**

- Check the [Troubleshooting Guide](./troubleshooting.md)
- Review [API Documentation](./api-reference.md)
- Join the [GitHub Discussions](https://github.com/markwoitaszek/llm-multimodal-stack/discussions)

---

**Happy Building! 🚀**

These scenarios demonstrate the powerful capabilities of the LLM Multimodal Stack. Start with one scenario, master it, then combine multiple scenarios to create sophisticated AI-powered applications.