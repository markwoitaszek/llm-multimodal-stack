"""
Agent Monitor for tracking agent executions and broadcasting updates
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AgentExecution:
    """Agent execution information"""
    id: str
    agent_id: str
    task: str
    user_id: str
    status: AgentStatus
    progress: int = 0
    current_step: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentInfo:
    """Agent information"""
    agent_id: str
    name: str
    status: AgentStatus = AgentStatus.IDLE
    current_execution: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.utcnow)
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_execution_time: float = 0.0
    subscribers: Set[str] = field(default_factory=set)

class AgentMonitor:
    """Monitors agent executions and broadcasts updates"""
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self.executions: Dict[str, AgentExecution] = {}
        self.agent_subscribers: Dict[str, Set[str]] = {}  # agent_id -> connection_ids
        self.user_subscribers: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.execution_history: List[AgentExecution] = []
        self.lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the agent monitor"""
        logger.info("Agent monitor initialized")
        
        # Initialize default agents
        await self._initialize_default_agents()
    
    async def _initialize_default_agents(self):
        """Initialize default agents"""
        default_agents = [
            {
                "agent_id": "research-assistant",
                "name": "Research Assistant",
                "status": AgentStatus.IDLE
            },
            {
                "agent_id": "content-creator",
                "name": "Content Creator",
                "status": AgentStatus.IDLE
            },
            {
                "agent_id": "customer-support",
                "name": "Customer Support",
                "status": AgentStatus.IDLE
            },
            {
                "agent_id": "data-analyst",
                "name": "Data Analyst",
                "status": AgentStatus.IDLE
            }
        ]
        
        for agent_data in default_agents:
            agent = AgentInfo(
                agent_id=agent_data["agent_id"],
                name=agent_data["name"],
                status=agent_data["status"]
            )
            await self.add_agent(agent)
    
    async def add_agent(self, agent: AgentInfo) -> bool:
        """Add an agent to monitoring"""
        try:
            async with self.lock:
                self.agents[agent.agent_id] = agent
                self.agent_subscribers[agent.agent_id] = set()
                logger.info(f"Added agent to monitoring: {agent.name} ({agent.agent_id})")
                return True
        except Exception as e:
            logger.error(f"Failed to add agent {agent.agent_id}: {e}")
            return False
    
    async def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from monitoring"""
        try:
            async with self.lock:
                if agent_id in self.agents:
                    del self.agents[agent_id]
                
                if agent_id in self.agent_subscribers:
                    del self.agent_subscribers[agent_id]
                
                logger.info(f"Removed agent from monitoring: {agent_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to remove agent {agent_id}: {e}")
            return False
    
    async def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent information"""
        return self.agents.get(agent_id)
    
    async def get_all_agents(self) -> List[AgentInfo]:
        """Get all agents"""
        return list(self.agents.values())
    
    async def get_agent_count(self) -> int:
        """Get the number of monitored agents"""
        return len(self.agents)
    
    async def start_execution(self, agent_id: str, task: str, user_id: str, connection_id: Optional[str] = None) -> Optional[str]:
        """Start an agent execution"""
        try:
            async with self.lock:
                if agent_id not in self.agents:
                    logger.error(f"Agent {agent_id} not found")
                    return None
                
                agent = self.agents[agent_id]
                
                # Check if agent is already running
                if agent.status == AgentStatus.RUNNING:
                    logger.warning(f"Agent {agent_id} is already running")
                    return None
                
                # Create execution
                execution_id = str(uuid.uuid4())
                execution = AgentExecution(
                    id=execution_id,
                    agent_id=agent_id,
                    task=task,
                    user_id=user_id,
                    status=AgentStatus.RUNNING
                )
                
                self.executions[execution_id] = execution
                
                # Update agent status
                agent.status = AgentStatus.RUNNING
                agent.current_execution = execution_id
                agent.last_activity = datetime.utcnow()
                agent.execution_count += 1
                
                # Log execution start
                logger.info(f"Started execution {execution_id} for agent {agent_id}: {task}")
                
                # Broadcast execution start
                await self._broadcast_execution_update(execution, "execution_started")
                
                return execution_id
                
        except Exception as e:
            logger.error(f"Failed to start execution for agent {agent_id}: {e}")
            return None
    
    async def update_execution(self, execution_id: str, updates: Dict[str, Any]) -> bool:
        """Update an execution"""
        try:
            async with self.lock:
                if execution_id not in self.executions:
                    return False
                
                execution = self.executions[execution_id]
                
                # Update fields
                if "progress" in updates:
                    execution.progress = updates["progress"]
                if "current_step" in updates:
                    execution.current_step = updates["current_step"]
                if "status" in updates:
                    execution.status = AgentStatus(updates["status"])
                if "result" in updates:
                    execution.result = updates["result"]
                if "error" in updates:
                    execution.error = updates["error"]
                if "metadata" in updates:
                    execution.metadata.update(updates["metadata"])
                
                # Update agent status
                if execution.agent_id in self.agents:
                    agent = self.agents[execution.agent_id]
                    agent.status = execution.status
                    agent.last_activity = datetime.utcnow()
                
                # Broadcast update
                await self._broadcast_execution_update(execution, "execution_updated")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to update execution {execution_id}: {e}")
            return False
    
    async def complete_execution(self, execution_id: str, result: Optional[str] = None, error: Optional[str] = None) -> bool:
        """Complete an execution"""
        try:
            async with self.lock:
                if execution_id not in self.executions:
                    return False
                
                execution = self.executions[execution_id]
                
                # Update execution
                execution.completed_at = datetime.utcnow()
                execution.execution_time = (execution.completed_at - execution.started_at).total_seconds()
                
                if error:
                    execution.status = AgentStatus.FAILED
                    execution.error = error
                else:
                    execution.status = AgentStatus.COMPLETED
                    execution.result = result
                    execution.progress = 100
                
                # Update agent statistics
                if execution.agent_id in self.agents:
                    agent = self.agents[execution.agent_id]
                    agent.status = AgentStatus.IDLE
                    agent.current_execution = None
                    agent.last_activity = datetime.utcnow()
                    agent.total_execution_time += execution.execution_time or 0
                    
                    if execution.status == AgentStatus.COMPLETED:
                        agent.success_count += 1
                    else:
                        agent.failure_count += 1
                
                # Add to history
                self.execution_history.append(execution)
                
                # Keep only last 1000 executions
                if len(self.execution_history) > 1000:
                    self.execution_history = self.execution_history[-1000:]
                
                # Broadcast completion
                await self._broadcast_execution_update(execution, "execution_completed")
                
                # Remove from active executions
                del self.executions[execution_id]
                
                logger.info(f"Completed execution {execution_id} for agent {execution.agent_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to complete execution {execution_id}: {e}")
            return False
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an execution"""
        try:
            async with self.lock:
                if execution_id not in self.executions:
                    return False
                
                execution = self.executions[execution_id]
                execution.status = AgentStatus.CANCELLED
                execution.completed_at = datetime.utcnow()
                execution.execution_time = (execution.completed_at - execution.started_at).total_seconds()
                
                # Update agent status
                if execution.agent_id in self.agents:
                    agent = self.agents[execution.agent_id]
                    agent.status = AgentStatus.IDLE
                    agent.current_execution = None
                    agent.last_activity = datetime.utcnow()
                
                # Broadcast cancellation
                await self._broadcast_execution_update(execution, "execution_cancelled")
                
                # Remove from active executions
                del self.executions[execution_id]
                
                logger.info(f"Cancelled execution {execution_id} for agent {execution.agent_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to cancel execution {execution_id}: {e}")
            return False
    
    async def get_execution(self, execution_id: str) -> Optional[AgentExecution]:
        """Get execution information"""
        return self.executions.get(execution_id)
    
    async def get_agent_executions(self, agent_id: str) -> List[AgentExecution]:
        """Get all executions for an agent"""
        executions = []
        for execution in self.executions.values():
            if execution.agent_id == agent_id:
                executions.append(execution)
        return executions
    
    async def get_user_executions(self, user_id: str) -> List[AgentExecution]:
        """Get all executions for a user"""
        executions = []
        for execution in self.executions.values():
            if execution.user_id == user_id:
                executions.append(execution)
        return executions
    
    async def get_execution_history(self, limit: int = 100) -> List[AgentExecution]:
        """Get execution history"""
        # Sort by completion time (newest first) and limit
        history = sorted(self.execution_history, key=lambda x: x.completed_at or x.started_at, reverse=True)
        return history[:limit]
    
    async def subscribe_connection(self, agent_id: str, connection_id: str) -> bool:
        """Subscribe a connection to agent updates"""
        try:
            async with self.lock:
                if agent_id not in self.agent_subscribers:
                    self.agent_subscribers[agent_id] = set()
                
                self.agent_subscribers[agent_id].add(connection_id)
                
                # Also add to agent's subscribers
                if agent_id in self.agents:
                    self.agents[agent_id].subscribers.add(connection_id)
                
                logger.info(f"Connection {connection_id} subscribed to agent {agent_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to subscribe connection {connection_id} to agent {agent_id}: {e}")
            return False
    
    async def unsubscribe_connection(self, agent_id: str, connection_id: str) -> bool:
        """Unsubscribe a connection from agent updates"""
        try:
            async with self.lock:
                if agent_id in self.agent_subscribers:
                    self.agent_subscribers[agent_id].discard(connection_id)
                
                # Also remove from agent's subscribers
                if agent_id in self.agents:
                    self.agents[agent_id].subscribers.discard(connection_id)
                
                logger.info(f"Connection {connection_id} unsubscribed from agent {agent_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to unsubscribe connection {connection_id} from agent {agent_id}: {e}")
            return False
    
    async def subscribe_user(self, agent_id: str, user_id: str) -> bool:
        """Subscribe a user to agent updates"""
        try:
            async with self.lock:
                if user_id not in self.user_subscribers:
                    self.user_subscribers[user_id] = set()
                
                self.user_subscribers[user_id].add(agent_id)
                
                logger.info(f"User {user_id} subscribed to agent {agent_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to subscribe user {user_id} to agent {agent_id}: {e}")
            return False
    
    async def unsubscribe_user(self, agent_id: str, user_id: str) -> bool:
        """Unsubscribe a user from agent updates"""
        try:
            async with self.lock:
                if user_id in self.user_subscribers:
                    self.user_subscribers[user_id].discard(agent_id)
                
                logger.info(f"User {user_id} unsubscribed from agent {agent_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to unsubscribe user {user_id} from agent {agent_id}: {e}")
            return False
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent status information"""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        current_execution = None
        
        if agent.current_execution and agent.current_execution in self.executions:
            execution = self.executions[agent.current_execution]
            current_execution = {
                "id": execution.id,
                "task": execution.task,
                "user_id": execution.user_id,
                "status": execution.status.value,
                "progress": execution.progress,
                "current_step": execution.current_step,
                "started_at": execution.started_at.isoformat()
            }
        
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "status": agent.status.value,
            "current_execution": current_execution,
            "last_activity": agent.last_activity.isoformat(),
            "execution_count": agent.execution_count,
            "success_count": agent.success_count,
            "failure_count": agent.failure_count,
            "success_rate": (agent.success_count / agent.execution_count * 100) if agent.execution_count > 0 else 0,
            "total_execution_time": agent.total_execution_time,
            "avg_execution_time": (agent.total_execution_time / agent.execution_count) if agent.execution_count > 0 else 0,
            "subscribers": len(agent.subscribers)
        }
    
    async def check_agent_status(self):
        """Check agent status and handle timeouts"""
        try:
            current_time = datetime.utcnow()
            timeout_executions = []
            
            for execution_id, execution in self.executions.items():
                # Check for timeout (5 minutes)
                time_since_start = (current_time - execution.started_at).total_seconds()
                if time_since_start > 300:  # 5 minutes
                    timeout_executions.append(execution_id)
            
            # Cancel timeout executions
            for execution_id in timeout_executions:
                await self.cancel_execution(execution_id)
                logger.warning(f"Cancelled timeout execution: {execution_id}")
                
        except Exception as e:
            logger.error(f"Error checking agent status: {e}")
    
    async def _broadcast_execution_update(self, execution: AgentExecution, update_type: str):
        """Broadcast execution update to subscribers"""
        try:
            # This would integrate with the WebSocket manager to broadcast updates
            # For now, we'll just log the update
            logger.info(f"Broadcasting {update_type} for execution {execution.id}")
            
            # In a real implementation, this would:
            # 1. Get all subscribers for the agent
            # 2. Send the update via WebSocket
            # 3. Handle delivery failures
            
        except Exception as e:
            logger.error(f"Failed to broadcast execution update: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get agent monitoring statistics"""
        total_agents = len(self.agents)
        active_executions = len(self.executions)
        total_executions = len(self.execution_history)
        
        # Calculate success rate
        successful_executions = sum(1 for exec in self.execution_history if exec.status == AgentStatus.COMPLETED)
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        # Calculate average execution time
        total_time = sum(exec.execution_time or 0 for exec in self.execution_history)
        avg_execution_time = (total_time / total_executions) if total_executions > 0 else 0
        
        # Get status distribution
        status_distribution = {}
        for agent in self.agents.values():
            status = agent.status.value
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        return {
            "total_agents": total_agents,
            "active_executions": active_executions,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": round(success_rate, 2),
            "avg_execution_time": round(avg_execution_time, 2),
            "status_distribution": status_distribution,
            "timestamp": datetime.utcnow().isoformat()
        }