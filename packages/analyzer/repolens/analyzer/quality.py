import re
from typing import List, Dict, Any, Tuple


class CodeQualityAnalyzer:
    # Common hardcoded patterns triggers
    SECRET_PATTERN = re.compile(
        r'(jwt_secret|api_key|password|secret_key|aws_access|db_password|private_key)\s*=\s*["\'][a-zA-Z0-9_\-\.]{8,}["\']',
        re.IGNORECASE
    )

    @classmethod
    def evaluate(
        cls,
        files: List[Dict[str, Any]],
        symbols: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        """
        Evaluate codebase static metrics to detect vulnerabilities or smells.
        Returns a list of findings and score breakdowns.
        """
        findings = []
        quality_score = 100.0
        security_score = 100.0
        architecture_score = 100.0

        # 1. Check Code Quality smells (e.g. God classes / large methods)
        for sym in symbols:
            line_start = sym.get("line_start", 0)
            line_end = sym.get("line_end", 0)
            lines_count = line_end - line_start + 1
            
            if sym.get("kind") == "class" and lines_count > 300:
                findings.append({
                    "rule_name": "god_class_smell",
                    "category": "quality",
                    "severity": "warning",
                    "target_id": sym.get("name", "Class"),
                    "title": "God Class Complexity Smell",
                    "description": f"Class '{sym.get('name')}' exceeds 300 lines ({lines_count} lines). Consider refactoring.",
                    "evidence": {"lines": lines_count, "file_path": sym.get("file_path")}
                })
                quality_score = max(quality_score - 4.0, 40.0)

            elif sym.get("kind") == "function" and lines_count > 60:
                findings.append({
                    "rule_name": "long_method_smell",
                    "category": "quality",
                    "severity": "info",
                    "target_id": sym.get("name", "Function"),
                    "title": "Long Method Code Smell",
                    "description": f"Method '{sym.get('name')}' exceeds 60 lines ({lines_count} lines).",
                    "evidence": {"lines": lines_count, "file_path": sym.get("file_path")}
                })
                quality_score = max(quality_score - 1.0, 50.0)

        # 2. Check Security Vulnerabilities (e.g. Hardcoded secrets)
        for f in files:
            content = f.get("content", "")
            if not content:
                continue

            matches = cls.SECRET_PATTERN.findall(content)
            for match in matches:
                findings.append({
                    "rule_name": "hardcoded_secrets",
                    "category": "security",
                    "severity": "critical",
                    "target_id": f.get("name", "File"),
                    "title": "Hardcoded Cryptographic Secret Leak",
                    "description": f"File '{f.get('name')}' contains hardcoded credentials pattern match: '{match}'.",
                    "evidence": {"file_path": f.get("path")}
                })
                security_score = max(security_score - 15.0, 20.0)

        # 3. Check Architecture Smells (Circular dependencies)
        circular_loops = 0
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            
            # Simple reciprocal check for imports cycles
            reciprocal = any(e for e in edges if e.get("source") == tgt and e.get("target") == src)
            if reciprocal:
                circular_loops += 1
                findings.append({
                    "rule_name": "circular_import_smell",
                    "category": "architecture",
                    "severity": "warning",
                    "target_id": f"{src}<->{tgt}",
                    "title": "Circular Package Reference Smell",
                    "description": f"Loop detected: import coupling between modules '{src}' and '{tgt}'.",
                    "evidence": {"source": src, "target": tgt}
                })
                architecture_score = max(architecture_score - 8.0, 30.0)

        # Compute average overall score
        overall = round((quality_score + security_score + architecture_score) / 3, 1)

        scores = {
            "overall": overall,
            "quality": round(quality_score, 1),
            "security": round(security_score, 1),
            "architecture": round(architecture_score, 1)
        }
        return findings, scores
