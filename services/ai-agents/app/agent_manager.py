"""
Agent Manager for LangChain-based autonomous agents
"""
import logging
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage

from .config import settings
from .tools import ToolRegistry
from .memory import MemoryManager

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages autonomous AI agents with multimodal capabilities"""
    
    def __init__(self, tool_registry: ToolRegistry, memory_manager: MemoryManager):
        self.tool_registry = tool_registry
        self.memory_manager = memory_manager
        self.agents: Dict[str, AgentExecutor] = {}
        self.llm = None
    
    async def initialize(self):
        """Initialize the agent manager"""
        try:
            # Initialize LLM connection
            self.llm = ChatOpenAI(
                base_url=settings.llm_base_url,
                api_key="dummy-key",  # Not required for local vLLM
                model_name=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )
            
            logger.info("Agent Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Agent Manager: {e}")
            raise
    
    async def create_agent(self, 
                          agent_name: str,
                          goal: str,
                          tools: List[str] = None,
                          memory_window: int = 10,
                          user_id: str = "default") -> str:
        """Create a new autonomous agent"""
        try:
            agent_id = str(uuid.uuid4())
            
            # Get available tools
            available_tools = await self.tool_registry.get_tools(tools or [])
            
            # Create agent memory
            memory = ConversationBufferWindowMemory(
                k=memory_window,
                memory_key="chat_history",
                return_messages=True
            )
            
            # Create agent prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are an autonomous AI agent with the following goal:
                
**Goal**: {goal}

You have access to various tools to help you achieve this goal. Use them wisely and efficiently.

**Available Tools**: {[tool.name for tool in available_tools]}

**Instructions**:
1. Break down complex tasks into smaller steps
2. Use tools when appropriate to gather information or perform actions
3. Provide clear explanations of your reasoning
4. Ask for clarification if the goal is unclear
5. Report progress and results clearly

Remember: You are autonomous but should be helpful and safe in your actions."""),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])
            
            # Create agent
            agent = create_openai_functions_agent(
                llm=self.llm,
                tools=available_tools,
                prompt=prompt
            )
            
            # Create agent executor
            agent_executor = AgentExecutor(
                agent=agent,
                tools=available_tools,
                memory=memory,
                verbose=settings.langchain_verbose,
                max_iterations=settings.max_tool_calls_per_execution,
                max_execution_time=settings.agent_execution_timeout,
                return_intermediate_steps=True
            )
            
            # Store agent
            self.agents[agent_id] = agent_executor
            
            # Save agent metadata
            await self.memory_manager.save_agent_metadata(
                agent_id=agent_id,
                agent_name=agent_name,
                goal=goal,
                tools=tools or [],
                user_id=user_id,
                created_at=datetime.utcnow()
            )
            
            logger.info(f"Created agent '{agent_name}' with ID: {agent_id}")
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise
    
    async def execute_agent(self, 
                           agent_id: str, 
                           task: str,
                           user_id: str = "default") -> Dict[str, Any]:
        """Execute a task with an agent"""
        try:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent_executor = self.agents[agent_id]
            
            # Execute the task
            result = await agent_executor.ainvoke({
                "input": task
            })
            
            # Save execution history
            await self.memory_manager.save_agent_execution(
                agent_id=agent_id,
                task=task,
                result=result,
                user_id=user_id,
                executed_at=datetime.utcnow()
            )
            
            return {
                "agent_id": agent_id,
                "task": task,
                "result": result["output"],
                "intermediate_steps": result.get("intermediate_steps", []),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "agent_id": agent_id,
                "task": task,
                "error": str(e),
                "success": False
            }
    
    async def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information"""
        try:
            metadata = await self.memory_manager.get_agent_metadata(agent_id)
            
            if not metadata:
                return None
            
            return {
                "agent_id": agent_id,
                "name": metadata.get("agent_name"),
                "goal": metadata.get("goal"),
                "tools": metadata.get("tools", []),
                "created_at": metadata.get("created_at"),
                "status": "active" if agent_id in self.agents else "inactive"
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent info: {e}")
            return None
    
    async def list_agents(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """List all agents for a user"""
        try:
            agent_list = await self.memory_manager.list_user_agents(user_id)
            
            result = []
            for agent_data in agent_list:
                agent_info = await self.get_agent_info(agent_data["agent_id"])
                if agent_info:
                    result.append(agent_info)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return []
    
    async def delete_agent(self, agent_id: str, user_id: str = "default") -> bool:
        """Delete an agent"""
        try:
            # Remove from active agents
            if agent_id in self.agents:
                del self.agents[agent_id]
            
            # Remove from memory
            await self.memory_manager.delete_agent(agent_id, user_id)
            
            logger.info(f"Deleted agent: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete agent: {e}")
            return False
    
    async def cleanup(self):
        """Clean up agent manager"""
        logger.info("Cleaning up Agent Manager...")
        self.agents.clear()
        logger.info("Agent Manager cleanup completed")
