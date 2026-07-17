import os
import json
import logging
from typing import List, Dict, Set, Any

logger = logging.getLogger("repolens.analyzer.languages")

# Suffix map
EXTENSION_TO_LANGUAGE = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".kt": "Kotlin",
    ".html": "HTML",
    ".css": "CSS",
    ".sql": "SQL",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".sh": "Shell",
    ".md": "Markdown"
}


class LanguageDetector:
    @staticmethod
    def detect(files: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate repository file sizes and counts by language.
        """
        stats = {}
        for f in files:
            _, ext = os.path.splitext(f["name"])
            lang = EXTENSION_TO_LANGUAGE.get(ext.lower())
            if not lang:
                continue
                
            if lang not in stats:
                stats[lang] = {"size": 0, "files_count": 0}
                
            stats[lang]["size"] += f["size"]
            stats[lang]["files_count"] += 1
            
        # Normalize to percentages
        total_size = sum(s["size"] for s in stats.values())
        for lang in stats:
            if total_size > 0:
                stats[lang]["percentage"] = round((stats[lang]["size"] / total_size) * 100, 2)
            else:
                stats[lang]["percentage"] = 0.0
                
        return stats


class FrameworkDetector:
    @staticmethod
    def detect(root_path: str, files: List[Dict[str, Any]]) -> List[str]:
        """
        Deterministic audit of frameworks.
        """
        detected = set()
        dependencies = set()
        
        # 1. Package files inspection
        package_json_path = os.path.join(root_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    for d in deps:
                        dependencies.add(d.lower())
            except Exception as e:
                logger.warning(f"Error parsing package.json: {str(e)}")

        requirements_path = os.path.join(root_path, "requirements.txt")
        if os.path.exists(requirements_path):
            try:
                with open(requirements_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip().lower()
                        if line and not line.startswith("#"):
                            # Strip version specs e.g. fastapi==0.100.0
                            name = line.split("=")[0].split(">")[0].split("<")[0].strip()
                            dependencies.add(name)
            except Exception as e:
                logger.warning(f"Error parsing requirements.txt: {str(e)}")

        pyproject_path = os.path.join(root_path, "pyproject.toml")
        if os.path.exists(pyproject_path):
            try:
                with open(pyproject_path, "r", encoding="utf-8") as f:
                    content = f.read().lower()
                    # Check packages names indicators in string
                    for item in ["fastapi", "django", "flask", "frappe"]:
                        if item in content:
                            dependencies.add(item)
            except Exception:
                pass

        # 2. Map dependencies to Framework signatures
        # JS frameworks
        if "react" in dependencies:
            detected.add("React")
        if "next" in dependencies:
            detected.add("Next.js")
        if "vue" in dependencies:
            detected.add("Vue")
        if "@angular/core" in dependencies:
            detected.add("Angular")
        if "express" in dependencies:
            detected.add("Express")
        if "@nestjs/core" in dependencies:
            detected.add("NestJS")
            
        # Python frameworks
        if "fastapi" in dependencies:
            detected.add("FastAPI")
        if "django" in dependencies:
            detected.add("Django")
        if "flask" in dependencies:
            detected.add("Flask")
        if "frappe" in dependencies:
            detected.add("Frappe")

        # 3. Code patterns fallbacks (checking physical files presence or contents)
        # Next.js indicator
        if not "Next.js" in detected:
            if any(f["name"] in ["next.config.js", "next.config.ts"] for f in files):
                detected.add("Next.js")
                
        # Django indicator
        if not "Django" in detected:
            if any(f["name"] == "manage.py" for f in files):
                detected.add("Django")
                
        # Spring boot indicator
        pom_xml_path = os.path.join(root_path, "pom.xml")
        gradle_path = os.path.join(root_path, "build.gradle")
        if os.path.exists(pom_xml_path):
            try:
                with open(pom_xml_path, "r", encoding="utf-8") as f:
                    if "spring-boot" in f.read().lower():
                        detected.add("Spring Boot")
            except Exception:
                pass
        if os.path.exists(gradle_path):
            try:
                with open(gradle_path, "r", encoding="utf-8") as f:
                    if "spring-boot" in f.read().lower():
                        detected.add("Spring Boot")
            except Exception:
                pass

        # Laravel / Rails
        composer_json = os.path.join(root_path, "composer.json")
        if os.path.exists(composer_json):
            try:
                with open(composer_json, "r") as f:
                    if "laravel" in f.read().lower():
                        detected.add("Laravel")
            except Exception:
                pass

        gemfile = os.path.join(root_path, "Gemfile")
        if os.path.exists(gemfile):
            try:
                with open(gemfile, "r") as f:
                    if "rails" in f.read().lower():
                        detected.add("Ruby on Rails")
            except Exception:
                pass

        return list(detected)
