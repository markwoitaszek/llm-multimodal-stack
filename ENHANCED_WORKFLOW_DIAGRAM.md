# Enhanced Workflow Diagram - LLM Multimodal Stack (Post PR 130 + Enhancements)

## 🎯 Overview

This diagram shows the complete workflow for the enhanced LLM Multimodal Stack, including the unified schema system from PR 130 and the new GPU optimization, environment wipe, and security hardening features.

## 🏗️ Enhanced System Architecture

```mermaid
graph TB
    %% User Interface Layer
    subgraph UserInterface[User Interface Layer]
        Developer["👨‍💻 Developer"]
        Makefile["📋 Makefile Commands"]
        Scripts["🔧 Enhanced Scripts"]
    end

    %% Enhanced Command Layer
    subgraph CommandLayer[Enhanced Command Layer]
        CoreCommands["Core Commands<br/>make setup, start-dev, start-prod"]
        GPUCommands["🎮 GPU Commands<br/>make detect-gpu, configure-gpu<br/>make start-gpu-auto"]
        WipeCommands["🧹 Wipe Commands<br/>make wipe, make reset"]
        SecurityCommands["🔒 Security Commands<br/>make validate-security"]
    end

    %% Unified Schema System (PR 130)
    subgraph SchemaSystem[Unified Schema System]
        Schema["📄 schemas/compose-schema.yaml<br/>Single Source of Truth (844 lines)"]
        Generator["⚙️ scripts/compose-generator.py<br/>Schema Processor"]
        GeneratedFiles["📁 Generated Compose Files<br/>compose.yml, compose.development.yml<br/>compose.staging.yml, compose.production.yml<br/>compose.gpu.yml, compose.elk.yml"]
    end

    %% Environment Templates
    subgraph EnvTemplates[Environment Templates]
        EnvTemplates["📄 env-templates/*.env.j2<br/>Jinja2 Templates"]
        CoreTemplate["core.env.j2"]
        VLLMTemplate["vllm.env.j2"]
        MasterTemplate["master.env.j2"]
        ServiceTemplates["Service-specific templates"]
    end

    %% Enhanced GPU System
    subgraph GPUSystem[Enhanced GPU System]
        GPUDetection["🔍 scripts/configure-gpu.sh<br/>GPU Detection & Configuration"]
        NVLinkDetection["🔗 NVLink Topology Detection"]
        RTX3090Config["🎮 RTX 3090 Optimization<br/>Tensor Parallelism: 2<br/>GPU Memory: 0.8-0.9"]
        CUDAConfig["⚡ CUDA Configuration<br/>CUDA_VISIBLE_DEVICES=0,1<br/>VLLM_TENSOR_PARALLEL_SIZE=2"]
    end

    %% Environment Wipe System
    subgraph WipeSystem[Environment Wipe System]
        WipeScript["🧹 scripts/wipe-environment.sh<br/>Comprehensive Reset"]
        ContainerWipe["🗑️ Container Cleanup"]
        VolumeWipe["💾 Volume Cleanup<br/>PostgreSQL, MinIO data"]
        NetworkWipe["🌐 Network Cleanup"]
        SecretsRegen["🔐 Secrets Regeneration"]
    end

    %% Security System
    subgraph SecuritySystem[Security System]
        SecurityValidation["🔒 Security Validation<br/>No hardcoded defaults"]
        SecretsManagement["🔐 Secrets Management<br/>setup_secrets.py"]
        SchemaValidation["✅ Schema Validation<br/>syntax and structure"]
    end

    %% Service Categories
    subgraph CoreServices[Core Services]
        Postgres[("🐘 PostgreSQL<br/>Database")]
        Redis[("🔴 Redis<br/>Cache")]
        Qdrant[("🔍 Qdrant<br/>Vector DB")]
        Minio[("📦 MinIO<br/>Object Storage")]
    end

    subgraph InferenceServices[Inference Services]
        VLLM["🚀 vLLM<br/>Model Server<br/>:8000"]
        LiteLLM["⚡ LiteLLM<br/>API Gateway<br/>:4000"]
    end

    subgraph MultimodalServices[Multimodal Services]
        MultimodalWorker["🤖 Multimodal Worker<br/>:8001"]
        RetrievalProxy["🔍 Retrieval Proxy<br/>:8002"]
        AIAgents["🧠 AI Agents<br/>:8003"]
        MemorySystem["🧠 Memory System<br/>:8004"]
        SearchEngine["🔍 Search Engine<br/>:8005"]
        UserManagement["👤 User Management<br/>:8006"]
    end

    subgraph UIServices[UI & Workflow Services]
        OpenWebUI["🌐 OpenWebUI<br/>:3030"]
        N8N["⚡ n8n<br/>:5678"]
        N8NMonitoring["📊 n8n Monitoring<br/>:5679"]
    end

    subgraph MonitoringServices[Monitoring Services]
        Prometheus["📊 Prometheus<br/>:9090"]
        Grafana["📈 Grafana<br/>:3000"]
        Elasticsearch["🔍 Elasticsearch<br/>:9200"]
        Kibana["📊 Kibana<br/>:5601"]
        Logstash["📝 Logstash<br/>:9600"]
    end

    %% Enhanced Workflow Connections
    Developer --> Makefile
    Makefile --> CoreCommands
    Makefile --> GPUCommands
    Makefile --> WipeCommands
    Makefile --> SecurityCommands

    %% Schema System Flow
    CoreCommands --> Schema
    Schema --> Generator
    Generator --> GeneratedFiles
    GeneratedFiles --> CoreServices
    GeneratedFiles --> InferenceServices
    GeneratedFiles --> MultimodalServices
    GeneratedFiles --> UIServices
    GeneratedFiles --> MonitoringServices

    %% GPU Enhancement Flow
    GPUCommands --> GPUDetection
    GPUDetection --> NVLinkDetection
    NVLinkDetection --> RTX3090Config
    RTX3090Config --> CUDAConfig
    CUDAConfig --> GeneratedFiles

    %% Wipe Enhancement Flow
    WipeCommands --> WipeScript
    WipeScript --> ContainerWipe
    WipeScript --> VolumeWipe
    WipeScript --> NetworkWipe
    WipeScript --> SecretsRegen

    %% Security Enhancement Flow
    SecurityCommands --> SecurityValidation
    SecurityValidation --> Schema
    SecurityValidation --> EnvTemplates
    SecretsManagement --> EnvTemplates

    %% Environment Template Flow
    EnvTemplates --> CoreTemplate
    EnvTemplates --> VLLMTemplate
    EnvTemplates --> MasterTemplate
    EnvTemplates --> ServiceTemplates

    %% Service Dependencies
    InferenceServices --> CoreServices
    MultimodalServices --> CoreServices
    MultimodalServices --> InferenceServices
    UIServices --> MultimodalServices
    MonitoringServices --> CoreServices

    %% Styling
    classDef enhanced fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef gpu fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef wipe fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef security fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef core fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class GPUCommands,GPUDetection,NVLinkDetection,RTX3090Config,CUDAConfig gpu
    class WipeCommands,WipeScript,ContainerWipe,VolumeWipe,NetworkWipe,SecretsRegen wipe
    class SecurityCommands,SecurityValidation,SecuritySystem security
    class CoreServices,InferenceServices,MultimodalServices,UIServices,MonitoringServices core
    class CoreCommands,Schema,Generator,GeneratedFiles,EnvTemplates enhanced
```

## 🚀 Enhanced Workflow Processes

### 1. Complete Setup Workflow

```mermaid
flowchart TD
    Start["🚀 make setup"] --> ValidateSchema["✅ make validate-schema"]
    ValidateSchema --> ValidateSecurity["🔒 make validate-security"]
    ValidateSecurity --> GenerateCompose["⚙️ make generate-compose"]
    GenerateCompose --> SetupSecrets["🔐 make setup-secrets"]
    SetupSecrets --> Complete["🎉 Setup Complete"]
    
    Complete --> NextSteps["📋 Next Steps Available:<br/>• make start-dev<br/>• make start-gpu-auto<br/>• make start-prod"]
```

### 2. Enhanced GPU Workflow

```mermaid
flowchart TD
    GPUSetup["🎮 GPU Setup"] --> DetectGPU["🔍 make detect-gpu"]
    DetectGPU --> GPUFound{"GPU Detected?"}
    
    GPUFound -->|Yes| ShowTopology["🔗 Show NVLink Topology<br/>GPU0 ←→ GPU1<br/>NV4 Connection"]
    GPUFound -->|No| CPUOnly["💻 CPU-only mode"]
    
    ShowTopology --> ConfigureGPU["⚙️ make configure-gpu"]
    ConfigureGPU --> SetEnvVars["🔧 Set Environment Variables:<br/>CUDA_VISIBLE_DEVICES=0,1<br/>VLLM_TENSOR_PARALLEL_SIZE=2<br/>GPU_COUNT=2"]
    
    SetEnvVars --> StartGPU["🚀 make start-gpu-auto"]
    StartGPU --> GPURunning["✅ GPU Environment Running<br/>Optimized for RTX 3090s"]
    
    CPUOnly --> StartDev["🚀 make start-dev"]
    StartDev --> DevRunning["✅ Development Environment Running"]
```

### 3. Environment Wipe Workflow

```mermaid
flowchart TD
    WipeRequest["🧹 make wipe"] --> Warning["⚠️ WARNING: DESTRUCTIVE OPERATION<br/>This will DELETE all data and containers!"]
    Warning --> Confirmation{"Type 'yes' to continue"}
    
    Confirmation -->|No| Cancel["❌ Operation cancelled"]
    Confirmation -->|Yes| WipeScript["🧹 scripts/wipe-environment.sh"]
    
    WipeScript --> StopContainers["🛑 Stop all compose services"]
    StopContainers --> RemoveVolumes["💾 Remove multimodal volumes<br/>(PostgreSQL, MinIO data)"]
    RemoveVolumes --> RemoveNetworks["🌐 Remove multimodal networks"]
    RemoveNetworks --> CleanupOrphans["🧹 Clean up orphaned containers"]
    CleanupOrphans --> WipeComplete["✅ Environment wiped completely"]
    
    WipeComplete --> ResetOption["🔄 make reset<br/>(Wipe + Regenerate)"]
    ResetOption --> FreshSetup["🎉 Fresh environment from scratch"]
```

### 4. Security Validation Workflow

```mermaid
flowchart TD
    SecurityCheck["🔒 make validate-security"] --> CheckSchema["🔍 Check schemas/compose-schema.yaml<br/>for hardcoded defaults"]
    CheckSchema --> SchemaClean{"Schema Clean?"}
    
    SchemaClean -->|No| SchemaFail["❌ Hardcoded defaults found in schema"]
    SchemaClean -->|Yes| CheckServices["🔍 Check service configs<br/>for hardcoded defaults"]
    
    CheckServices --> ServicesClean{"Services Clean?"}
    ServicesClean -->|No| ServicesFail["❌ Hardcoded defaults found in services"]
    ServicesClean -->|Yes| SecurityPass["✅ Security validation passed"]
    
    SchemaFail --> FixSchema["🔧 Fix schema defaults"]
    ServicesFail --> FixServices["🔧 Fix service defaults"]
    FixSchema --> SecurityCheck
    FixServices --> SecurityCheck
```

### 5. Environment Management Workflow

```mermaid
flowchart TD
    EnvChoice["🌍 Environment Choice"] --> Dev["🔧 Development<br/>make start-dev"]
    EnvChoice --> Staging["🏗️ Staging<br/>make start-staging"]
    EnvChoice --> Prod["🚀 Production<br/>make start-prod"]
    EnvChoice --> GPU["🎮 GPU Optimized<br/>make start-gpu-auto"]
    EnvChoice --> Monitoring["📊 Monitoring<br/>make start-monitoring"]
    
    Dev --> DevServices["📋 Services:<br/>• LiteLLM: :4000<br/>• vLLM: :8000<br/>• Multimodal Worker: :8001<br/>• Qdrant: :6333<br/>• MinIO: :9002"]
    
    Staging --> StagingServices["📋 Services:<br/>• All base services<br/>• Production-like config<br/>• Monitoring enabled"]
    
    Prod --> ProdServices["📋 Services:<br/>• All base services<br/>• Prometheus: :9090<br/>• Grafana: :3000<br/>• Full monitoring"]
    
    GPU --> GPUServices["📋 Services:<br/>• Dual RTX 3090 optimized<br/>• NVLink topology detected<br/>• Tensor parallelism: 2<br/>• GPU memory: 0.8-0.9"]
    
    Monitoring --> MonitoringServices["📋 Services:<br/>• Kibana: :5601<br/>• Elasticsearch: :9200<br/>• Logstash: :9600<br/>• ELK stack"]
```

## 🔄 Enhanced Command Matrix

| Command | Purpose | Enhanced Features |
|---------|---------|-------------------|
| `make setup` | Complete setup | ✅ Security validation added |
| `make start-dev` | Development | ✅ GPU auto-detection |
| `make start-gpu` | GPU environment | ✅ NVLink optimization |
| `make start-gpu-auto` | **NEW** | ✅ Auto-detect + configure + start |
| `make detect-gpu` | **NEW** | ✅ RTX 3090 + NVLink detection |
| `make configure-gpu` | **NEW** | ✅ Optimal GPU configuration |
| `make wipe` | **NEW** | ✅ Complete environment reset |
| `make reset` | **NEW** | ✅ Wipe + regenerate from scratch |
| `make validate-security` | **NEW** | ✅ No hardcoded defaults check |

## 🎯 Key Enhancements Over Previous System

### ✅ **What's New**
1. **GPU Auto-Detection**: Automatic RTX 3090 and NVLink topology detection
2. **Comprehensive Wipe**: Complete environment reset including database volumes
3. **Security Hardening**: Validation and removal of hardcoded defaults
4. **Enhanced Makefile**: Professional command interface with new targets
5. **Unified Schema**: Single source of truth for all configurations

### 🔄 **What's Improved**
1. **Schema-Driven**: All compose files generated from unified schema
2. **Template-Based**: Jinja2 environment templates for consistency
3. **Professional Commands**: Clean, intuitive Makefile targets
4. **Comprehensive Documentation**: Complete workflow and configuration guides

---

**Diagram Version**: 2.0 (Post PR 130 + Enhancements)  
**Last Updated**: October 1, 2024  
**Compatible With**: Enhanced LLM Multimodal Stack
