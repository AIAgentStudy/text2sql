<!--
============================================================================
SYNC IMPACT REPORT
============================================================================
Version change: 1.0.0 → 2.0.0 (MAJOR - language change from TypeScript to Python)

Modified principles:
  - I. Type Safety: TypeScript → Python with type hints
  - II. Modular Architecture: index.ts → __init__.py
  - V. Documentation as Code: TSDoc → docstrings

Added sections: None

Removed sections: None

Templates requiring updates:
  ✅ .specify/templates/plan-template.md - Compatible
  ✅ .specify/templates/spec-template.md - Compatible
  ✅ .specify/templates/tasks-template.md - Compatible
  ✅ .specify/templates/checklist-template.md - Compatible
  ✅ .specify/templates/agent-file-template.md - Compatible

Follow-up TODOs: None
============================================================================
-->

# TSAgent Constitution

> TSAgent = Text2SQL Agent (약어)

## Core Principles

### I. Type Safety

All code MUST use Python type hints with strict type checking via mypy or pyright.
Dynamic typing without annotations is prohibited except when interfacing with untyped
external libraries, and such exceptions MUST be documented with a justification comment.

**Requirements**:
- `strict = true` in mypy.ini or pyproject.toml
- All function parameters and return types MUST be explicitly annotated
- Use `typing` module types (Optional, Union, List, Dict, etc.) or Python 3.10+ syntax
- Use Pydantic models for data validation and serialization
- External library types: use stub packages or create type stubs

**Rationale**: Type hints catch errors at lint time, improve IDE support,
and serve as executable documentation. The upfront cost prevents runtime type errors
and reduces debugging time.

### II. Modular Architecture

Features MUST be implemented as independent, composable modules with clear boundaries.
Each module MUST have a single responsibility and expose a well-defined public API.

**Requirements**:
- One module = one directory with an `__init__.py` defining public exports
- Modules MUST NOT have circular dependencies
- Internal implementation details MUST NOT be exported from __init__.py
- Cross-module communication MUST use defined protocols/interfaces, not concrete implementations
- Module dependencies MUST be injected via dependency injection where testability matters

**Rationale**: Modular design enables independent testing, parallel development,
and selective replacement of components without cascading changes.

### III. Test-First Development

Tests MUST be written before implementation code. The Red-Green-Refactor cycle
is mandatory for all feature development.

**Requirements**:
- Write failing tests first (Red)
- Implement minimum code to pass tests (Green)
- Refactor while keeping tests green (Refactor)
- Tests MUST be approved/reviewed before implementation begins
- Code coverage MUST be maintained above 80% for critical paths
- Integration tests required for cross-module interactions

**Rationale**: TDD ensures code is designed for testability, prevents over-engineering,
and provides living documentation of expected behavior.

### IV. Simplicity First

Start with the simplest solution that works. Complexity MUST be justified by concrete,
current requirements—not hypothetical future needs.

**Requirements**:
- YAGNI (You Aren't Gonna Need It): Do not build features "just in case"
- Prefer composition over inheritance
- Avoid premature abstraction: three concrete uses before extracting a pattern
- No design patterns without a documented problem they solve
- Configuration and feature flags only when multiple modes are required today

**Rationale**: Simpler code is easier to understand, test, debug, and modify.
Complexity is a cost that must be justified by proportional benefit.

### V. Documentation as Code

Documentation MUST be maintained alongside code and treated with equal importance.
Outdated documentation is worse than no documentation.

**Requirements**:
- Public APIs MUST have docstrings (Google style) explaining purpose, parameters, and return values
- README.md required for each module explaining purpose and basic usage
- Architectural decisions MUST be recorded in decision logs when non-obvious
- Examples MUST be executable and verified by CI
- CHANGELOG.md MUST be updated for user-facing changes

**Rationale**: Documentation enables onboarding, reduces knowledge silos, and
serves as the first line of support for consumers of the code.

## Development Workflow

### Code Review Process

- All changes MUST be submitted via pull request
- PRs MUST pass automated checks before review (lint, type-check, tests)
- At least one approval required before merge
- Author MUST NOT merge their own PR without approval
- Review comments MUST be resolved or explicitly deferred with justification

### Quality Gates

- Type checking (mypy/pyright) MUST succeed with zero errors
- Linting (ruff) MUST pass with zero warnings in CI
- All tests MUST pass
- Type coverage MUST not decrease
- No `print()` statements in production code (use structured logging)

## Quality Standards

### Performance

- Async operations MUST use `asyncio` and not block the event loop
- Memory-intensive operations MUST use streaming/generators where applicable
- Performance-critical code MUST have benchmarks

### Error Handling

- Errors MUST be typed (custom exception classes extending Exception)
- Async functions MUST handle exceptions properly
- User-facing errors MUST be actionable (explain what went wrong and how to fix)
- Internal errors MUST be logged with sufficient context for debugging

### Security

- User input MUST be validated at system boundaries (Pydantic models)
- Secrets MUST NOT be committed to version control
- Dependencies MUST be audited regularly for vulnerabilities

## Governance

This constitution is the authoritative source for development practices in TSAgent.
All contributors, code reviews, and architectural decisions MUST comply with these
principles.

### Amendment Process

1. Propose amendment via pull request modifying this file
2. Document rationale for the change
3. Obtain approval from project maintainers
4. Update version number according to semantic versioning:
   - MAJOR: Principle removal or backward-incompatible redefinition
   - MINOR: New principle or section added
   - PATCH: Clarifications, wording improvements
5. Update LAST_AMENDED_DATE to the merge date
6. Propagate changes to dependent templates if principles affect them

### Compliance Review

- PRs MUST verify compliance with constitution principles
- Violations MUST be documented and justified in the Complexity Tracking section of plans
- Regular audits SHOULD review adherence to principles

**Version**: 2.0.0 | **Ratified**: 2025-01-30 | **Last Amended**: 2025-01-30
