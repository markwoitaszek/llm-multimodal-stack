# Getting Started: Real-World Scenarios with LLM Multimodal Stack

This guide provides practical, real-world scenarios to help you get started with the LLM Multimodal Stack. Each scenario demonstrates different capabilities and use cases.

## 🎯 **GUI-First Approach**

This guide emphasizes **visual, user-friendly interfaces** over command-line tools. You'll primarily use:

- **🌐 Web Interfaces**: Access services through your browser
- **🎨 n8n Visual Workflows**: Drag-and-drop workflow builder
- **💬 Chat Interfaces**: Natural language interactions with AI agents
- **📊 Dashboards**: Visual monitoring and control panels
- **🔧 Configuration Panels**: Point-and-click setup tools

**No coding experience required!** All scenarios can be completed using web interfaces and visual tools.

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

## 🌐 **Service Access Points**

Once running, access these services through your web browser:

- **OpenWebUI**: http://localhost:3030 (Main chat interface)
- **AI Agents Dashboard**: http://localhost:8003 (Create and manage AI agents)
- **Multimodal Worker**: http://localhost:8001 (Upload and process files)
- **Search Engine**: http://localhost:8004 (Search your knowledge base)
- **n8n Workflows**: http://localhost:5678 (Visual workflow builder)
- **Environment Control**: http://localhost:8008 (Smart home control)
- **Analytics Dashboard**: http://localhost:8080 (Performance monitoring)
- **Kibana**: http://localhost:5601 (Log analysis)
- **Grafana**: http://localhost:3001 (Metrics visualization)

## 🔧 **First-Time Setup Guide**

### **Step 1: Verify All Services Are Running**

1. **Check Docker Status**:
   ```bash
   docker compose ps
   ```
   All services should show "Up" status. If any are down, wait a few minutes and check again.

2. **Test Service Connectivity**:
   ```bash
   # Test if services are responding
   curl -f http://localhost:3030/health || echo "OpenWebUI not ready"
   curl -f http://localhost:8003/health || echo "AI Agents not ready"
   curl -f http://localhost:8001/health || echo "Multimodal Worker not ready"
   ```

### **Step 2: Initial Service Configuration**

#### **Configure OpenWebUI (Main Chat Interface)**

1. **Open OpenWebUI**: http://localhost:3030
2. **Create Admin Account**:
   - Click "Sign Up" or "Create Account"
   - Enter your email and password
   - Complete the registration
3. **Configure Models**:
   - Go to Settings → Models
   - Add your preferred LLM models (GPT-4, Claude, etc.)
   - Test model connectivity

#### **Set Up AI Agents Dashboard**

1. **Open AI Agents Dashboard**: http://localhost:8003
2. **Initial Setup**:
   - Create your first user account
   - Configure agent templates
   - Set up tool integrations
3. **Test Agent Creation**:
   - Click "Create New Agent"
   - Use the "Basic Assistant" template
   - Test the agent with a simple question

#### **Configure Multimodal Worker**

1. **Open Multimodal Worker**: http://localhost:8001
2. **Initial Configuration**:
   - Set up storage directories
   - Configure processing models
   - Test file upload functionality
3. **Upload Test File**:
   - Upload a small image or text file
   - Verify processing completes successfully

#### **Set Up n8n Workflows**

1. **Open n8n**: http://localhost:5678
2. **Create Admin Account**:
   - Set up your admin credentials
   - Configure email settings (optional)
3. **Test Workflow Creation**:
   - Create a simple "Hello World" workflow
   - Test webhook functionality
   - Verify workflow execution

### **Step 3: Create Your First AI Agent**

1. **Go to AI Agents Dashboard**: http://localhost:8003
2. **Click "Create New Agent"**
3. **Fill in Basic Information**:
   - **Name**: "My First Assistant"
   - **Goal**: "Help me get started with the LLM Multimodal Stack"
   - **Tools**: Select "web_search" and "text_analysis"
   - **Memory Window**: 10 conversations
4. **Click "Create Agent"**
5. **Test Your Agent**:
   - Click "Start Chat"
   - Ask: "Hello! Can you help me understand what you can do?"
   - Verify the agent responds appropriately

### **Step 4: Set Up File Storage**

1. **Create Storage Directories**:
   ```bash
   mkdir -p ~/multimodal-stack-data/{documents,images,videos,audio}
   mkdir -p ~/multimodal-stack-data/processed/{documents,images,videos,audio}
   ```

2. **Configure Storage in Services**:
   - **Multimodal Worker**: Set upload directory to `~/multimodal-stack-data/`
   - **Search Engine**: Set index directory to `~/multimodal-stack-data/processed/`
   - **AI Agents**: Set memory storage to `~/multimodal-stack-data/agents/`

### **Step 5: Test End-to-End Workflow**

1. **Upload a Test Document**:
   - Go to Multimodal Worker: http://localhost:8001
   - Upload a small text file or image
   - Verify it processes successfully

2. **Search Your Content**:
   - Go to Search Engine: http://localhost:8004
   - Search for content from your uploaded file
   - Verify results appear

3. **Ask Questions About Your Content**:
   - Go to AI Agents Dashboard: http://localhost:8003
   - Select your agent
   - Ask questions about the content you uploaded
   - Verify the agent can access and discuss your content

### **Step 6: Configure Monitoring (Optional)**

1. **Set Up Grafana Dashboards**:
   - Open Grafana: http://localhost:3001
   - Login with admin/admin (change password)
   - Import default dashboards
   - Configure alerts

2. **Set Up Log Monitoring**:
   - Open Kibana: http://localhost:5601
   - Create index patterns
   - Set up log visualization

### **Step 7: Create Your First n8n Workflow**

1. **Open n8n**: http://localhost:5678
2. **Create Simple Workflow**:
   - Drag "Webhook" node
   - Drag "HTTP Request" node
   - Connect them
   - Configure webhook to receive data
   - Configure HTTP request to send data to AI Agents
3. **Test Workflow**:
   - Activate the workflow
   - Send test data to webhook
   - Verify data flows through to AI Agents

### **Troubleshooting Common Issues**

#### **Services Not Starting**
```bash
# Check logs
docker compose logs [service-name]

# Restart specific service
docker compose restart [service-name]

# Rebuild if needed
docker compose up --build [service-name]
```

#### **Port Conflicts**
```bash
# Check what's using ports
sudo netstat -tulpn | grep :3030
sudo netstat -tulpn | grep :8003

# Kill conflicting processes
sudo kill -9 [PID]
```

#### **Permission Issues**
```bash
# Fix file permissions
sudo chown -R $USER:$USER ~/multimodal-stack-data/
chmod -R 755 ~/multimodal-stack-data/
```

#### **Memory Issues**
```bash
# Check system resources
free -h
df -h

# Increase Docker memory if needed
# Edit docker-compose.yml and add:
# deploy:
#   resources:
#     limits:
#       memory: 4G
```

### **Verification Checklist**

Before proceeding to scenarios, verify:

- [ ] All Docker services are running (`docker compose ps`)
- [ ] OpenWebUI is accessible and you can create an account
- [ ] AI Agents Dashboard is accessible and you can create an agent
- [ ] Multimodal Worker can process files
- [ ] Search Engine can index and search content
- [ ] n8n is accessible and you can create workflows
- [ ] You can upload files and they process successfully
- [ ] You can search for uploaded content
- [ ] AI agents can answer questions about your content
- [ ] Basic n8n workflows execute successfully

**Once all items are checked, you're ready to start with the scenarios!**

## 📚 **Scenario 1: Erotic Fiction Writing Assistant**

Create an intelligent chatbot that helps writers craft compelling erotic fiction while maintaining appropriate boundaries and creative guidance.

### **What You'll Build**
- A specialized AI agent for creative writing assistance
- Content filtering and safety mechanisms
- Character development and plot progression tools
- Writing style analysis and improvement suggestions

### **Implementation Steps**

#### **Step 1: Access the Web Interface**

1. **Open OpenWebUI**: Navigate to http://localhost:3030
2. **Create New Chat**: Click "New Chat" and select "Custom Agent"
3. **Configure Agent**: Use the visual interface to set up your writing assistant

#### **Step 2: Set Up the Writing Agent via Web Interface**

1. **Go to AI Agents Dashboard**: http://localhost:8003
2. **Click "Create New Agent"**
3. **Fill in Agent Details**:
   - **Name**: "Erotic Fiction Assistant"
   - **Goal**: "Help writers create compelling erotic fiction with appropriate boundaries and creative guidance"
   - **Tools**: Select from available tools (web_search, text_analysis, character_development)
   - **Memory Window**: Set to 20 conversations
4. **Click "Create Agent"**

#### **Step 3: Configure Content Guidelines via Web Interface**

1. **In the Agent Dashboard**, click on your newly created agent
2. **Go to "Settings" tab**
3. **Add System Prompt**:
```
You are a specialized writing assistant for erotic fiction. Your role is to help writers create compelling stories while maintaining appropriate boundaries and creative guidance.

Guidelines:
- Focus on character development over explicit scenes
- Emphasize emotional connection and tension building
- Include consent and communication themes
- Maintain literary quality and prose style
- Always include appropriate content warnings
- Verify age restrictions (18+ only)
```

#### **Step 4: Test the Agent via Chat Interface**

1. **Open the agent chat interface**
2. **Start a conversation**:
   - "Help me develop a character for an erotic romance novel"
   - "Analyze this writing sample for style and improvement suggestions"
   - "Create a plot outline for a story about emotional healing through intimacy"

#### **Step 5: Create n8n Workflow for Content Review**

1. **Open n8n Workflow Builder**: Navigate to http://localhost:5678
2. **Login**: Use the credentials you set up (admin/[your-password])
3. **Create New Workflow**: Click "New Workflow"

**Build the Content Review Workflow:**

1. **Add Webhook Trigger**:
   - Drag "Webhook" node from the left panel
   - Set HTTP Method to "POST"
   - Set Path to "fiction-review"
   - Copy the webhook URL for later use

2. **Add Content Analysis Node**:
   - Drag "HTTP Request" node
   - Set URL to: `http://multimodal-worker:8001/api/v1/process/text`
   - Set Method to "POST"
   - In Body, add:
     ```json
     {
       "text": "={{ $json.content }}",
       "metadata": {
         "analysis_type": "content_review",
         "genre": "erotic_fiction"
       }
     }
     ```

3. **Add Safety Check Node**:
   - Drag "Function" node
   - Add this code:
     ```javascript
     // Check content against safety guidelines
     const content = $input.first().json;
     const safetyScore = analyzeContentSafety(content);
     return { 
       safety_score: safetyScore, 
       approved: safetyScore > 0.8 
     };
     ```

4. **Add Feedback Node**:
   - Drag another "HTTP Request" node
   - Set URL to: `http://ai-agents:8003/api/v1/agents/[your-agent-id]/execute`
   - Set Method to "POST"
   - In Body, add:
     ```json
     {
       "task": "Provide writing feedback and suggestions"
     }
     ```

5. **Connect the Nodes**: Drag connections between nodes in sequence
6. **Save and Activate**: Click "Save" then "Activate"

#### **Step 6: Test the Workflow**

1. **Use the webhook URL** from step 1 to send test content
2. **Monitor execution** in the n8n interface
3. **Check results** in the AI Agents dashboard

### **Advanced Features**

#### **Real-time Collaboration via Web Interface**

1. **Open the AI Agents Dashboard**: http://localhost:8003
2. **Select your Writing Agent**
3. **Click "Collaboration Mode"**
4. **Invite collaborators** by sharing the collaboration link
5. **Enable real-time editing** and feedback features

#### **Content Search and Reference via Search Interface**

1. **Open the Search Engine**: http://localhost:8004
2. **Enter search query**: "romantic tension building techniques in literature"
3. **Set filters**:
   - Genre: Romance
   - Technique: Tension
   - Limit: 10 results
4. **Browse results** and click to view full content
5. **Save relevant references** to your agent's memory

---

## 📸 **Scenario 2: Intelligent Photo Analysis Workflow**

Build an automated photo analysis system that reviews photo collections, rates photos, enhances the best ones, and integrates with PhotoPrism.

### **What You'll Build**
- Automated photo quality assessment
- AI-powered photo enhancement
- Intelligent categorization and tagging
- PhotoPrism integration for photo management

### **Implementation Steps**

#### **Step 1: Set Up Photo Analysis Agent via Web Interface**

1. **Open AI Agents Dashboard**: http://localhost:8003
2. **Click "Create New Agent"**
3. **Configure Agent**:
   - **Name**: "Photo Analysis Expert"
   - **Goal**: "Analyze photo collections, rate quality, enhance best photos, and organize them intelligently"
   - **Tools**: Select image_analysis, photo_enhancement, categorization
   - **Memory Window**: 50 conversations
4. **Click "Create Agent"**

#### **Step 2: Upload Photos via Web Interface**

1. **Open Multimodal Worker Interface**: http://localhost:8001
2. **Click "Upload Images"**
3. **Select multiple photos** from your collection
4. **Set Analysis Type**: Choose "Quality Assessment"
5. **Add Metadata**:
   - Collection: "vacation_photos_2024"
   - Analysis Type: "comprehensive_quality"
6. **Click "Process Images"**

#### **Step 3: Review Analysis Results**

1. **View Results Dashboard**: The interface will show:
   - Overall rating for each photo
   - Quality score breakdown (composition, lighting, sharpness)
   - Enhancement suggestions
   - Automatic categorization tags

2. **Select Photos for Enhancement**:
   - Check photos with ratings above 7/10
   - Click "Enhance Selected Photos"
   - Choose enhancement options (brightness, contrast, sharpness, color correction)

#### **Step 4: Create n8n Photo Processing Workflow**

1. **Open n8n Workflow Builder**: http://localhost:5678
2. **Create New Workflow**: Click "New Workflow"

**Build the Photo Processing Pipeline:**

1. **Add Webhook Trigger**:
   - Drag "Webhook" node
   - Set Path to "photo-upload"
   - Set HTTP Method to "POST"
   - Copy the webhook URL

2. **Add Photo Analysis Node**:
   - Drag "HTTP Request" node
   - Set URL to: `http://multimodal-worker:8001/api/v1/process/image`
   - Set Method to "POST"
   - In Body, add:
     ```json
     {
       "image_path": "={{ $json.photo_path }}",
       "metadata": {
         "analysis_type": "comprehensive_quality"
       }
     }
     ```

3. **Add Rating Logic**:
   - Drag "Function" node
   - Add this code:
     ```javascript
     const analysis = $input.first().json;
     const rating = (analysis.quality_score + analysis.composition_score + analysis.lighting_score + analysis.sharpness_score) / 4;
     return { 
       rating: rating, 
       enhancement_needed: rating < 0.7 
     };
     ```

4. **Add Conditional Enhancement**:
   - Drag "IF" node
   - Set condition: `enhancement_needed = true`
   - Connect to enhancement branch

5. **Add Enhancement Node**:
   - Drag "HTTP Request" node
   - Set URL to: `http://multimodal-worker:8001/api/v1/enhance/image`
   - Set Method to "POST"
   - In Body, add:
     ```json
     {
       "image_path": "={{ $json.photo_path }}",
       "enhancements": ["brightness", "contrast", "sharpness", "color_correction"]
     }
     ```

6. **Add Tag Generation**:
   - Drag "HTTP Request" node
   - Set URL to: `http://ai-agents:8003/api/v1/agents/[your-agent-id]/execute`
   - Set Method to "POST"
   - In Body, add:
     ```json
     {
       "task": "Generate descriptive tags and categories for this photo"
     }
     ```

7. **Add PhotoPrism Upload**:
   - Drag "HTTP Request" node
   - Set URL to: `http://photoprism:2342/api/v1/photos`
   - Set Method to "POST"
   - In Body, add:
     ```json
     {
       "file": "={{ $json.enhanced_photo }}",
       "tags": "={{ $json.tags }}",
       "rating": "={{ $json.rating }}"
     }
     ```

8. **Connect All Nodes** and **Save/Activate** the workflow

#### **Step 5: Batch Photo Processing via Web Interface**

1. **Open Multimodal Worker**: http://localhost:8001
2. **Click "Batch Processing"**
3. **Upload Photo Folder**:
   - Select entire folder of photos
   - Choose processing options (quality analysis, enhancement, tagging)
   - Set batch size (recommend 10-20 photos at a time)
4. **Monitor Progress**: Watch the real-time processing dashboard
5. **Review Results**: Check the batch processing results page

#### **Step 6: PhotoPrism Integration**

1. **Open PhotoPrism**: http://localhost:2342
2. **Configure Import Settings**:
   - Set import folder to your processed photos directory
   - Enable automatic tagging
   - Set quality thresholds
3. **Start Import Process**:
   - Click "Import Photos"
   - Monitor import progress
   - Review imported photos with AI-generated tags

---

## 📄 **Scenario 3: Personal Document Repository with AI Understanding**

Create an intelligent document repository that understands your personal universe of ideas, makes connections, and answers questions about your knowledge base.

### **What You'll Build**
- Intelligent document ingestion and processing
- Semantic search across your personal knowledge base
- AI-powered connection discovery between ideas
- Question-answering system for your documents

### **Implementation Steps**

#### **Step 1: Create Knowledge Management Agent via Web Interface**

1. **Open AI Agents Dashboard**: http://localhost:8003
2. **Click "Create New Agent"**
3. **Configure Agent**:
   - **Name**: "Personal Knowledge Assistant"
   - **Goal**: "Understand, organize, and make connections within personal document collections"
   - **Tools**: Select document_analysis, semantic_search, connection_discovery
   - **Memory Window**: 100 conversations
4. **Click "Create Agent"**

#### **Step 2: Document Ingestion via Web Interface**

1. **Open Multimodal Worker**: http://localhost:8001
2. **Click "Upload Documents"**
3. **Select Document Types**:
   - PDF files
   - Markdown files (.md)
   - Text files (.txt)
   - Word documents (.docx)
4. **Upload Documents**:
   - Drag and drop files or click "Browse"
   - Set document metadata (title, category, tags)
   - Choose processing options (extract text, analyze content, generate summary)
5. **Start Processing**: Click "Process Documents"
6. **Monitor Progress**: Watch the real-time processing dashboard

#### **Step 3: Semantic Search via Web Interface**

1. **Open Search Engine**: http://localhost:8004
2. **Enter Search Query**:
   - Type your search terms in the search box
   - Use natural language queries like "artificial intelligence ethics"
3. **Set Search Filters**:
   - Document type (PDF, Markdown, Text)
   - Date range
   - Source (personal_knowledge_base)
   - Score threshold (0.7 recommended)
4. **View Search Results**:
   - Browse ranked results with relevance scores
   - Click on documents to view full content
   - See highlighted matching sections
5. **Explore Connections**:
   - Click "Show Connections" to see related documents
   - View concept maps and relationship diagrams

#### **Step 4: Question Answering via Chat Interface**

1. **Open AI Agents Dashboard**: http://localhost:8003
2. **Select your Knowledge Assistant**
3. **Start Chat Session**:
   - Click "Start Chat"
   - Ask questions about your documents
4. **Example Questions to Try**:
   - "What are the main ethical concerns with AI development?"
   - "How can I improve my startup's funding strategy?"
   - "What connections exist between my research on AI and my business ideas?"
5. **View Answer Sources**:
   - Click "Show Sources" to see which documents were used
   - Review confidence scores
   - Explore related documents

#### **Step 5: Connection Discovery via Web Interface**

1. **Open Search Engine**: http://localhost:8004
2. **Click "Connection Discovery"**
3. **Enter Central Topic**: Type "artificial intelligence"
4. **Set Discovery Depth**: Choose how deep to explore connections (1-3 levels)
5. **View Connection Map**:
   - Interactive concept map showing relationships
   - Click on nodes to explore deeper connections
   - See relevance scores and document counts
6. **Generate Insights**:
   - Click "Generate Insights" to get AI analysis
   - View pattern analysis and relationship summaries
   - Export connection map as image or data

---

## 🎵 **Scenario 4: Emotional Analysis Environment Control**

Build a system that analyzes human emotions and automatically adjusts environment factors like mood lighting and background music.

### **What You'll Build**
- Real-time emotion detection from voice and facial expressions
- Environment control system for lighting and music
- Mood-based automation workflows
- Personalized environment preferences

### **Implementation Steps**

#### **Step 1: Create Emotion Analysis Agent via Web Interface**

1. **Open AI Agents Dashboard**: http://localhost:8003
2. **Click "Create New Agent"**
3. **Configure Agent**:
   - **Name**: "Emotion Environment Controller"
   - **Goal**: "Analyze human emotions and automatically adjust environment factors like lighting and music"
   - **Tools**: Select emotion_analysis, environment_control, music_selection
   - **Memory Window**: 30 conversations
4. **Click "Create Agent"**

#### **Step 2: Set Up Emotion Detection via Web Interface**

1. **Open Multimodal Worker**: http://localhost:8001
2. **Click "Emotion Detection"**
3. **Choose Input Method**:
   - **Audio Input**: Upload audio files or connect microphone
   - **Video Input**: Upload video files or connect webcam
   - **Real-time**: Enable live emotion detection
4. **Configure Detection Settings**:
   - Set confidence threshold (0.7 recommended)
   - Choose emotion categories (happy, sad, angry, calm, excited, neutral)
   - Enable real-time processing
5. **Test Detection**: Upload sample audio/video to test the system

#### **Step 3: Configure Environment Control via Web Interface**

1. **Open Environment Control Dashboard**: http://localhost:8008
2. **Add Smart Devices**:
   - **Lighting Systems**: Philips Hue, LIFX, SmartThings
   - **Music Systems**: Spotify, Sonos, AirPlay
   - **Other Devices**: Smart speakers, thermostats, etc.
3. **Set Up Device Connections**:
   - Enter device IP addresses and API keys
   - Test connections to ensure devices respond
   - Configure device groups (living room, bedroom, etc.)
4. **Create Emotion Presets**:
   - **Happy**: Warm white lighting, upbeat music
   - **Sad**: Soft blue lighting, melancholic music
   - **Angry**: Red lighting, aggressive music
   - **Calm**: Cool white lighting, ambient music
   - **Excited**: Dynamic colors, electronic music
   - **Neutral**: Daylight lighting, instrumental music
5. **Test Presets**: Click "Test" on each preset to verify device responses

#### **Step 4: Create n8n Emotion Control Workflow**

1. **Open n8n Workflow Builder**: http://localhost:5678
2. **Create New Workflow**: Click "New Workflow"

**Build the Emotion Control Pipeline:**

1. **Add Webhook Trigger**:
   - Drag "Webhook" node
   - Set Path to "emotion-detection"
   - Set HTTP Method to "POST"
   - Copy the webhook URL

2. **Add Emotion Analysis Node**:
   - Drag "HTTP Request" node
   - Set URL to: `http://multimodal-worker:8001/api/v1/process/audio`
   - Set Method to "POST"
   - In Body, add:
     ```json
     {
       "audio_path": "={{ $json.audio_path }}",
       "metadata": {
         "analysis_type": "emotion_detection"
       }
     }
     ```

3. **Add Environment Settings Logic**:
   - Drag "Function" node
   - Add this code:
     ```javascript
     const emotion = $input.first().json.emotions;
     const dominantEmotion = Object.keys(emotion).reduce((a, b) => emotion[a] > emotion[b] ? a : b);
     
     const environmentSettings = {
       'happy': { lighting: 'warm', music: 'upbeat', intensity: 0.8 },
       'sad': { lighting: 'soft', music: 'melancholic', intensity: 0.4 },
       'angry': { lighting: 'red', music: 'aggressive', intensity: 0.6 },
       'calm': { lighting: 'cool', music: 'ambient', intensity: 0.5 },
       'excited': { lighting: 'dynamic', music: 'electronic', intensity: 0.9 }
     };
     
     return {
       emotion: dominantEmotion,
       settings: environmentSettings[dominantEmotion] || environmentSettings['calm']
     };
     ```

4. **Add Lighting Control**:
   - Drag "HTTP Request" node
   - Set URL to: `http://192.168.1.100/api/lights/set`
   - Set Method to "POST"
   - In Body, add:
     ```json
     {
       "color": "={{ $json.settings.lighting }}",
       "intensity": "={{ $json.settings.intensity }}"
     }
     ```

5. **Add Music Control**:
   - Drag "HTTP Request" node
   - Set URL to: `http://localhost:8080/api/music/play`
   - Set Method to "POST"
   - In Body, add:
     ```json
     {
       "genre": "={{ $json.settings.music }}",
       "volume": "={{ $json.settings.intensity }}"
     }
     ```

6. **Add Logging Node**:
   - Drag "HTTP Request" node
   - Set URL to: `http://ai-agents:8003/api/v1/agents/[your-agent-id]/execute`
   - Set Method to "POST"
   - In Body, add:
     ```json
     {
       "task": "Log environment change based on emotion detection"
     }
     ```

7. **Connect All Nodes** and **Save/Activate** the workflow

#### **Step 5: Real-time Emotion Monitoring via Web Interface**

1. **Open Emotion Detection Dashboard**: http://localhost:8001/emotion-monitoring
2. **Enable Live Monitoring**:
   - Click "Start Live Monitoring"
   - Allow camera/microphone access when prompted
   - Set monitoring interval (1-5 seconds recommended)
3. **View Real-time Results**:
   - Watch emotion detection in real-time
   - See confidence scores and emotion changes
   - Monitor environment adjustments
4. **Control Monitoring**:
   - Pause/resume monitoring
   - Adjust sensitivity settings
   - View emotion history and trends

#### **Step 6: Personalized Environment Learning via Web Interface**

1. **Open Environment Control Dashboard**: http://localhost:8008
2. **Click "Learn Preferences"**
3. **Rate Environment Combinations**:
   - Test different lighting and music combinations
   - Rate each combination for each emotion (1-10 scale)
   - Provide feedback on what works best for you
4. **Save Personalized Presets**:
   - Click "Save Preferences" to store your ratings
   - The system will learn your preferences over time
   - View preference history and trends
5. **Test Personalized Settings**:
   - Click "Test Personalized Presets"
   - Verify that the system adjusts to your preferences

---

## 🚀 **Advanced Integration Examples**

### **Cross-Scenario Integration via Web Interface**

1. **Open AI Agents Dashboard**: http://localhost:8003
2. **Click "Create Master Agent"**
3. **Configure Unified Assistant**:
   - **Name**: "Unified AI Assistant"
   - **Goal**: "Provide comprehensive AI assistance across writing, photo analysis, knowledge management, and environment control"
   - **Tools**: Select all available tools from all scenarios
   - **Memory Window**: 200 conversations
4. **Set Up Cross-Scenario Triggers**:
   - Voice commands
   - Text input
   - Photo uploads
   - Document uploads
   - Emotion detection
5. **Enable Unified Capabilities**:
   - Creative writing assistance
   - Photo analysis and enhancement
   - Knowledge base search
   - Environment control
   - Cross-scenario insights

### **Real-time Collaboration via Web Interface**

1. **Open Collaboration Dashboard**: http://localhost:8000/collaboration
2. **Enable Real-time Features**:
   - Click "Enable Collaboration"
   - Set up WebSocket connections
   - Configure collaboration channels
3. **Configure Collaboration Channels**:
   - Writing sessions
   - Photo analysis
   - Knowledge sharing
   - Environment control
4. **Enable Collaboration Features**:
   - Live editing
   - Real-time feedback
   - Shared workspace
   - Presence indicators
5. **Invite Collaborators**:
   - Share collaboration links
   - Set permissions and access levels
   - Monitor active sessions

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