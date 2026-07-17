import re
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger("repolens.analyzer.db_detector")


class DatabaseDetector:
    @staticmethod
    def detect_models(filepath: str, file_content: str) -> List[Dict[str, Any]]:
        """
        Identify ORM models inside source files.
        Supports:
            - SQLAlchemy (Python)
            - Django ORM (Python)
            - Prisma Schema (prisma files)
            - TypeORM / Mongoose (JS/TS)
        """
        detected_models = []
        
        # 1. Prisma Schemas: schema.prisma
        if filepath.endswith(".prisma"):
            # Match block: model Name { fields }
            model_pattern = r'model\s+(\w+)\s*{([^}]*)}'
            for match in re.finditer(model_pattern, file_content):
                model_name = match.group(1)
                body = match.group(2)
                
                fields = []
                relations = []
                for line in body.splitlines():
                    line = line.strip()
                    if not line or line.startswith("//") or line.startswith("@@"):
                        continue
                    # Match name type [attributes]
                    parts = line.split()
                    if len(parts) >= 2:
                        f_name = parts[0]
                        f_type = parts[1]
                        attrs = " ".join(parts[2:]) if len(parts) > 2 else ""
                        
                        if "@relation" in attrs:
                            relations.append({
                                "field": f_name,
                                "target_model": f_type.replace("[]", ""),
                                "details": attrs
                            })
                        else:
                            fields.append({
                                "name": f_name,
                                "type": f_type,
                                "is_primary": "@id" in attrs,
                                "is_nullable": "?" in f_type
                            })
                            
                detected_models.append({
                    "model_name": model_name,
                    "fields": fields,
                    "relationships": relations
                })
            return detected_models

        # 2. Django Models: e.g. class User(models.Model)
        # 3. SQLAlchemy Models: e.g. class User(Base)
        if filepath.endswith(".py"):
            # Matches class Declarations
            class_pattern = r'class\s+(\w+)\s*\(([^)]+)\):'
            lines = file_content.splitlines()
            
            for match in re.finditer(class_pattern, file_content):
                model_name = match.group(1)
                bases_str = match.group(2)
                
                # Check base class suffix matches SQLAlchemy or Django ORM indicators
                is_orm = any(b.strip() in ["Base", "models.Model", "DeclarativeBase"] or "models" in b for b in bases_str.split(","))
                if not is_orm:
                    # Alternative check: does it contain Column or mapped_column declarations in body?
                    char_idx = match.end()
                    body_lines = file_content[char_idx:].splitlines()[:15]
                    is_orm = any("Column(" in l or "mapped_column(" in l or "relationship(" in l for l in body_lines)
                
                if is_orm:
                    fields = []
                    relations = []
                    char_idx = match.end()
                    body_lines = file_content[char_idx:].splitlines()
                    
                    # Gather model attributes until next class definition or end of block indentation
                    for line in body_lines:
                        # Break if out of block indentation (non-empty line starting with no spaces)
                        if line and not line.startswith(" ") and not line.startswith("\t") and not line.startswith("#"):
                            break
                        
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                            
                        # Matches: name = Column(...) or name: Mapped[...] = mapped_column(...) or name = models.CharField(...)
                        # Match relation: name = relationship(...) or name: Mapped[...] = relationship(...)
                        if "relationship(" in line:
                            rel_match = re.search(r'(\w+)\s*(?::\s*[\w\["\]]+)?\s*=\s*relationship\(\s*[\'"]?(\w+)[\'"]?', line)
                            if rel_match:
                                relations.append({
                                    "field": rel_match.group(1),
                                    "target_model": rel_match.group(2)
                                })
                        elif "=" in line:
                            parts = line.split("=")
                            var_part = parts[0].strip()
                            var_name = var_part.split(":")[0].strip()
                            
                            val_part = "=".join(parts[1:]).strip()
                            if any(ind in val_part for ind in ["Column", "mapped_column", "models."]):
                                is_pk = "primary_key=True" in val_part or "models.AutoField" in val_part
                                f_type = "string"
                                if "Integer" in val_part or "BigInteger" in val_part:
                                    f_type = "integer"
                                elif "DateTime" in val_part:
                                    f_type = "datetime"
                                elif "Boolean" in val_part:
                                    f_type = "boolean"
                                    
                                fields.append({
                                    "name": var_name,
                                    "type": f_type,
                                    "is_primary": is_pk,
                                    "is_nullable": "nullable=True" in val_part
                                })
                                
                    detected_models.append({
                        "model_name": model_name,
                        "fields": fields,
                        "relationships": relations
                    })

        # 4. TypeScript TypeORM or Mongoose schemas: class Name { ... }
        if filepath.endswith((".js", ".jsx", ".ts", ".tsx")):
            # Look for TypeORM @Entity() classes
            if "@Entity" in file_content or "@Schema" in file_content or "mongoose.model" in file_content:
                # Basic name extractor
                class_pattern = r'class\s+(\w+)'
                for match in re.finditer(class_pattern, file_content):
                    model_name = match.group(1)
                    fields = []
                    
                    # Estimate fields looking for @Column decorators
                    char_idx = match.end()
                    body_lines = file_content[char_idx:].splitlines()[:30]
                    
                    for idx, line in enumerate(body_lines):
                        line = line.strip()
                        if "@Column" in line or "@Primary" in line:
                            # Search name in next line
                            if idx + 1 < len(body_lines):
                                next_line = body_lines[idx+1].strip()
                                f_match = re.search(r'(\w+)\s*(?::|;)', next_line)
                                if f_match:
                                    fields.append({
                                        "name": f_match.group(1),
                                        "type": "any",
                                        "is_primary": "@Primary" in line,
                                        "is_nullable": True
                                    })
                                    
                    detected_models.append({
                        "model_name": model_name,
                        "fields": fields,
                        "relationships": []
                    })

        return detected_models
