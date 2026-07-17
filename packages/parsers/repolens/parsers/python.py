import ast
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("repolens.parsers.python")


class PythonASTParser:
    @staticmethod
    def _get_docstring(node: ast.AST) -> str | None:
        doc = ast.get_docstring(node)
        return doc.strip() if doc else None

    @classmethod
    def _parse_function_params(cls, arguments: ast.arguments) -> List[Dict[str, Any]]:
        params = []
        # Standard positional-only + positional-or-keyword + keyword-only arguments
        all_args = []
        if hasattr(arguments, "posonlyargs"):
            all_args.extend(arguments.posonlyargs)
        all_args.extend(arguments.args)
        all_args.extend(arguments.kwonlyargs)
        
        for arg in all_args:
            arg_type = None
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    arg_type = arg.annotation.id
                elif isinstance(arg.annotation, ast.Constant):
                    arg_type = str(arg.annotation.value)
                else:
                    try:
                        arg_type = ast.unparse(arg.annotation)
                    except Exception:
                        arg_type = "unknown"
            params.append({
                "name": arg.arg,
                "type": arg_type or "any"
            })
            
        if arguments.vararg:
            params.append({"name": f"*{arguments.vararg.arg}", "type": "any"})
        if arguments.kwarg:
            params.append({"name": f"**{arguments.kwarg.arg}", "type": "any"})
            
        return params

    @classmethod
    def _get_return_type(cls, returns: ast.expr | None) -> str | None:
        if not returns:
            return None
        try:
            return ast.unparse(returns)
        except Exception:
            return "unknown"

    @classmethod
    def _get_decorators(cls, decorator_list: List[ast.expr]) -> List[str]:
        decorators = []
        for dec in decorator_list:
            try:
                decorators.append(ast.unparse(dec))
            except Exception:
                pass
        return decorators

    @classmethod
    def parse_code(cls, code_content: str) -> Dict[str, Any]:
        """
        Parse python code string and retrieve class/function metadata and imports.
        """
        result = {
            "classes": [],
            "functions": [],
            "imports": [],
            "loc": len(code_content.splitlines())
        }
        
        try:
            tree = ast.parse(code_content)
        except SyntaxError as e:
            logger.warning(f"Syntax error during Python parse: {str(e)}")
            return result

        for node in ast.walk(tree):
            # 1. Classes
            if isinstance(node, ast.ClassDef):
                bases = []
                for base in node.bases:
                    try:
                        bases.append(ast.unparse(base))
                    except Exception:
                        pass
                
                # Fetch snippet
                snippet = ""
                try:
                    lines = code_content.splitlines()
                    snippet = "\n".join(lines[node.lineno - 1 : node.end_lineno])
                except Exception:
                    pass

                result["classes"].append({
                    "name": node.name,
                    "kind": "class",
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "inheritance": bases,
                    "decorators": cls._get_decorators(node.decorator_list),
                    "docstring": cls._get_docstring(node),
                    "code_snippet": snippet[:1500] if snippet else ""
                })

            # 2. Functions (Global functions only, methods inside classes will be nested or resolved)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # We extract both global functions and class methods.
                # Determine if nested or a method
                # (Simple parent search can be done, but for metadata we extract all functions)
                snippet = ""
                try:
                    lines = code_content.splitlines()
                    snippet = "\n".join(lines[node.lineno - 1 : node.end_lineno])
                except Exception:
                    pass

                result["functions"].append({
                    "name": node.name,
                    "kind": "function",
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "parameters": cls._parse_function_params(node.args),
                    "return_type": cls._get_return_type(node.returns),
                    "decorators": cls._get_decorators(node.decorator_list),
                    "docstring": cls._get_docstring(node),
                    "code_snippet": snippet[:1500] if snippet else ""
                })

            # 3. Imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append({
                        "source": alias.name,
                        "symbols": [alias.asname or alias.name],
                        "is_external": not (alias.name.startswith(".") or alias.name.split(".")[0] in ["app", "packages"])
                    })
            elif isinstance(node, sa_type := ast.ImportFrom):
                symbols = [alias.asname or alias.name for alias in node.names]
                source = node.module or ""
                # Mapped dot relative imports
                if node.level > 0:
                    source = "." * node.level + source
                
                is_ext = not (source.startswith(".") or source.split(".")[0] in ["app", "packages"])
                result["imports"].append({
                    "source": source,
                    "symbols": symbols,
                    "is_external": is_ext
                })

        return result
