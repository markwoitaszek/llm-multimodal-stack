"""
API routes for the AI agents service
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field

from .config import settings
from .templates import get_all_templates, get_template, get_templates_by_category, search_templates

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class CreateAgentRequest(BaseModel):
    name: str = Field(..., description="Agent name")
    goal: str = Field(..., description="Agent goal or purpose")
    tools: Optional[List[str]] = Field(default=None, description="List of tool names to enable")
    memory_window: Optional[int] = Field(default=10, description="Conversation memory window size")
    user_id: Optional[str] = Field(default="default", description="User ID")

class ExecuteTaskRequest(BaseModel):
    task: str = Field(..., description="Task for the agent to execute")
    user_id: Optional[str] = Field(default="default", description="User ID")

class AgentResponse(BaseModel):
    agent_id: str
    name: str
    goal: str
    tools: List[str]
    created_at: str
    status: str

class ExecutionResponse(BaseModel):
    agent_id: str
    task: str
    result: str
    success: bool
    intermediate_steps: Optional[List[Dict[str, Any]]] = None

@router.post("/agents", response_model=Dict[str, str])
async def create_agent(request: CreateAgentRequest, background_tasks: BackgroundTasks, req: Request):
    """Create a new AI agent"""
    try:
        # Validate request
        if not request.name or not request.goal:
            raise HTTPException(status_code=400, detail="Name and goal are required")
        
        # Get agent manager from app state
        agent_manager = req.app.state.agent_manager
        
        # Create agent using the actual AgentManager
        agent_id = await agent_manager.create_agent(
            agent_name=request.name,
            goal=request.goal,
            tools=request.tools,
            memory_window=request.memory_window,
            user_id=request.user_id
        )
        
        return {
            "agent_id": agent_id,
            "message": f"Agent '{request.name}' created successfully",
            "goal": request.goal,
            "tools": request.tools or [],
            "status": "created"
        }
        
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents", response_model=List[AgentResponse])
async def list_agents(user_id: str = "default", req: Request = None):
    """List all agents for a user"""
    try:
        # Get agent manager from app state
        agent_manager = req.app.state.agent_manager
        
        # Get agents using the actual AgentManager
        agents_data = await agent_manager.list_agents(user_id)
        
        # Convert to response format
        agents = []
        for agent_data in agents_data:
            agents.append(AgentResponse(
                agent_id=agent_data["agent_id"],
                name=agent_data["name"],
                goal=agent_data["goal"],
                tools=agent_data["tools"],
                created_at=agent_data["created_at"].isoformat() if agent_data.get("created_at") else "",
                status=agent_data["status"]
            ))
        
        return agents
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, req: Request = None):
    """Get agent information"""
    try:
        # Get agent manager from app state
        agent_manager = req.app.state.agent_manager
        
        # Get agent info using the actual AgentManager
        agent_data = await agent_manager.get_agent_info(agent_id)
        
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return AgentResponse(
            agent_id=agent_data["agent_id"],
            name=agent_data["name"],
            goal=agent_data["goal"],
            tools=agent_data["tools"],
            created_at=agent_data["created_at"].isoformat() if agent_data.get("created_at") else "",
            status=agent_data["status"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{agent_id}/execute", response_model=ExecutionResponse)
async def execute_agent_task(agent_id: str, request: ExecuteTaskRequest, req: Request):
    """Execute a task with an agent"""
    try:
        # Get agent manager from app state
        agent_manager = req.app.state.agent_manager
        
        # Execute task using the actual AgentManager
        execution_result = await agent_manager.execute_agent(
            agent_id=agent_id,
            task=request.task,
            user_id=request.user_id
        )
        
        return ExecutionResponse(
            agent_id=execution_result["agent_id"],
            task=execution_result["task"],
            result=execution_result.get("result", ""),
            success=execution_result["success"],
            intermediate_steps=execution_result.get("intermediate_steps", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to execute agent task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, user_id: str = "default", req: Request = None):
    """Delete an agent"""
    try:
        # Get agent manager from app state
        agent_manager = req.app.state.agent_manager
        
        # Delete agent using the actual AgentManager
        success = await agent_manager.delete_agent(agent_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found or could not be deleted")
        
        return {
            "message": f"Agent {agent_id} deleted successfully",
            "agent_id": agent_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools")
async def list_tools(req: Request = None):
    """List available tools for agents"""
    try:
        # Get tool registry from app state
        tool_registry = req.app.state.tool_registry
        
        # Get tools using the actual ToolRegistry
        tools = await tool_registry.list_available_tools()
        
        return {
            "tools": tools,
            "count": len(tools)
        }
        
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def list_templates(category: Optional[str] = None, search: Optional[str] = None):
    """List available agent templates"""
    try:
        if search:
            templates = search_templates(search)
        elif category:
            templates = get_templates_by_category(category)
        else:
            templates = get_all_templates()
        
        # Convert templates to response format
        template_list = []
        for name, template in templates.items():
            template_list.append({
                "name": name,
                "display_name": template.name,
                "description": template.description,
                "goal": template.goal,
                "tools": template.tools,
                "memory_window": template.memory_window,
                "category": template.category,
                "use_cases": template.use_cases
            })
        
        return {
            "templates": template_list,
            "count": len(template_list),
            "category": category,
            "search": search
        }
        
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/{template_name}")
async def get_template_details(template_name: str):
    """Get details for a specific template"""
    try:
        template = get_template(template_name)
        
        return {
            "name": template_name,
            "display_name": template.name,
            "description": template.description,
            "goal": template.goal,
            "tools": template.tools,
            "memory_window": template.memory_window,
            "category": template.category,
            "use_cases": template.use_cases
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get template details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/from-template")
async def create_agent_from_template(
    template_name: str,
    agent_name: Optional[str] = None,
    user_id: str = "default",
    req: Request = None
):
    """Create an agent from a template"""
    try:
        # Get template
        template = get_template(template_name)
        
        # Get agent manager from app state
        agent_manager = req.app.state.agent_manager
        
        # Create agent using template
        agent_id = await agent_manager.create_agent(
            agent_name=agent_name or template.name,
            goal=template.goal,
            tools=template.tools,
            memory_window=template.memory_window,
            user_id=user_id
        )
        
        return {
            "agent_id": agent_id,
            "template_name": template_name,
            "agent_name": agent_name or template.name,
            "message": f"Agent created from template '{template.name}'",
            "goal": template.goal,
            "tools": template.tools,
            "status": "created"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create agent from template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/categories")
async def list_template_categories():
    """List all template categories"""
    try:
        from .templates import AgentTemplates
        categories = AgentTemplates.get_categories()
        
        return {
            "categories": categories,
            "count": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Failed to list template categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}/history")
async def get_agent_history(
    agent_id: str,
    limit: int = 20,
    req: Request = None
):
    """Get conversation history for an agent"""
    try:
        memory_manager = req.app.state.memory_manager
        
        # Get execution history from memory manager
        async with memory_manager.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT task, result, executed_at, success, execution_time_ms
                FROM agent_executions
                WHERE agent_id = $1
                ORDER BY executed_at DESC
                LIMIT $2
            """, agent_id, limit)
            
            history = []
            for row in rows:
                history.append({
                    "task": row['task'],
                    "result": row['result'],
                    "executed_at": row['executed_at'].isoformat(),
                    "success": row['success'],
                    "execution_time_ms": row['execution_time_ms']
                })
        
        return {
            "agent_id": agent_id,
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}/stats")
async def get_agent_stats(agent_id: str, req: Request = None):
    """Get statistics for an agent"""
    try:
        memory_manager = req.app.state.memory_manager
        
        async with memory_manager.pool.acquire() as conn:
            # Get execution statistics
            stats_row = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_executions,
                    COUNT(CASE WHEN success = true THEN 1 END) as successful_executions,
                    AVG(CASE WHEN execution_time_ms IS NOT NULL THEN execution_time_ms END) as avg_execution_time,
                    MAX(executed_at) as last_execution
                FROM agent_executions
                WHERE agent_id = $1
            """, agent_id)
            
            if not stats_row:
                return {
                    "agent_id": agent_id,
                    "total_executions": 0,
                    "successful_executions": 0,
                    "success_rate": 0,
                    "avg_execution_time_ms": 0,
                    "last_execution": None
                }
            
            total_executions = stats_row['total_executions'] or 0
            successful_executions = stats_row['successful_executions'] or 0
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
            
            return {
                "agent_id": agent_id,
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "success_rate": round(success_rate, 2),
                "avg_execution_time_ms": round(stats_row['avg_execution_time'] or 0, 2),
                "last_execution": stats_row['last_execution'].isoformat() if stats_row['last_execution'] else None
            }
        
    except Exception as e:
        logger.error(f"Failed to get agent stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_service_status():
    """Get AI agents service status"""
    try:
        return {
            "service": "ai-agents",
            "status": "healthy",
            "version": "1.0.0",
            "features": {
                "langchain": "enabled",
                "multimodal_tools": "enabled",
                "persistent_memory": "enabled",
                "autonomous_execution": "enabled"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
