#!/usr/bin/env python3
"""
API Gateway Management System
Part of Issue #54: Authentication & API Gateway Dependencies

This module provides comprehensive API gateway functionality including:
- Request routing and load balancing
- Rate limiting and throttling
- Authentication and authorization middleware
- Request/response transformation
- API versioning and routing
- Monitoring and analytics
- Circuit breaker pattern
"""

import asyncio
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from pathlib import Path
import aiohttp
import asyncio
from collections import defaultdict, deque
import statistics
import hashlib
import hmac

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RouteMethod(Enum):
    """HTTP method enumeration"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

class RateLimitType(Enum):
    """Rate limit type enumeration"""
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    PER_USER = "per_user"
    PER_IP = "per_ip"

class CircuitState(Enum):
    """Circuit breaker state enumeration"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class Route:
    """API route definition"""
    route_id: str
    path: str
    method: RouteMethod
    target_url: str
    enabled: bool = True
    timeout: int = 30
    retries: int = 3
    rate_limit: Optional[Dict[str, Any]] = None
    auth_required: bool = True
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    path_params: Dict[str, str] = field(default_factory=dict)
    middleware: List[str] = field(default_factory=list)

@dataclass
class RateLimit:
    """Rate limit configuration"""
    limit_id: str
    name: str
    limit_type: RateLimitType
    requests_per_period: int
    period_seconds: int
    burst_limit: int = 0
    enabled: bool = True

@dataclass
class CircuitBreaker:
    """Circuit breaker configuration"""
    breaker_id: str
    name: str
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[str] = None
    success_count: int = 0

@dataclass
class RequestLog:
    """Request log entry"""
    log_id: str
    route_id: str
    method: str
    path: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    request_time: str
    response_time: Optional[str] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None

@dataclass
class GatewayStats:
    """Gateway statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    circuit_breaker_trips: int = 0
    average_response_time: float = 0.0
    requests_per_minute: float = 0.0
    error_rate: float = 0.0

class APIGateway:
    """API Gateway implementation"""
    
    def __init__(self, data_dir: Path, auth_manager=None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Dependencies
        self.auth_manager = auth_manager
        
        # Storage
        self.routes: Dict[str, Route] = {}
        self.rate_limits: Dict[str, RateLimit] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.request_logs: List[RequestLog] = []
        self.stats = GatewayStats()
        
        # Rate limiting tracking
        self.rate_limit_tracker: Dict[str, deque] = defaultdict(lambda: deque())
        self.user_rate_limits: Dict[str, deque] = defaultdict(lambda: deque())
        self.ip_rate_limits: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Configuration files
        self.routes_file = self.data_dir / "routes.json"
        self.rate_limits_file = self.data_dir / "rate_limits.json"
        self.circuit_breakers_file = self.data_dir / "circuit_breakers.json"
        self.logs_file = self.data_dir / "request_logs.json"
        self.stats_file = self.data_dir / "gateway_stats.json"
        
        # Load existing data
        self._load_data()
        
        # Initialize default configurations
        self._initialize_defaults()
    
    def _load_data(self):
        """Load gateway data from files"""
        try:
            # Load routes
            if self.routes_file.exists():
                with open(self.routes_file, 'r') as f:
                    data = json.load(f)
                    for route_id, route_data in data.items():
                        route_data['method'] = RouteMethod(route_data['method'])
                        self.routes[route_id] = Route(**route_data)
            
            # Load rate limits
            if self.rate_limits_file.exists():
                with open(self.rate_limits_file, 'r') as f:
                    data = json.load(f)
                    for limit_id, limit_data in data.items():
                        limit_data['limit_type'] = RateLimitType(limit_data['limit_type'])
                        self.rate_limits[limit_id] = RateLimit(**limit_data)
            
            # Load circuit breakers
            if self.circuit_breakers_file.exists():
                with open(self.circuit_breakers_file, 'r') as f:
                    data = json.load(f)
                    for breaker_id, breaker_data in data.items():
                        breaker_data['state'] = CircuitState(breaker_data['state'])
                        self.circuit_breakers[breaker_id] = CircuitBreaker(**breaker_data)
            
            # Load request logs
            if self.logs_file.exists():
                with open(self.logs_file, 'r') as f:
                    data = json.load(f)
                    self.request_logs = [RequestLog(**log_data) for log_data in data]
            
            # Load stats
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    self.stats = GatewayStats(**data)
            
            logger.info(f"Loaded {len(self.routes)} routes, {len(self.rate_limits)} rate limits, {len(self.circuit_breakers)} circuit breakers")
            
        except Exception as e:
            logger.error(f"Error loading gateway data: {e}")
    
    def _save_data(self):
        """Save gateway data to files"""
        try:
            # Save routes
            routes_data = {}
            for route_id, route in self.routes.items():
                route_dict = asdict(route)
                route_dict['method'] = route.method.value
                routes_data[route_id] = route_dict
            
            with open(self.routes_file, 'w') as f:
                json.dump(routes_data, f, indent=2)
            
            # Save rate limits
            rate_limits_data = {}
            for limit_id, limit in self.rate_limits.items():
                limit_dict = asdict(limit)
                limit_dict['limit_type'] = limit.limit_type.value
                rate_limits_data[limit_id] = limit_dict
            
            with open(self.rate_limits_file, 'w') as f:
                json.dump(rate_limits_data, f, indent=2)
            
            # Save circuit breakers
            circuit_breakers_data = {}
            for breaker_id, breaker in self.circuit_breakers.items():
                breaker_dict = asdict(breaker)
                breaker_dict['state'] = breaker.state.value
                circuit_breakers_data[breaker_id] = breaker_dict
            
            with open(self.circuit_breakers_file, 'w') as f:
                json.dump(circuit_breakers_data, f, indent=2)
            
            # Save request logs
            logs_data = [asdict(log) for log in self.request_logs]
            with open(self.logs_file, 'w') as f:
                json.dump(logs_data, f, indent=2)
            
            # Save stats
            with open(self.stats_file, 'w') as f:
                json.dump(asdict(self.stats), f, indent=2)
            
            logger.info("Gateway data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving gateway data: {e}")
    
    def _initialize_defaults(self):
        """Initialize default configurations"""
        if not self.rate_limits:
            # Create default rate limits
            default_limits = [
                RateLimit(
                    "default-per-minute",
                    "Default Per Minute",
                    RateLimitType.PER_MINUTE,
                    100,
                    60
                ),
                RateLimit(
                    "default-per-hour",
                    "Default Per Hour",
                    RateLimitType.PER_HOUR,
                    1000,
                    3600
                ),
                RateLimit(
                    "default-per-user",
                    "Default Per User",
                    RateLimitType.PER_USER,
                    500,
                    3600
                )
            ]
            
            for limit in default_limits:
                self.rate_limits[limit.limit_id] = limit
        
        if not self.circuit_breakers:
            # Create default circuit breaker
            default_breaker = CircuitBreaker(
                "default-breaker",
                "Default Circuit Breaker",
                failure_threshold=5,
                recovery_timeout=60
            )
            
            self.circuit_breakers["default-breaker"] = default_breaker
        
        self._save_data()
    
    def create_route(
        self,
        route_id: str,
        path: str,
        method: RouteMethod,
        target_url: str,
        enabled: bool = True,
        timeout: int = 30,
        retries: int = 3,
        auth_required: bool = True,
        rate_limit_id: Optional[str] = None,
        headers: Dict[str, str] = None,
        middleware: List[str] = None
    ) -> Route:
        """Create a new route"""
        if route_id in self.routes:
            raise ValueError(f"Route {route_id} already exists")
        
        route = Route(
            route_id=route_id,
            path=path,
            method=method,
            target_url=target_url,
            enabled=enabled,
            timeout=timeout,
            retries=retries,
            auth_required=auth_required,
            headers=headers or {},
            middleware=middleware or []
        )
        
        if rate_limit_id and rate_limit_id in self.rate_limits:
            route.rate_limit = {"limit_id": rate_limit_id}
        
        self.routes[route_id] = route
        self._save_data()
        
        logger.info(f"Created route: {route_id}")
        return route
    
    def find_route(self, path: str, method: str) -> Optional[Route]:
        """Find route matching path and method"""
        method_enum = RouteMethod(method.upper())
        
        for route in self.routes.values():
            if not route.enabled:
                continue
            
            if route.method != method_enum:
                continue
            
            # Simple path matching (in production, use proper routing library)
            if self._match_path(route.path, path):
                return route
        
        return None
    
    def _match_path(self, route_path: str, request_path: str) -> bool:
        """Match route path with request path"""
        # Simple exact match (in production, support path parameters)
        return route_path == request_path
    
    async def handle_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        query_params: Dict[str, str],
        body: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: str = "",
        user_agent: str = ""
    ) -> Dict[str, Any]:
        """Handle incoming request"""
        start_time = time.time()
        
        # Find matching route
        route = self.find_route(path, method)
        if not route:
            return {
                "status_code": 404,
                "body": {"error": "Route not found"},
                "headers": {"Content-Type": "application/json"}
            }
        
        # Create request log
        request_log = RequestLog(
            log_id=str(uuid.uuid4()),
            route_id=route.route_id,
            method=method,
            path=path,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_time=datetime.now().isoformat()
        )
        
        try:
            # Check authentication
            if route.auth_required and not user_id:
                request_log.status_code = 401
                request_log.response_time = datetime.now().isoformat()
                request_log.error_message = "Authentication required"
                self._log_request(request_log)
                
                return {
                    "status_code": 401,
                    "body": {"error": "Authentication required"},
                    "headers": {"Content-Type": "application/json"}
                }
            
            # Check rate limiting
            if not await self._check_rate_limit(route, user_id, ip_address):
                request_log.status_code = 429
                request_log.response_time = datetime.now().isoformat()
                request_log.error_message = "Rate limit exceeded"
                self._log_request(request_log)
                
                return {
                    "status_code": 429,
                    "body": {"error": "Rate limit exceeded"},
                    "headers": {"Content-Type": "application/json"}
                }
            
            # Check circuit breaker
            if not await self._check_circuit_breaker(route):
                request_log.status_code = 503
                request_log.response_time = datetime.now().isoformat()
                request_log.error_message = "Service unavailable (circuit breaker open)"
                self._log_request(request_log)
                
                return {
                    "status_code": 503,
                    "body": {"error": "Service unavailable"},
                    "headers": {"Content-Type": "application/json"}
                }
            
            # Forward request to target
            response = await self._forward_request(route, method, path, headers, query_params, body)
            
            # Update request log
            request_log.status_code = response.get("status_code", 500)
            request_log.response_time = datetime.now().isoformat()
            request_log.response_time_ms = (time.time() - start_time) * 1000
            
            # Update circuit breaker
            await self._update_circuit_breaker(route, response.get("status_code", 500) < 500)
            
            # Update stats
            self._update_stats(response.get("status_code", 500), request_log.response_time_ms)
            
            self._log_request(request_log)
            
            return response
            
        except Exception as e:
            # Handle errors
            request_log.status_code = 500
            request_log.response_time = datetime.now().isoformat()
            request_log.response_time_ms = (time.time() - start_time) * 1000
            request_log.error_message = str(e)
            
            # Update circuit breaker
            await self._update_circuit_breaker(route, False)
            
            # Update stats
            self._update_stats(500, request_log.response_time_ms)
            
            self._log_request(request_log)
            
            logger.error(f"Request handling error: {e}")
            
            return {
                "status_code": 500,
                "body": {"error": "Internal server error"},
                "headers": {"Content-Type": "application/json"}
            }
    
    async def _check_rate_limit(self, route: Route, user_id: Optional[str], ip_address: str) -> bool:
        """Check rate limiting"""
        if not route.rate_limit:
            return True
        
        limit_id = route.rate_limit.get("limit_id")
        if not limit_id or limit_id not in self.rate_limits:
            return True
        
        rate_limit = self.rate_limits[limit_id]
        if not rate_limit.enabled:
            return True
        
        current_time = time.time()
        
        # Check different rate limit types
        if rate_limit.limit_type == RateLimitType.PER_USER and user_id:
            return self._check_user_rate_limit(user_id, rate_limit, current_time)
        elif rate_limit.limit_type == RateLimitType.PER_IP:
            return self._check_ip_rate_limit(ip_address, rate_limit, current_time)
        else:
            return self._check_global_rate_limit(rate_limit, current_time)
    
    def _check_user_rate_limit(self, user_id: str, rate_limit: RateLimit, current_time: float) -> bool:
        """Check user-specific rate limit"""
        user_requests = self.user_rate_limits[user_id]
        
        # Remove old requests
        while user_requests and current_time - user_requests[0] > rate_limit.period_seconds:
            user_requests.popleft()
        
        # Check if limit exceeded
        if len(user_requests) >= rate_limit.requests_per_period:
            return False
        
        # Add current request
        user_requests.append(current_time)
        return True
    
    def _check_ip_rate_limit(self, ip_address: str, rate_limit: RateLimit, current_time: float) -> bool:
        """Check IP-specific rate limit"""
        ip_requests = self.ip_rate_limits[ip_address]
        
        # Remove old requests
        while ip_requests and current_time - ip_requests[0] > rate_limit.period_seconds:
            ip_requests.popleft()
        
        # Check if limit exceeded
        if len(ip_requests) >= rate_limit.requests_per_period:
            return False
        
        # Add current request
        ip_requests.append(current_time)
        return True
    
    def _check_global_rate_limit(self, rate_limit: RateLimit, current_time: float) -> bool:
        """Check global rate limit"""
        global_requests = self.rate_limit_tracker[rate_limit.limit_id]
        
        # Remove old requests
        while global_requests and current_time - global_requests[0] > rate_limit.period_seconds:
            global_requests.popleft()
        
        # Check if limit exceeded
        if len(global_requests) >= rate_limit.requests_per_period:
            return False
        
        # Add current request
        global_requests.append(current_time)
        return True
    
    async def _check_circuit_breaker(self, route: Route) -> bool:
        """Check circuit breaker state"""
        # Use default circuit breaker for now
        breaker = self.circuit_breakers.get("default-breaker")
        if not breaker:
            return True
        
        if breaker.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if breaker.last_failure_time:
                last_failure = datetime.fromisoformat(breaker.last_failure_time)
                if datetime.now() - last_failure > timedelta(seconds=breaker.recovery_timeout):
                    breaker.state = CircuitState.HALF_OPEN
                    breaker.success_count = 0
                    self._save_data()
                    return True
            return False
        
        return True
    
    async def _update_circuit_breaker(self, route: Route, success: bool):
        """Update circuit breaker state"""
        breaker = self.circuit_breakers.get("default-breaker")
        if not breaker:
            return
        
        if success:
            breaker.success_count += 1
            if breaker.state == CircuitState.HALF_OPEN and breaker.success_count >= breaker.half_open_max_calls:
                breaker.state = CircuitState.CLOSED
                breaker.failure_count = 0
                breaker.success_count = 0
        else:
            breaker.failure_count += 1
            breaker.last_failure_time = datetime.now().isoformat()
            
            if breaker.failure_count >= breaker.failure_threshold:
                breaker.state = CircuitState.OPEN
                breaker.success_count = 0
                self.stats.circuit_breaker_trips += 1
        
        self._save_data()
    
    async def _forward_request(
        self,
        route: Route,
        method: str,
        path: str,
        headers: Dict[str, str],
        query_params: Dict[str, str],
        body: Optional[str]
    ) -> Dict[str, Any]:
        """Forward request to target service"""
        # Prepare target URL
        target_url = route.target_url + path
        
        # Add query parameters
        if query_params:
            query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
            target_url += f"?{query_string}"
        
        # Prepare headers
        forward_headers = route.headers.copy()
        forward_headers.update(headers)
        
        # Remove host header to avoid conflicts
        forward_headers.pop("host", None)
        
        # Make request to target service
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=route.timeout)) as session:
            try:
                async with session.request(
                    method=method,
                    url=target_url,
                    headers=forward_headers,
                    data=body
                ) as response:
                    response_body = await response.text()
                    
                    return {
                        "status_code": response.status,
                        "body": response_body,
                        "headers": dict(response.headers)
                    }
                    
            except asyncio.TimeoutError:
                return {
                    "status_code": 504,
                    "body": {"error": "Gateway timeout"},
                    "headers": {"Content-Type": "application/json"}
                }
            except Exception as e:
                logger.error(f"Request forwarding error: {e}")
                return {
                    "status_code": 502,
                    "body": {"error": "Bad gateway"},
                    "headers": {"Content-Type": "application/json"}
                }
    
    def _log_request(self, request_log: RequestLog):
        """Log request"""
        self.request_logs.append(request_log)
        
        # Keep only last 10000 logs
        if len(self.request_logs) > 10000:
            self.request_logs = self.request_logs[-10000:]
        
        self._save_data()
    
    def _update_stats(self, status_code: int, response_time_ms: float):
        """Update gateway statistics"""
        self.stats.total_requests += 1
        
        if status_code < 400:
            self.stats.successful_requests += 1
        elif status_code == 429:
            self.stats.rate_limited_requests += 1
        else:
            self.stats.failed_requests += 1
        
        # Update average response time
        if self.stats.total_requests == 1:
            self.stats.average_response_time = response_time_ms
        else:
            self.stats.average_response_time = (
                (self.stats.average_response_time * (self.stats.total_requests - 1) + response_time_ms) /
                self.stats.total_requests
            )
        
        # Update error rate
        self.stats.error_rate = (self.stats.failed_requests / self.stats.total_requests) * 100
        
        self._save_data()
    
    def create_rate_limit(
        self,
        limit_id: str,
        name: str,
        limit_type: RateLimitType,
        requests_per_period: int,
        period_seconds: int,
        burst_limit: int = 0
    ) -> RateLimit:
        """Create a new rate limit"""
        if limit_id in self.rate_limits:
            raise ValueError(f"Rate limit {limit_id} already exists")
        
        rate_limit = RateLimit(
            limit_id=limit_id,
            name=name,
            limit_type=limit_type,
            requests_per_period=requests_per_period,
            period_seconds=period_seconds,
            burst_limit=burst_limit
        )
        
        self.rate_limits[limit_id] = rate_limit
        self._save_data()
        
        logger.info(f"Created rate limit: {limit_id}")
        return rate_limit
    
    def create_circuit_breaker(
        self,
        breaker_id: str,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ) -> CircuitBreaker:
        """Create a new circuit breaker"""
        if breaker_id in self.circuit_breakers:
            raise ValueError(f"Circuit breaker {breaker_id} already exists")
        
        circuit_breaker = CircuitBreaker(
            breaker_id=breaker_id,
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            half_open_max_calls=half_open_max_calls
        )
        
        self.circuit_breakers[breaker_id] = circuit_breaker
        self._save_data()
        
        logger.info(f"Created circuit breaker: {breaker_id}")
        return circuit_breaker
    
    def get_route(self, route_id: str) -> Optional[Route]:
        """Get route by ID"""
        return self.routes.get(route_id)
    
    def list_routes(self, enabled_only: bool = False) -> List[Route]:
        """List routes"""
        routes = list(self.routes.values())
        
        if enabled_only:
            routes = [r for r in routes if r.enabled]
        
        return routes
    
    def update_route(self, route_id: str, **kwargs) -> Optional[Route]:
        """Update route"""
        if route_id not in self.routes:
            return None
        
        route = self.routes[route_id]
        
        # Update allowed fields
        allowed_fields = ['enabled', 'timeout', 'retries', 'auth_required', 'headers', 'middleware']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(route, field, value)
        
        self._save_data()
        return route
    
    def delete_route(self, route_id: str) -> bool:
        """Delete route"""
        if route_id not in self.routes:
            return False
        
        del self.routes[route_id]
        self._save_data()
        
        logger.info(f"Deleted route: {route_id}")
        return True
    
    def get_request_logs(
        self,
        route_id: Optional[str] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[RequestLog]:
        """Get request logs with optional filtering"""
        logs = self.request_logs.copy()
        
        if route_id:
            logs = [log for log in logs if log.route_id == route_id]
        
        if user_id:
            logs = [log for log in logs if log.user_id == user_id]
        
        if start_time:
            logs = [log for log in logs if datetime.fromisoformat(log.request_time) >= start_time]
        
        if end_time:
            logs = [log for log in logs if datetime.fromisoformat(log.request_time) <= end_time]
        
        # Sort by request time (newest first)
        logs.sort(key=lambda log: log.request_time, reverse=True)
        
        return logs[:limit]
    
    def get_gateway_stats(self) -> GatewayStats:
        """Get gateway statistics"""
        return self.stats
    
    def get_route_stats(self, route_id: str, period_hours: int = 24) -> Dict[str, Any]:
        """Get statistics for a specific route"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=period_hours)
        
        logs = self.get_request_logs(route_id=route_id, start_time=start_time, end_time=end_time)
        
        if not logs:
            return {"total_requests": 0}
        
        total_requests = len(logs)
        successful_requests = len([log for log in logs if log.status_code and log.status_code < 400])
        failed_requests = total_requests - successful_requests
        
        response_times = [log.response_time_ms for log in logs if log.response_time_ms is not None]
        
        stats = {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": (successful_requests / total_requests) * 100 if total_requests > 0 else 0,
            "error_rate": (failed_requests / total_requests) * 100 if total_requests > 0 else 0
        }
        
        if response_times:
            stats.update({
                "average_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "median_response_time": statistics.median(response_times)
            })
        
        return stats

async def main():
    """Main function to demonstrate API gateway"""
    data_dir = Path("./gateway_data")
    gateway = APIGateway(data_dir)
    
    # Create a route
    route = gateway.create_route(
        "api-users",
        "/api/users",
        RouteMethod.GET,
        "http://localhost:8001",
        rate_limit_id="default-per-minute"
    )
    
    print(f"Created route: {route.route_id}")
    
    # Handle a request
    response = await gateway.handle_request(
        "GET",
        "/api/users",
        {"Authorization": "Bearer token123"},
        {},
        user_id="user123",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0"
    )
    
    print(f"Response: {response}")
    
    # Get gateway stats
    stats = gateway.get_gateway_stats()
    print(f"Gateway stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())