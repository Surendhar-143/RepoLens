import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.database.models import User, Repository, File, Symbol, GraphEdge, Rule, Finding, HealthScore
from app.core.exceptions import NotFoundError
from repolens.analyzer.quality import CodeQualityAnalyzer

router = APIRouter(prefix="/quality", tags=["Code Quality & Security Intelligence"])
logger = logging.getLogger("repolens.routes.quality")


@router.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_codebase_quality(
    repository_id: uuid.UUID = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Scan codebase for code smells, architectural loops, and cryptographic secret leaks"""
    repo_query = await db.execute(
        select(Repository).where(
            Repository.id == repository_id,
            Repository.user_id == current_user.id
        )
    )
    repo = repo_query.scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repository")

    # Load context data
    files_query = await db.execute(select(File).where(File.repository_id == repository_id))
    files_list = [{"name": f.name, "path": f.path, "content": f.content} for f in files_query.scalars().all()]

    symbols_query = await db.execute(select(Symbol).where(Symbol.repository_id == repository_id))
    symbols_list = [{"name": s.name, "kind": s.kind, "line_start": s.line_start, "line_end": s.line_end, "file_path": ""} for s in symbols_query.scalars().all()]

    edges_query = await db.execute(select(GraphEdge).where(GraphEdge.repository_id == repository_id))
    edges_list = [{"source": str(e.source_id), "target": str(e.target_id)} for e in edges_query.scalars().all()]

    # Run analysis
    raw_findings, scores = CodeQualityAnalyzer.evaluate(files_list, symbols_list, edges_list)

    # Ensure default rules exist in DB
    rule_map = {}
    for rname in ["god_class_smell", "long_method_smell", "hardcoded_secrets", "circular_import_smell"]:
        rq = await db.execute(select(Rule).where(Rule.name == rname))
        rule_obj = rq.scalar_one_or_none()
        if not rule_obj:
            cat = "security" if rname == "hardcoded_secrets" else "quality"
            sev = "critical" if rname == "hardcoded_secrets" else "warning"
            rule_obj = Rule(
                name=rname,
                category=cat,
                severity=sev,
                is_enabled=True,
                thresholds_json={}
            )
            db.add(rule_obj)
            await db.commit()
            await db.refresh(rule_obj)
        rule_map[rname] = rule_obj.id

    # Purge existing findings
    await db.execute(delete(Finding).where(Finding.repository_id == repository_id))
    await db.execute(delete(HealthScore).where(HealthScore.repository_id == repository_id))
    await db.commit()

    # Save new findings
    for f in raw_findings:
        rid = rule_map.get(f["rule_name"])
        if not rid:
            continue
        finding = Finding(
            repository_id=repository_id,
            rule_id=rid,
            target_id=f["target_id"],
            title=f["title"],
            severity=f["severity"],
            category=f["category"],
            description=f["description"],
            evidence_json=f["evidence"],
            status="open"
        )
        db.add(finding)

    # Save overall scores
    health_score = HealthScore(
        repository_id=repository_id,
        overall=scores["overall"],
        quality=scores["quality"],
        security=scores["security"],
        architecture=scores["architecture"]
    )
    db.add(health_score)
    await db.commit()

    return scores


@router.get("/findings", status_code=status.HTTP_200_OK)
async def list_findings(
    repository_id: uuid.UUID,
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve code smells and security warnings list"""
    query = select(Finding).where(Finding.repository_id == repository_id)
    if category:
        query = query.where(Finding.category == category)
    if severity:
        query = query.where(Finding.severity == severity)
        
    res = await db.execute(query.order_by(Finding.created_at.desc()))
    findings = []
    for f in res.scalars().all():
        findings.append({
            "id": str(f.id),
            "title": f.title,
            "category": f.category,
            "severity": f.severity,
            "description": f.description,
            "evidence": f.evidence_json,
            "status": f.status
        })
    return findings


@router.get("/security/summary", status_code=status.HTTP_200_OK)
async def get_security_summary(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get security dashboard metrics"""
    query = select(Finding).where(
        Finding.repository_id == repository_id,
        Finding.category == "security"
    )
    res = await db.execute(query)
    findings = res.scalars().all()

    critical = sum(1 for f in findings if f.severity == "critical")
    warning = sum(1 for f in findings if f.severity == "warning")
    info = sum(1 for f in findings if f.severity == "info")

    return {
        "total_vulnerabilities": len(findings),
        "critical_count": critical,
        "warning_count": warning,
        "info_count": info
    }


@router.get("/rules", status_code=status.HTTP_200_OK)
async def list_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List static rules checks status"""
    res = await db.execute(select(Rule))
    rules = []
    for r in res.scalars().all():
        rules.append({
            "id": str(r.id),
            "name": r.name,
            "category": r.category,
            "severity": r.severity,
            "is_enabled": r.is_enabled
        })
    return rules


@router.patch("/rules/{id}", status_code=status.HTTP_200_OK)
async def update_rule(
    id: uuid.UUID,
    is_enabled: bool = Body(...),
    severity: str = Body("warning"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle a rule status or modify warning thresholds"""
    query = select(Rule).where(Rule.id == id)
    res = await db.execute(query)
    rule = res.scalar_one_or_none()
    if not rule:
        raise NotFoundError("Rule")

    rule.is_enabled = is_enabled
    rule.severity = severity
    await db.commit()
    return {"success": True}


@router.post("/reports/engineering", status_code=status.HTTP_200_OK)
async def compile_technical_debt_report(
    repository_id: uuid.UUID = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate technical debt assessments and remediations effort estimates"""
    query = select(Finding).where(Finding.repository_id == repository_id)
    res = await db.execute(query)
    findings = res.scalars().all()

    # Simple math mapping technical debt efforts
    total_hours = 0
    initiatives = []
    for f in findings:
        hours = 8 if f.severity == "critical" else (3 if f.severity == "warning" else 1)
        total_hours += hours
        initiatives.append({
            "finding_id": str(f.id),
            "title": f.title,
            "remediation_hours": hours,
            "priority": "High" if f.severity == "critical" else "Medium"
        })

    return {
        "estimated_debt_remediation_hours": total_hours,
        "remediation_cost_level": "High" if total_hours > 40 else "Medium",
        "initiatives": initiatives
    }
