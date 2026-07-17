import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("repolens.analyzer.api_detector")


class APIDetector:
    @staticmethod
    def detect_apis(filepath: str, file_content: str) -> List[Dict[str, Any]]:
        """
        Scan a source file's contents for API routing declarations.
        Supports:
            - FastAPI / Flask / Django REST
            - Express / NestJS / Koa
        """
        detected_routes = []
        
        # 1. FastAPI / Flask decorators: e.g., @router.get("/path") or @app.post("/path")
        # Matches: @(router|app|api|route|blueprint).(get|post|put|delete|patch|options)("/path"...)
        py_api_pattern = r'@(?:router|app|api|route|blueprint)\.(get|post|put|delete|patch|options)\(\s*[\'"]([^\'"]+)[\'"]'
        
        # Check python imports or decorators
        if filepath.endswith(".py"):
            lines = file_content.splitlines()
            for match in re.finditer(py_api_pattern, file_content):
                method = match.group(1).upper()
                route = match.group(2)
                
                # Try to find corresponding function name on next lines
                char_idx = match.end()
                lines_after = file_content[char_idx:].splitlines()[:5]
                func_name = None
                for line in lines_after:
                    func_match = re.search(r'async\s+def\s+(\w+)|def\s+(\w+)', line)
                    if func_match:
                        func_name = func_match.group(1) or func_match.group(2)
                        break
                        
                detected_routes.append({
                    "route": route,
                    "method": method,
                    "parameters": [], # Resolved via functional specs in pipelines
                    "controller_func": func_name
                })

        # 2. JS / TS Express Router patterns: e.g., router.get('/path', ...) or app.post('/path', ...)
        # Matches: (router|app|api|route).(get|post|put|delete|patch)\(\s*[\'"]([^\'"]+)[\'"]
        js_api_pattern = r'\b(?:router|app|api|route)\.(get|post|put|delete|patch)\(\s*[\'"]([^\'"]+)[\'"]'
        
        # NestJS decorators: @Get('/path') or @Post('/path')
        nest_api_pattern = r'@(?:Get|Post|Put|Delete|Patch)\(\s*[\'"]([^\'"]+)[\'"]\)'

        if filepath.endswith((".js", ".jsx", ".ts", ".tsx")):
            # Express check
            for match in re.finditer(js_api_pattern, file_content):
                method = match.group(1).upper()
                route = match.group(2)
                detected_routes.append({
                    "route": route,
                    "method": method,
                    "parameters": [],
                    "controller_func": None
                })
            # NestJS check
            for match in re.finditer(nest_api_pattern, file_content):
                # Retrieve method from decorator name
                decorator = re.search(r'@(\w+)', match.group(0)).group(1)
                method = decorator.upper()
                if method == "GET" or method == "POST" or method == "PUT" or method == "DELETE" or method == "PATCH":
                    route = match.group(1)
                    detected_routes.append({
                        "route": route,
                        "method": method,
                        "parameters": [],
                        "controller_func": None
                    })

        return detected_routes
