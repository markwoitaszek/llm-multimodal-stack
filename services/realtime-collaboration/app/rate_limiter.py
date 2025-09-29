"""
Rate Limiter for WebSocket connections and API requests
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests: int
    window: int  # seconds
    burst: int = 0  # additional requests allowed in burst

@dataclass
class RateLimitEntry:
    """Rate limit entry for tracking requests"""
    requests: deque = field(default_factory=deque)
    last_request: Optional[datetime] = None
    burst_count: int = 0
    blocked_until: Optional[datetime] = None

class RateLimiter:
    """Rate limiter for WebSocket connections and API requests"""
    
    def __init__(self):
        self.limits: Dict[str, RateLimit] = {}
        self.entries: Dict[str, RateLimitEntry] = {}
        self.lock = asyncio.Lock()
        
        # Default rate limits
        self.default_limits = {
            "websocket": RateLimit(requests=100, window=60, burst=20),
            "api": RateLimit(requests=1000, window=3600, burst=100),
            "agent_execution": RateLimit(requests=10, window=60, burst=5),
            "workspace_update": RateLimit(requests=50, window=60, burst=10),
            "user_notification": RateLimit(requests=20, window=60, burst=5)
        }
    
    async def initialize(self):
        """Initialize the rate limiter"""
        logger.info("Rate limiter initialized")
        
        # Set default limits
        for limit_type, limit in self.default_limits.items():
            await self.set_rate_limit(limit_type, limit)
    
    async def set_rate_limit(self, limit_type: str, limit: RateLimit) -> bool:
        """Set rate limit for a specific type"""
        try:
            async with self.lock:
                self.limits[limit_type] = limit
                logger.info(f"Set rate limit for {limit_type}: {limit.requests} requests per {limit.window} seconds")
                return True
        except Exception as e:
            logger.error(f"Failed to set rate limit for {limit_type}: {e}")
            return False
    
    async def get_rate_limit(self, limit_type: str) -> Optional[RateLimit]:
        """Get rate limit for a specific type"""
        return self.limits.get(limit_type)
    
    async def check_rate_limit(self, identifier: str, limit_type: str = "websocket") -> bool:
        """Check if a request is within rate limits"""
        try:
            async with self.lock:
                # Get rate limit configuration
                limit = self.limits.get(limit_type)
                if not limit:
                    logger.warning(f"No rate limit configured for {limit_type}")
                    return True
                
                # Get or create rate limit entry
                key = f"{limit_type}:{identifier}"
                if key not in self.entries:
                    self.entries[key] = RateLimitEntry()
                
                entry = self.entries[key]
                current_time = datetime.utcnow()
                
                # Check if currently blocked
                if entry.blocked_until and current_time < entry.blocked_until:
                    logger.warning(f"Rate limit exceeded for {identifier} ({limit_type}), blocked until {entry.blocked_until}")
                    return False
                
                # Clean up old requests outside the window
                cutoff_time = current_time - timedelta(seconds=limit.window)
                while entry.requests and entry.requests[0] < cutoff_time:
                    entry.requests.popleft()
                
                # Check if within rate limit
                if len(entry.requests) < limit.requests:
                    # Within normal rate limit
                    entry.requests.append(current_time)
                    entry.last_request = current_time
                    entry.burst_count = 0
                    return True
                
                # Check burst limit
                if limit.burst > 0 and entry.burst_count < limit.burst:
                    # Within burst limit
                    entry.requests.append(current_time)
                    entry.last_request = current_time
                    entry.burst_count += 1
                    return True
                
                # Rate limit exceeded
                entry.blocked_until = current_time + timedelta(seconds=limit.window)
                logger.warning(f"Rate limit exceeded for {identifier} ({limit_type}), blocking for {limit.window} seconds")
                return False
                
        except Exception as e:
            logger.error(f"Error checking rate limit for {identifier}: {e}")
            return True  # Allow request on error
    
    async def get_rate_limit_status(self, identifier: str, limit_type: str = "websocket") -> Dict[str, Any]:
        """Get rate limit status for an identifier"""
        try:
            async with self.lock:
                limit = self.limits.get(limit_type)
                if not limit:
                    return {"error": f"No rate limit configured for {limit_type}"}
                
                key = f"{limit_type}:{identifier}"
                entry = self.entries.get(key)
                
                if not entry:
                    return {
                        "identifier": identifier,
                        "limit_type": limit_type,
                        "requests_used": 0,
                        "requests_limit": limit.requests,
                        "burst_used": 0,
                        "burst_limit": limit.burst,
                        "window_seconds": limit.window,
                        "blocked_until": None,
                        "reset_time": None
                    }
                
                current_time = datetime.utcnow()
                
                # Clean up old requests
                cutoff_time = current_time - timedelta(seconds=limit.window)
                while entry.requests and entry.requests[0] < cutoff_time:
                    entry.requests.popleft()
                
                # Calculate reset time
                reset_time = None
                if entry.requests:
                    reset_time = entry.requests[0] + timedelta(seconds=limit.window)
                
                return {
                    "identifier": identifier,
                    "limit_type": limit_type,
                    "requests_used": len(entry.requests),
                    "requests_limit": limit.requests,
                    "burst_used": entry.burst_count,
                    "burst_limit": limit.burst,
                    "window_seconds": limit.window,
                    "blocked_until": entry.blocked_until.isoformat() if entry.blocked_until else None,
                    "reset_time": reset_time.isoformat() if reset_time else None,
                    "last_request": entry.last_request.isoformat() if entry.last_request else None
                }
                
        except Exception as e:
            logger.error(f"Error getting rate limit status for {identifier}: {e}")
            return {"error": str(e)}
    
    async def reset_rate_limit(self, identifier: str, limit_type: str = "websocket") -> bool:
        """Reset rate limit for an identifier"""
        try:
            async with self.lock:
                key = f"{limit_type}:{identifier}"
                if key in self.entries:
                    del self.entries[key]
                    logger.info(f"Reset rate limit for {identifier} ({limit_type})")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to reset rate limit for {identifier}: {e}")
            return False
    
    async def cleanup_expired_entries(self) -> int:
        """Clean up expired rate limit entries"""
        try:
            async with self.lock:
                current_time = datetime.utcnow()
                expired_keys = []
                
                for key, entry in self.entries.items():
                    # Check if entry is expired (no requests in the last 2 hours)
                    if entry.last_request:
                        time_since_last = (current_time - entry.last_request).total_seconds()
                        if time_since_last > 7200:  # 2 hours
                            expired_keys.append(key)
                    
                    # Check if blocked period has expired
                    if entry.blocked_until and current_time > entry.blocked_until:
                        entry.blocked_until = None
                
                # Remove expired entries
                for key in expired_keys:
                    del self.entries[key]
                
                if expired_keys:
                    logger.info(f"Cleaned up {len(expired_keys)} expired rate limit entries")
                
                return len(expired_keys)
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired rate limit entries: {e}")
            return 0
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        try:
            async with self.lock:
                total_entries = len(self.entries)
                total_limits = len(self.limits)
                
                # Count entries by type
                entries_by_type = defaultdict(int)
                blocked_entries = 0
                
                for key, entry in self.entries.items():
                    limit_type = key.split(":", 1)[0]
                    entries_by_type[limit_type] += 1
                    
                    if entry.blocked_until and datetime.utcnow() < entry.blocked_until:
                        blocked_entries += 1
                
                return {
                    "total_entries": total_entries,
                    "total_limits": total_limits,
                    "blocked_entries": blocked_entries,
                    "entries_by_type": dict(entries_by_type),
                    "configured_limits": {
                        limit_type: {
                            "requests": limit.requests,
                            "window": limit.window,
                            "burst": limit.burst
                        }
                        for limit_type, limit in self.limits.items()
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get rate limiter statistics: {e}")
            return {}
    
    async def is_blocked(self, identifier: str, limit_type: str = "websocket") -> bool:
        """Check if an identifier is currently blocked"""
        try:
            async with self.lock:
                key = f"{limit_type}:{identifier}"
                entry = self.entries.get(key)
                
                if not entry or not entry.blocked_until:
                    return False
                
                return datetime.utcnow() < entry.blocked_until
                
        except Exception as e:
            logger.error(f"Error checking if {identifier} is blocked: {e}")
            return False
    
    async def get_blocked_identifiers(self) -> Dict[str, Any]:
        """Get all currently blocked identifiers"""
        try:
            async with self.lock:
                blocked = {}
                current_time = datetime.utcnow()
                
                for key, entry in self.entries.items():
                    if entry.blocked_until and current_time < entry.blocked_until:
                        limit_type, identifier = key.split(":", 1)
                        blocked[key] = {
                            "identifier": identifier,
                            "limit_type": limit_type,
                            "blocked_until": entry.blocked_until.isoformat(),
                            "remaining_seconds": (entry.blocked_until - current_time).total_seconds()
                        }
                
                return blocked
                
        except Exception as e:
            logger.error(f"Failed to get blocked identifiers: {e}")
            return {}
    
    async def unblock_identifier(self, identifier: str, limit_type: str = "websocket") -> bool:
        """Manually unblock an identifier"""
        try:
            async with self.lock:
                key = f"{limit_type}:{identifier}"
                if key in self.entries:
                    self.entries[key].blocked_until = None
                    logger.info(f"Manually unblocked {identifier} ({limit_type})")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to unblock {identifier}: {e}")
            return False