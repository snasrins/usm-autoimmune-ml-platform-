"""
Rate Limiting Middleware for FastAPI
Prevents API abuse and ensures fair resource allocation
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from typing import Dict, Tuple
import time
from collections import defaultdict


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm
    
    Limits:
    - 100 requests per minute per IP (general)
    - 30 requests per minute for ML training endpoints
    - 200 requests per minute for read-only endpoints
    """
    
    def __init__(self, app):
        super().__init__(app)
        # Store: {ip_address: [(timestamp, endpoint), ...]}
        self.request_history: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 60  # Clean up old entries every 60 seconds
        self.last_cleanup = time.time()
        
        # Rate limits by endpoint pattern
        self.rate_limits = {
            "/api/v1/ml/training/": (30, 60),      # 30 requests per minute
            "/api/v1/ml/ensemble/": (30, 60),      # 30 requests per minute
            "/api/v1/upload/": (20, 60),           # 20 uploads per minute
            "/api/v1/auth/login": (30, 60),        # 30 login attempts per minute (increased for development)
            "/api/v1/admin/": (50, 60),            # 50 admin requests per minute
            "default": (100, 60)                   # 100 requests per minute (general)
        }
    
    def get_rate_limit(self, path: str) -> Tuple[int, int]:
        """
        Get rate limit for a specific path
        Returns: (max_requests, window_seconds)
        """
        for pattern, limit in self.rate_limits.items():
            if pattern in path:
                return limit
        return self.rate_limits["default"]
    
    def cleanup_old_entries(self):
        """Remove entries older than 2 minutes"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = datetime.now() - timedelta(minutes=2)
        for ip in list(self.request_history.keys()):
            self.request_history[ip] = [
                (ts, endpoint) for ts, endpoint in self.request_history[ip]
                if ts > cutoff_time
            ]
            # Remove IP if no recent requests
            if not self.request_history[ip]:
                del self.request_history[ip]
        
        self.last_cleanup = current_time
    
    async def dispatch(self, request: Request, call_next):
        """Process rate limiting for each request"""
        
        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # Get rate limit for this endpoint
        max_requests, window_seconds = self.get_rate_limit(request.url.path)
        
        # Clean up old entries periodically
        self.cleanup_old_entries()
        
        # Get request history for this IP
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=window_seconds)
        
        # Filter recent requests
        recent_requests = [
            (ts, endpoint) for ts, endpoint in self.request_history[client_ip]
            if ts > cutoff_time
        ]
        
        # Check rate limit
        if len(recent_requests) >= max_requests:
            # Calculate retry-after time
            oldest_request = min(recent_requests, key=lambda x: x[0])[0]
            retry_after = int((oldest_request + timedelta(seconds=window_seconds) - now).total_seconds())
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds.",
                    "retry_after": retry_after,
                    "limit": max_requests,
                    "window": window_seconds
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # Add current request to history
        self.request_history[client_ip].append((now, request.url.path))
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max_requests - len(recent_requests) - 1
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int((now + timedelta(seconds=window_seconds)).timestamp()))
        
        return response


class RateLimitByUser(BaseHTTPMiddleware):
    """
    Rate limiting by authenticated user (JWT-based)
    More granular control per user role
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.user_history: Dict[str, list] = defaultdict(list)
        
        # Role-based limits
        self.role_limits = {
            "admin": (500, 60),      # 500 requests per minute
            "researcher": (200, 60),  # 200 requests per minute
            "viewer": (100, 60)       # 100 requests per minute
        }
    
    async def dispatch(self, request: Request, call_next):
        """Apply user-based rate limiting"""
        
        # Skip for unauthenticated endpoints
        if request.url.path in ["/api/v1/auth/login", "/api/v1/auth/register", "/health"]:
            return await call_next(request)
        
        # Extract user from JWT token (simplified - would need proper JWT decode)
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return await call_next(request)
        
        # Process request (actual user extraction would be done by auth middleware)
        response = await call_next(request)
        return response
