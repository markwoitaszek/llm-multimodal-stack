"""
API endpoints for Setup Wizard Service
"""

import uuid
import asyncio
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .models import (
    SetupState, SetupStep, SetupProgress, SystemCheckResult,
    ModelOption, StorageConfig, SecurityConfig, DeploymentConfig,
    ValidationResult, DeploymentStatus
)
from .system_checker import SystemChecker
from .model_selector import ModelSelector
from .config_generator import ConfigGenerator
from .tutorials import TutorialManager, TutorialCategory

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for setup sessions (in production, use Redis or database)
setup_sessions: Dict[str, SetupProgress] = {}

# Initialize services
system_checker = SystemChecker()
model_selector = ModelSelector()
config_generator = ConfigGenerator()
tutorial_manager = TutorialManager()


@router.get("/", response_class=HTMLResponse)
async def setup_wizard_home():
    """Serve the setup wizard frontend"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Multimodal LLM Stack Setup Wizard</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f7; }
            .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 40px; }
            .logo { font-size: 32px; font-weight: 700; color: #1d1d1f; margin-bottom: 8px; }
            .subtitle { color: #86868b; font-size: 18px; }
            .step { margin-bottom: 30px; padding: 20px; border: 2px solid #e5e5e7; border-radius: 8px; }
            .step.active { border-color: #007aff; background: #f0f8ff; }
            .step.completed { border-color: #34c759; background: #f0fff4; }
            .step-title { font-size: 20px; font-weight: 600; margin-bottom: 10px; }
            .step-description { color: #86868b; margin-bottom: 15px; }
            .btn { background: #007aff; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-size: 16px; cursor: pointer; }
            .btn:hover { background: #0056b3; }
            .btn:disabled { background: #d1d1d6; cursor: not-allowed; }
            .progress-bar { width: 100%; height: 8px; background: #e5e5e7; border-radius: 4px; margin: 20px 0; }
            .progress-fill { height: 100%; background: #007aff; border-radius: 4px; transition: width 0.3s ease; }
            .model-option { padding: 15px; border: 2px solid #e5e5e7; border-radius: 8px; margin-bottom: 10px; cursor: pointer; }
            .model-option.selected { border-color: #007aff; background: #f0f8ff; }
            .model-option.recommended { border-color: #34c759; }
            .model-name { font-weight: 600; margin-bottom: 5px; }
            .model-description { color: #86868b; font-size: 14px; margin-bottom: 8px; }
            .model-specs { font-size: 12px; color: #86868b; }
            .warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 12px; border-radius: 6px; margin: 10px 0; }
            .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 12px; border-radius: 6px; margin: 10px 0; }
            .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 12px; border-radius: 6px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🚀 Multimodal LLM Stack</div>
                <div class="subtitle">Setup Wizard & Tutorials</div>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill" style="width: 0%"></div>
            </div>
            
            <div id="setupContent">
                <div class="step active" id="step-welcome">
                    <div class="step-title">Welcome to the Setup Wizard</div>
                    <div class="step-description">
                        This wizard will guide you through setting up your Multimodal LLM Stack. 
                        We'll check your system, help you choose the right model, and configure everything automatically.
                    </div>
                    <button class="btn" onclick="startSetup()">Get Started</button>
                </div>
            </div>
        </div>
        
        <script>
            let setupSession = null;
            
            async function startSetup() {
                try {
                    const response = await fetch('/api/setup/start', { method: 'POST' });
                    setupSession = await response.json();
                    loadStep(setupSession.state.current_step);
                } catch (error) {
                    console.error('Failed to start setup:', error);
                }
            }
            
            async function loadStep(step) {
                const response = await fetch(`/api/setup/step/${step}`);
                const stepData = await response.json();
                
                document.getElementById('setupContent').innerHTML = stepData.html;
                updateProgress(stepData.progress_percentage);
            }
            
            function updateProgress(percentage) {
                document.getElementById('progressFill').style.width = percentage + '%';
            }
            
            // Add more JavaScript functions as needed
        </script>
    </body>
    </html>
    """


@router.post("/api/setup/start", response_model=SetupProgress)
async def start_setup():
    """Start a new setup session"""
    session_id = str(uuid.uuid4())
    
    setup_state = SetupState(
        current_step=SetupStep.WELCOME,
        completed_steps=[]
    )
    
    setup_progress = SetupProgress(
        session_id=session_id,
        state=setup_state,
        progress_percentage=0.0,
        current_task="Starting setup wizard..."
    )
    
    setup_sessions[session_id] = setup_progress
    
    logger.info(f"Started setup session: {session_id}")
    return setup_progress


@router.get("/api/setup/step/{step}", response_model=Dict[str, Any])
async def get_setup_step(step: SetupStep):
    """Get setup step content and progress"""
    # This would typically load from the current session
    # For now, return static content for each step
    
    step_content = {
        SetupStep.WELCOME: {
            "html": """
            <div class="step active">
                <div class="step-title">Welcome to the Setup Wizard</div>
                <div class="step-description">
                    This wizard will guide you through setting up your Multimodal LLM Stack. 
                    We'll check your system, help you choose the right model, and configure everything automatically.
                </div>
                <button class="btn" onclick="nextStep()">Get Started</button>
            </div>
            """,
            "progress_percentage": 10.0
        },
        SetupStep.SYSTEM_CHECK: {
            "html": """
            <div class="step active">
                <div class="step-title">System Check</div>
                <div class="step-description">
                    Checking your system requirements and available resources...
                </div>
                <button class="btn" onclick="runSystemCheck()">Check System</button>
            </div>
            """,
            "progress_percentage": 20.0
        },
        SetupStep.MODEL_SELECTION: {
            "html": """
            <div class="step active">
                <div class="step-title">Choose Your AI Model</div>
                <div class="step-description">
                    Select the AI model that best fits your needs and system capabilities.
                </div>
                <div id="modelOptions"></div>
                <button class="btn" onclick="nextStep()" disabled id="modelNextBtn">Continue</button>
            </div>
            """,
            "progress_percentage": 40.0
        }
    }
    
    return step_content.get(step, {"html": "<div>Step not found</div>", "progress_percentage": 0.0})


@router.post("/api/setup/system-check", response_model=SystemCheckResult)
async def run_system_check():
    """Run system check"""
    try:
        result = system_checker.run_full_check()
        logger.info("System check completed successfully")
        return result
    except Exception as e:
        logger.error(f"System check failed: {e}")
        raise HTTPException(status_code=500, detail=f"System check failed: {str(e)}")


@router.get("/api/setup/models", response_model=List[ModelOption])
async def get_available_models():
    """Get available models"""
    return model_selector.available_models


@router.get("/api/setup/models/recommended", response_model=List[ModelOption])
async def get_recommended_models():
    """Get recommended models for beginners"""
    return model_selector.get_recommended_models()


@router.post("/api/setup/validate-model")
async def validate_model_selection(model_id: str):
    """Validate model selection"""
    try:
        # Get system check result (would come from session in real implementation)
        system_check = SystemCheckResult(
            docker_installed=True,
            docker_compose_installed=True,
            nvidia_gpu_available=True,
            nvidia_docker_available=True,
            disk_space_gb=50.0,
            memory_gb=16.0,
            ports_available=[],
            conflicts=[]
        )
        
        validation = model_selector.validate_model_selection(model_id, system_check)
        return validation
    except Exception as e:
        logger.error(f"Model validation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid model: {str(e)}")


@router.post("/api/setup/configure")
async def configure_setup(
    storage_config: StorageConfig,
    security_config: SecurityConfig,
    deployment_config: DeploymentConfig,
    selected_model: str
):
    """Configure setup based on user choices"""
    try:
        # This would update the session state
        # For now, just return success
        return {"status": "configured", "message": "Setup configured successfully"}
    except Exception as e:
        logger.error(f"Setup configuration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")


@router.post("/api/setup/deploy")
async def deploy_stack(background_tasks: BackgroundTasks):
    """Deploy the stack"""
    try:
        # Start deployment in background
        background_tasks.add_task(deploy_stack_background)
        
        return {
            "status": "deploying",
            "message": "Deployment started in background"
        }
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


async def deploy_stack_background():
    """Background deployment task"""
    try:
        logger.info("Starting background deployment...")
        
        # This would run the actual deployment
        # For now, just simulate
        await asyncio.sleep(5)
        
        logger.info("Background deployment completed")
    except Exception as e:
        logger.error(f"Background deployment failed: {e}")


@router.get("/api/setup/status/{session_id}", response_model=DeploymentStatus)
async def get_deployment_status(session_id: str):
    """Get deployment status"""
    if session_id not in setup_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Return mock deployment status
    return DeploymentStatus(
        status="completed",
        progress=100.0,
        current_service="All services",
        completed_services=["vllm", "litellm", "multimodal-worker", "retrieval-proxy", "openwebui"],
        failed_services=[],
        logs=["Deployment completed successfully"],
        errors=[]
    )


@router.get("/api/setup/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "setup-wizard"}


# Tutorial endpoints
@router.get("/api/tutorials")
async def get_all_tutorials():
    """Get all available tutorials"""
    return tutorial_manager.tutorials


@router.get("/api/tutorials/category/{category}")
async def get_tutorials_by_category(category: TutorialCategory):
    """Get tutorials by category"""
    return tutorial_manager.get_tutorials_by_category(category)


@router.get("/api/tutorials/beginner")
async def get_beginner_tutorials():
    """Get beginner-friendly tutorials"""
    return tutorial_manager.get_beginner_tutorials()


@router.get("/api/tutorials/{tutorial_id}")
async def get_tutorial(tutorial_id: str):
    """Get specific tutorial"""
    tutorial = tutorial_manager.get_tutorial(tutorial_id)
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    return tutorial


@router.get("/api/tutorials/{tutorial_id}/progress")
async def get_tutorial_progress(tutorial_id: str, user_id: str = "default"):
    """Get tutorial progress for user"""
    progress = tutorial_manager.get_tutorial_progress(user_id, tutorial_id)
    return progress


@router.post("/api/tutorials/{tutorial_id}/progress")
async def update_tutorial_progress(tutorial_id: str, step_id: str, user_id: str = "default"):
    """Update tutorial progress"""
    success = tutorial_manager.update_tutorial_progress(user_id, tutorial_id, step_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update progress")
    return {"status": "updated", "step": step_id}
