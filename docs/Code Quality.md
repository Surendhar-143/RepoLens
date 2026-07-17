# Code Quality & Security Scanning Manual

RepoLens runs static code assessments to measure maintainability, trace architectural imports cycles, and scan for hardcoded secrets.

## 1. Scanner Rules Checkers
We implement configurable backend checks:
* **God Class Smell**: Flags any class node exceeding 300 source lines.
* **Long Method Smell**: Flags helper functions exceeding 60 lines.
* **Cryptographic Secret Leak**: Uses regex checking variable declarations matching common passwords, tokens, or credential signatures.
* **Circular imports loop**: Analyzes packages imports trees for mutual dependency reference loops.

---

## 2. Engineering Telemetry Health Score
Health scores are calculated out of 100 based on warnings:
* **Overall Rating**: Average score mapping quality, security, and architecture health indicators.
* **Security score**: Decrements dynamically by 15% for every critical credentials leak detected.
* **smells warnings score**: Decrements by 5% for circular packages loops and 1% for long functions.

---

## 3. Technical Debt Initiatives
Remediation estimates predict refactoring hours:
* **Critical Secret vulnerability**: 8 hours effort.
* **Warning circular reference smell**: 3 hours effort.
* **Info code smells**: 1 hour.
