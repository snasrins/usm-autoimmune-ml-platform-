"""
Audit Logging Middleware
Automatically logs all API requests for compliance and security
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import time
from typing import Optional

from app.core.database import SessionLocal
from app.models.audit_log import AuditLog
from app.core.security import decode_token


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Audit logging middleware
    Logs all API requests with user context, timing, and response status
    """
    
    # Endpoints to skip (to avoid log spam)
    SKIP_PATHS = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico"
    ]
    
    # Sensitive endpoints that should always be logged
    SENSITIVE_PATHS = [
        "/api/v1/admin/",
        "/api/v1/ml/training/",
        "/api/v1/upload/",
        "/api/v1/patients/",
        "/api/v1/flexible/import/"
    ]
    
    # Data access endpoints (require detailed logging)
    DATA_ACCESS_PATHS = [
        "/api/v1/patients/",
        "/api/v1/flexible/preview/",
        "/api/v1/ml/predictions/"
    ]
    
    async def dispatch(self, request: Request, call_next):
        """Log each request"""
        
        # Skip non-logged paths
        if any(request.url.path.startswith(skip) for skip in self.SKIP_PATHS):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Extract user info from JWT token
        user_id = None
        username = None
        user_role = None
        
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = decode_token(token)
                user_id = payload.get("user_id")
                username = payload.get("sub")
                # Role would need to be fetched from DB or included in token
            except Exception:
                pass
        
        # Get client IP
        client_ip = request.client.host
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Determine if this should be logged
        is_sensitive = any(request.url.path.startswith(path) for path in self.SENSITIVE_PATHS)
        is_data_access = any(request.url.path.startswith(path) for path in self.DATA_ACCESS_PATHS)
        
        # Log to database (async)
        if is_sensitive or is_data_access or response.status_code >= 400:
            db = None
            try:
                # Create audit log entry
                db = SessionLocal()
                
                # Determine action
                action = self.determine_action(request.method, request.url.path, response.status_code)
                
                # Determine resource type
                resource_type = self.determine_resource_type(request.url.path)
                
                audit_log = AuditLog(
                    user_id=user_id,
                    username=username or "anonymous",
                    user_role=user_role,
                    action=action,
                    resource_type=resource_type,
                    endpoint=request.url.path,
                    http_method=request.method,
                    ip_address=client_ip,
                    user_agent=request.headers.get("user-agent"),
                    response_status=response.status_code,
                    response_time_ms=response_time_ms,
                    is_sensitive=is_sensitive,
                    success=response.status_code < 400
                )
                
                db.add(audit_log)
                db.commit()
            except Exception as e:
                # Don't fail the request if logging fails
                if db:
                    db.rollback()
                print(f"[AUDIT] Failed to log request: {e}")
            finally:
                if db:
                    db.close()
        
        return response
    
    def determine_action(self, method: str, path: str, status_code: int) -> str:
        """Determine action type from request"""
        if "login" in path:
            return "USER_LOGIN" if status_code < 400 else "USER_LOGIN_FAILED"
        elif "logout" in path:
            return "USER_LOGOUT"
        elif "/ml/training/" in path:
            return "MODEL_TRAIN"
        elif "/ml/predictions/" in path:
            if method == "POST":
                return "PREDICTION_CREATE"
            else:
                return "PREDICTION_ACCESS"
        elif "/patients/" in path:
            if method == "GET":
                return "DATA_ACCESS"
            elif method in ["POST", "PUT", "PATCH"]:
                return "DATA_MODIFY"
            elif method == "DELETE":
                return "DATA_DELETE"
        elif "/upload/" in path:
            return "DATA_UPLOAD"
        elif "/api_keys" in path or "/keys" in path:
            if method == "POST":
                return "API_KEY_CREATE"
            elif method == "DELETE":
                return "API_KEY_REVOKE"
            else:
                return "API_KEY_ACCESS"
        else:
            return f"{method}_REQUEST"
    
    def determine_resource_type(self, path: str) -> Optional[str]:
        """Determine resource type from path"""
        if "/patients/" in path:
            return "patient"
        elif "/ml/training/" in path:
            return "training_job"
        elif "/ml/predictions/" in path:
            return "prediction"
        elif "/upload/" in path:
            return "upload"
        elif "/api_keys" in path or "/keys" in path:
            return "api_key"
        elif "/users/" in path or "/admin/users" in path:
            return "user"
        else:
            return None
