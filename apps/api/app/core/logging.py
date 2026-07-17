import logging
import sys
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json

# Setup standard formatting or JSON formatting based on environment
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Merge extra attributes if any
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)
            
        return json.dumps(log_data)


def setup_logging(env: str = "development") -> None:
    root_logger = logging.getLogger()
    
    # Clear handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler(sys.stdout)
    
    if env == "production":
        formatter = JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%SZ")
        root_logger.setLevel(logging.INFO)
    else:
        # Structured but human-readable in development
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        root_logger.setLevel(logging.DEBUG)
        
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Silence verbose logs from external packages unless necessary
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        logger = logging.getLogger("repolens.api.request")
        start_time = time.perf_counter()
        
        # Log request incoming
        logger.info(f"Incoming request: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time
            logger.info(
                f"Completed request: {request.method} {request.url.path} - Status: {response.status_code} - Duration: {process_time:.4f}s",
                extra={
                    "extra": {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration": process_time
                    }
                }
            )
            return response
        except Exception as e:
            process_time = time.perf_counter() - start_time
            logger.error(
                f"Failed request: {request.method} {request.url.path} - Error: {str(e)} - Duration: {process_time:.4f}s",
                exc_info=True,
                extra={
                    "extra": {
                        "method": request.method,
                        "path": request.url.path,
                        "duration": process_time
                    }
                }
            )
            raise e
