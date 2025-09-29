"""
Message Queue for reliable message delivery and persistence
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class MessageStatus(Enum):
    """Message status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class QueuedMessage:
    """Queued message structure"""
    id: str
    type: str
    data: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    retry_after: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MessageHandler:
    """Message handler configuration"""
    message_type: str
    handler_func: Callable
    priority: MessagePriority = MessagePriority.NORMAL
    max_retries: int = 3
    retry_delay: int = 5  # seconds

class MessageQueue:
    """Message queue for reliable message delivery"""
    
    def __init__(self):
        self.queue: List[QueuedMessage] = []
        self.handlers: Dict[str, MessageHandler] = {}
        self.processing_messages: Set[str] = set()
        self.completed_messages: List[QueuedMessage] = []
        self.failed_messages: List[QueuedMessage] = []
        self.lock = asyncio.Lock()
        self.processing = False
        self.max_queue_size = 10000
        self.max_retention_hours = 24
    
    async def initialize(self):
        """Initialize the message queue"""
        logger.info("Message queue initialized")
        
        # Register default handlers
        await self._register_default_handlers()
    
    async def _register_default_handlers(self):
        """Register default message handlers"""
        # Agent execution handler
        await self.register_handler(
            "agent_execution",
            self._handle_agent_execution,
            MessagePriority.HIGH
        )
        
        # Workspace update handler
        await self.register_handler(
            "workspace_update",
            self._handle_workspace_update,
            MessagePriority.NORMAL
        )
        
        # User notification handler
        await self.register_handler(
            "user_notification",
            self._handle_user_notification,
            MessagePriority.NORMAL
        )
        
        # System event handler
        await self.register_handler(
            "system_event",
            self._handle_system_event,
            MessagePriority.LOW
        )
    
    async def register_handler(self, message_type: str, handler_func: Callable, priority: MessagePriority = MessagePriority.NORMAL, max_retries: int = 3, retry_delay: int = 5) -> bool:
        """Register a message handler"""
        try:
            handler = MessageHandler(
                message_type=message_type,
                handler_func=handler_func,
                priority=priority,
                max_retries=max_retries,
                retry_delay=retry_delay
            )
            
            self.handlers[message_type] = handler
            logger.info(f"Registered handler for message type: {message_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register handler for {message_type}: {e}")
            return False
    
    async def unregister_handler(self, message_type: str) -> bool:
        """Unregister a message handler"""
        try:
            if message_type in self.handlers:
                del self.handlers[message_type]
                logger.info(f"Unregistered handler for message type: {message_type}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to unregister handler for {message_type}: {e}")
            return False
    
    async def enqueue_message(self, message_type: str, data: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL, max_retries: int = 3, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Enqueue a message for processing"""
        try:
            async with self.lock:
                # Check queue size limit
                if len(self.queue) >= self.max_queue_size:
                    logger.warning("Message queue is full, dropping oldest message")
                    if self.queue:
                        self.queue.pop(0)
                
                # Create message
                message_id = str(uuid.uuid4())
                message = QueuedMessage(
                    id=message_id,
                    type=message_type,
                    data=data,
                    priority=priority,
                    max_retries=max_retries,
                    metadata=metadata or {}
                )
                
                # Insert message based on priority
                inserted = False
                for i, existing_message in enumerate(self.queue):
                    if message.priority.value > existing_message.priority.value:
                        self.queue.insert(i, message)
                        inserted = True
                        break
                
                if not inserted:
                    self.queue.append(message)
                
                logger.debug(f"Enqueued message {message_id} of type {message_type}")
                return message_id
                
        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            raise
    
    async def dequeue_message(self) -> Optional[QueuedMessage]:
        """Dequeue the next message for processing"""
        try:
            async with self.lock:
                if not self.queue:
                    return None
                
                # Find the next message to process
                for i, message in enumerate(self.queue):
                    # Check if message is ready for processing
                    if message.status == MessageStatus.PENDING:
                        if message.retry_after is None or datetime.utcnow() >= message.retry_after:
                            # Mark as processing and remove from queue
                            message.status = MessageStatus.PROCESSING
                            message.processed_at = datetime.utcnow()
                            self.processing_messages.add(message.id)
                            self.queue.pop(i)
                            return message
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to dequeue message: {e}")
            return None
    
    async def process_messages(self):
        """Process queued messages"""
        try:
            if self.processing:
                return
            
            self.processing = True
            
            # Process messages until queue is empty or no more messages are ready
            while True:
                message = await self.dequeue_message()
                if not message:
                    break
                
                await self._process_message(message)
            
            self.processing = False
            
        except Exception as e:
            logger.error(f"Error processing messages: {e}")
            self.processing = False
    
    async def _process_message(self, message: QueuedMessage):
        """Process a single message"""
        try:
            # Get handler for message type
            handler = self.handlers.get(message.type)
            if not handler:
                logger.warning(f"No handler found for message type: {message.type}")
                await self._mark_message_failed(message, "No handler found")
                return
            
            # Process message
            logger.debug(f"Processing message {message.id} of type {message.type}")
            result = await handler.handler_func(message.data)
            
            if result:
                await self._mark_message_completed(message)
            else:
                await self._handle_message_failure(message, handler)
                
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
            await self._handle_message_failure(message, self.handlers.get(message.type))
    
    async def _handle_message_failure(self, message: QueuedMessage, handler: Optional[MessageHandler]):
        """Handle message processing failure"""
        try:
            message.retry_count += 1
            
            if message.retry_count >= message.max_retries:
                # Max retries exceeded, mark as failed
                await self._mark_message_failed(message, f"Max retries exceeded ({message.max_retries})")
            else:
                # Schedule retry
                retry_delay = handler.retry_delay if handler else 5
                message.retry_after = datetime.utcnow() + timedelta(seconds=retry_delay)
                message.status = MessageStatus.RETRYING
                
                # Re-queue message
                async with self.lock:
                    self.queue.append(message)
                    self.processing_messages.discard(message.id)
                
                logger.warning(f"Message {message.id} failed, retrying in {retry_delay} seconds (attempt {message.retry_count}/{message.max_retries})")
                
        except Exception as e:
            logger.error(f"Error handling message failure: {e}")
    
    async def _mark_message_completed(self, message: QueuedMessage):
        """Mark message as completed"""
        try:
            message.status = MessageStatus.COMPLETED
            self.processing_messages.discard(message.id)
            
            # Add to completed messages
            self.completed_messages.append(message)
            
            # Keep only last 1000 completed messages
            if len(self.completed_messages) > 1000:
                self.completed_messages = self.completed_messages[-1000:]
            
            logger.debug(f"Message {message.id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error marking message as completed: {e}")
    
    async def _mark_message_failed(self, message: QueuedMessage, error: str):
        """Mark message as failed"""
        try:
            message.status = MessageStatus.FAILED
            message.metadata["error"] = error
            self.processing_messages.discard(message.id)
            
            # Add to failed messages
            self.failed_messages.append(message)
            
            # Keep only last 1000 failed messages
            if len(self.failed_messages) > 1000:
                self.failed_messages = self.failed_messages[-1000:]
            
            logger.error(f"Message {message.id} failed: {error}")
            
        except Exception as e:
            logger.error(f"Error marking message as failed: {e}")
    
    async def get_message_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get message status"""
        try:
            # Check in queue
            for message in self.queue:
                if message.id == message_id:
                    return {
                        "id": message.id,
                        "type": message.type,
                        "status": message.status.value,
                        "priority": message.priority.value,
                        "created_at": message.created_at.isoformat(),
                        "retry_count": message.retry_count,
                        "max_retries": message.max_retries,
                        "retry_after": message.retry_after.isoformat() if message.retry_after else None
                    }
            
            # Check in processing
            if message_id in self.processing_messages:
                return {
                    "id": message_id,
                    "status": "processing",
                    "processed_at": datetime.utcnow().isoformat()
                }
            
            # Check in completed
            for message in self.completed_messages:
                if message.id == message_id:
                    return {
                        "id": message.id,
                        "type": message.type,
                        "status": message.status.value,
                        "created_at": message.created_at.isoformat(),
                        "processed_at": message.processed_at.isoformat() if message.processed_at else None
                    }
            
            # Check in failed
            for message in self.failed_messages:
                if message.id == message_id:
                    return {
                        "id": message.id,
                        "type": message.type,
                        "status": message.status.value,
                        "created_at": message.created_at.isoformat(),
                        "processed_at": message.processed_at.isoformat() if message.processed_at else None,
                        "error": message.metadata.get("error")
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting message status: {e}")
            return None
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status information"""
        try:
            pending_count = sum(1 for msg in self.queue if msg.status == MessageStatus.PENDING)
            retrying_count = sum(1 for msg in self.queue if msg.status == MessageStatus.RETRYING)
            processing_count = len(self.processing_messages)
            completed_count = len(self.completed_messages)
            failed_count = len(self.failed_messages)
            
            # Get message type distribution
            type_distribution = {}
            for message in self.queue:
                msg_type = message.type
                type_distribution[msg_type] = type_distribution.get(msg_type, 0) + 1
            
            return {
                "queue_size": len(self.queue),
                "pending_count": pending_count,
                "retrying_count": retrying_count,
                "processing_count": processing_count,
                "completed_count": completed_count,
                "failed_count": failed_count,
                "type_distribution": type_distribution,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {}
    
    async def cleanup_old_messages(self):
        """Clean up old messages"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.max_retention_hours)
            
            # Clean up completed messages
            self.completed_messages = [
                msg for msg in self.completed_messages
                if msg.created_at > cutoff_time
            ]
            
            # Clean up failed messages
            self.failed_messages = [
                msg for msg in self.failed_messages
                if msg.created_at > cutoff_time
            ]
            
            logger.info("Cleaned up old messages")
            
        except Exception as e:
            logger.error(f"Error cleaning up old messages: {e}")
    
    # Default message handlers
    async def _handle_agent_execution(self, data: Dict[str, Any]) -> bool:
        """Handle agent execution messages"""
        try:
            logger.info(f"Handling agent execution: {data}")
            # In a real implementation, this would integrate with the agent monitor
            return True
        except Exception as e:
            logger.error(f"Error handling agent execution: {e}")
            return False
    
    async def _handle_workspace_update(self, data: Dict[str, Any]) -> bool:
        """Handle workspace update messages"""
        try:
            logger.info(f"Handling workspace update: {data}")
            # In a real implementation, this would integrate with the workspace manager
            return True
        except Exception as e:
            logger.error(f"Error handling workspace update: {e}")
            return False
    
    async def _handle_user_notification(self, data: Dict[str, Any]) -> bool:
        """Handle user notification messages"""
        try:
            logger.info(f"Handling user notification: {data}")
            # In a real implementation, this would send notifications to users
            return True
        except Exception as e:
            logger.error(f"Error handling user notification: {e}")
            return False
    
    async def _handle_system_event(self, data: Dict[str, Any]) -> bool:
        """Handle system event messages"""
        try:
            logger.info(f"Handling system event: {data}")
            # In a real implementation, this would handle system events
            return True
        except Exception as e:
            logger.error(f"Error handling system event: {e}")
            return False