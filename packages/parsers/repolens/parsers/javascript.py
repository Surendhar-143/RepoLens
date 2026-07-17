import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("repolens.parsers.javascript")


class JavaScriptParser:
    @staticmethod
    def parse_code(code_content: str) -> Dict[str, Any]:
        """
        Parse JS/TS files to extract imports, classes, functions, and lines of code.
        """
        result = {
            "classes": [],
            "functions": [],
            "imports": [],
            "loc": len(code_content.splitlines())
        }

        # 1. Parsing Imports
        # import { Symbol1, Symbol2 } from "module";
        # import Symbol from "module";
        # import * as Symbol from "module";
        # const x = require("module");
        import_regexes = [
            # ES6 imports
            r'(?:import)\s+(?:type\s+)?(?:[\w*\s{},]*)\s+(?:from)\s+[\'"]([^\'"]+)[\'"]',
            # Require imports
            r'(?:const|let|var)\s+(?:[\w\s{},]*)\s*=\s*require\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        ]
        
        seen_imports = set()
        for regex in import_regexes:
            for match in re.finditer(regex, code_content):
                source = match.group(1)
                if source in seen_imports:
                    continue
                seen_imports.add(source)
                
                is_ext = not (source.startswith(".") or source.startswith("/") or source.startswith("@/"))
                result["imports"].append({
                    "source": source,
                    "symbols": [],  # Optional detail
                    "is_external": is_ext
                })

        # 2. Parsing Classes
        # class ClassName [extends Parent]
        class_regex = r'(?:export\s+)?(?:default\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?'
        lines = code_content.splitlines()
        
        for match in re.finditer(class_regex, code_content):
            name = match.group(1)
            parent = match.group(2)
            
            # Estimate lines by finding open brace to next match or end of block
            char_index = match.start()
            line_no = code_content[:char_index].count('\n') + 1
            
            snippet = ""
            try:
                snippet = "\n".join(lines[line_no - 1 : line_no + 15])
            except Exception:
                pass

            result["classes"].append({
                "name": name,
                "kind": "class",
                "line_start": line_no,
                "line_end": line_no + 5, # Estimated length fallback
                "inheritance": [parent] if parent else [],
                "decorators": [],
                "docstring": "",
                "code_snippet": snippet[:1500] if snippet else ""
            })

        # 3. Parsing Functions & Methods
        # function name(params)
        # const name = (params) =>
        # async function name(params)
        function_regexes = [
            # Standard function
            r'(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)',
            # Arrow functions
            r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>'
        ]

        seen_funcs = set()
        for regex in function_regexes:
            for match in re.finditer(regex, code_content):
                name = match.group(1)
                if name in seen_funcs or name in ["if", "for", "while", "switch", "catch"]:
                    continue
                seen_funcs.add(name)
                
                params_str = match.group(2)
                params = [{"name": p.strip().split(":")[0].strip(), "type": "any"} for p in params_str.split(",") if p.strip()]

                char_index = match.start()
                line_no = code_content[:char_index].count('\n') + 1
                
                snippet = ""
                try:
                    snippet = "\n".join(lines[line_no - 1 : line_no + 10])
                except Exception:
                    pass

                result["functions"].append({
                    "name": name,
                    "kind": "function",
                    "line_start": line_no,
                    "line_end": line_no + 4,
                    "parameters": params,
                    "return_type": "any",
                    "decorators": [],
                    "docstring": "",
                    "code_snippet": snippet[:1500] if snippet else ""
                })

        return result
