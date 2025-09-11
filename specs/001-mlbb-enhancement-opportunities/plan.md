# Implementation Plan: MLBB Coach AI Enhancement Opportunities

**Branch**: `001-mlbb-enhancement-opportunities` | **Date**: 2025-09-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-mlbb-enhancement-opportunities/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path ✅
   → Spec loaded successfully from spec.md
2. Fill Technical Context (scan for NEEDS CLARIFICATION) ✅
   → Detected Project Type: web (FastAPI backend + Next.js frontend)
   → Set Structure Decision: Option 2 (Web application)
3. Evaluate Constitution Check section below ✅
   → Initial assessment completed
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md ⏳
   → Research tasks identified and executing
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md ⏳
6. Re-evaluate Constitution Check section ⏳
   → Post-design evaluation pending
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md) ⏳
8. STOP - Ready for /tasks command ⏳
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Implement comprehensive enhancements to the MLBB Coach AI system including expanded hero coverage (20+ heroes), analytics dashboard with historical tracking, mobile PWA optimization, real-time WebSocket-based coaching, multi-language support (5+ languages), and team analysis capabilities. Technical approach leverages existing FastAPI + Next.js architecture with Redis caching and integrates new PostgreSQL analytics storage.

## Technical Context
**Language/Version**: Python 3.11, JavaScript ES2022, TypeScript 5.0  
**Primary Dependencies**: FastAPI, Next.js 15, React 19, PyTorch, ultralytics (YOLOv8), EasyOCR, OpenCV, shadcn/ui  
**Storage**: Redis (caching/sessions), PostgreSQL (analytics), File system (ML models)  
**Testing**: pytest (backend), Jest/Vitest (frontend), Playwright (E2E)  
**Target Platform**: Linux server (backend), Modern browsers (frontend), PWA mobile  
**Project Type**: web - FastAPI backend + Next.js frontend  
**Performance Goals**: <3s analysis, <200ms real-time, <1s mobile load, 1000 req/s  
**Constraints**: <500MB memory per instance, 99.9% uptime, backward compatibility  
**Scale/Scope**: 10K concurrent users, 100K daily analyses, 20+ heroes, 5+ languages

**FOCUS: OCR+Parsing Layer Improvement**  
**Current Issue**: Low data completeness (28%), failed player detection ("Diary of dolls"), generic fallbacks  
**Target Screenshots**: KDA view (IMG_1767) → hero=Kagura, KDA=9/2/12, MVP=10.5; Damage view (IMG_1768) → damage percentages  
**Core Requirements**: Robust player row detection, structured field extraction, cross-view fusion, confidence scoring, explicit error reasons  
**Deliverables**: `/backend/ocr/` modules (detectors.py, parsers_kda.py, parsers_damage.py, fuse.py, tests/), debug script, integration  
**Acceptance**: ≥85% data completeness, player_located=true, overall_confidence ≥0.85, no bogus defaults

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 3 (backend API, frontend web, shared ML pipeline) ✅ (max 3)
- Using framework directly? ✅ (FastAPI, Next.js without wrapper classes)
- Single data model? ✅ (unified models with serialization for API)
- Avoiding patterns? ✅ (direct service classes, no Repository/UoW unless proven need)

**Architecture**:
- EVERY feature as library? ✅ (hero-rules-engine, analytics-pipeline, realtime-coach, i18n-service)
- Libraries listed: 
  * hero-rules-engine: Expanded hero-specific coaching logic
  * analytics-pipeline: Historical performance tracking and visualization
  * realtime-coach: WebSocket-based live coaching
  * i18n-service: Multi-language support system
  * team-analyzer: Team composition and synergy analysis
- CLI per library: ✅ (--help/--version/--format for each)
- Library docs: llms.txt format planned ✅

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? ✅ (tests written first, must fail before implementation)
- Git commits show tests before implementation? ✅ (commit strategy planned)
- Order: Contract→Integration→E2E→Unit strictly followed? ✅
- Real dependencies used? ✅ (actual Redis, PostgreSQL, WebSocket connections)
- Integration tests for: new libraries, contract changes, shared schemas ✅
- FORBIDDEN: Implementation before test, skipping RED phase ✅

**Observability**:
- Structured logging included? ✅ (JSON structured logs for backend, frontend→backend)
- Frontend logs → backend? ✅ (unified logging stream via API)
- Error context sufficient? ✅ (request IDs, user context, performance metrics)

**Versioning**:
- Version number assigned? ✅ (2.0.0 - major feature expansion)
- BUILD increments on every change? ✅ (automated versioning)
- Breaking changes handled? ✅ (parallel tests, migration plan for API v1→v2)

## Project Structure

### Documentation (this feature)
```
specs/001-mlbb-enhancement-opportunities/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 2: Web application (FastAPI backend + Next.js frontend)
backend/
├── src/
│   ├── models/          # Hero, Analytics, Session models
│   ├── services/        # Hero rules, Analytics, Real-time services
│   ├── api/            # REST and WebSocket endpoints
│   └── lib/            # Shared libraries (i18n, team-analyzer)
└── tests/
    ├── contract/       # API contract tests
    ├── integration/    # Service integration tests
    └── unit/          # Individual component tests

frontend/
├── src/
│   ├── components/     # Enhanced UI components
│   ├── pages/         # Analytics dashboard, mobile-optimized pages
│   └── services/      # API clients, WebSocket handlers
└── tests/
    ├── e2e/           # End-to-end user workflows
    ├── integration/   # Component integration tests
    └── unit/         # Component unit tests

shared/
├── types/             # TypeScript definitions
├── schemas/           # Data validation schemas
└── constants/         # Shared constants (heroes, languages)
```

**Structure Decision**: Option 2 (Web application) - FastAPI backend + Next.js frontend with shared types

## Phase 0: Outline & Research

### Research Tasks Identified:

1. **Hero Rules Engine Architecture**: Research scalable patterns for 20+ hero-specific rule systems
2. **Real-time WebSocket Performance**: Best practices for low-latency (<200ms) WebSocket coaching
3. **Multi-language Localization**: i18n frameworks for gaming terminology and cultural adaptation
4. **PWA Mobile Optimization**: Advanced PWA patterns for image upload and offline capabilities
5. **Analytics Time-Series Storage**: PostgreSQL vs specialized time-series databases for performance metrics
6. **Team Composition Algorithms**: Research MLBB meta analysis and synergy calculation methods

### Research Execution:

**Decision**: PostgreSQL with TimescaleDB extension for time-series analytics  
**Rationale**: Leverages existing PostgreSQL expertise, provides excellent time-series performance, integrates well with FastAPI  
**Alternatives considered**: InfluxDB (overkill for current scale), Redis TimeSeries (limited query capabilities)

**Decision**: React i18next for frontend, Python Babel for backend localization  
**Rationale**: Mature ecosystem, gaming-specific plugins available, namespace support for hero/skill terms  
**Alternatives considered**: Custom solution (too complex), Weblate (overkill for current needs)

**Decision**: YAML-based hero rule configuration with Python dataclasses  
**Rationale**: Human-readable, version controllable, type-safe validation, easy for community contributions  
**Alternatives considered**: JSON (less readable), Database (harder to version), Python code (less accessible)

**Decision**: WebSocket with Redis pub/sub for real-time scaling  
**Rationale**: Existing Redis infrastructure, horizontal scaling support, session persistence  
**Alternatives considered**: Server-Sent Events (one-way only), WebRTC (too complex for text coaching)

**Decision**: Workbox for PWA with custom image preprocessing worker  
**Rationale**: Battle-tested PWA toolkit, custom worker for ML preprocessing, offline-first approach  
**Alternatives considered**: Custom service worker (reinventing wheel), PWA Builder (less control)

**Decision**: Graph-based team synergy analysis with NetworkX  
**Rationale**: Flexible modeling of hero interactions, visualization capabilities, extensible algorithms  
**Alternatives considered**: Matrix-based (less intuitive), Rule-based (harder to maintain), ML-based (insufficient training data)

**Output**: All technical unknowns resolved, implementation approaches validated

## Phase 1: Design & Contracts

### Data Model Design

**Core Entities**:
- `HeroRule`: Enhanced with YAML configuration support, skill-specific analysis
- `AnalyticsSession`: Time-series performance data with aggregation support  
- `RealtimeCoaching`: WebSocket session management and coaching state
- `LocalizationEntry`: Multi-language support with context and pluralization
- `TeamComposition`: Team synergy analysis and recommendations
- `UserPreferences`: Language, coaching style, notification settings

### API Contracts

**REST Endpoints**:
- `POST /api/v2/analysis/screenshot` - Enhanced analysis with hero selection
- `GET /api/v2/analytics/performance` - Historical performance data
- `GET /api/v2/heroes/{hero_id}/rules` - Hero-specific coaching rules
- `POST /api/v2/localization/translate` - Dynamic translation endpoint
- `POST /api/v2/team/analyze` - Team composition analysis

**WebSocket Endpoints**:
- `/ws/realtime-coaching` - Live coaching session management
- `/ws/team-session` - Multi-player team analysis sessions

### Mobile PWA Enhancements

**Service Worker Features**:
- Offline image preprocessing
- Coaching rule caching
- Progressive image upload with retry
- Background sync for failed uploads

**Mobile-Specific UI**:
- Touch-optimized screenshot crop tool
- Gesture-based navigation
- Adaptive image quality based on connection
- One-handed operation support

### Contract Test Framework

**API Contract Tests**:
- OpenAPI 3.0 schema validation for all endpoints
- Request/response type checking with TypeScript
- WebSocket message format validation
- Error response standardization

**Integration Test Scenarios**:
- Hero rule loading and application
- Real-time coaching session lifecycle
- Multi-language content delivery
- Team analysis workflow
- Mobile upload and processing pipeline

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each API contract → contract test task [P]
- Each data model → model creation task [P] 
- Each user story → integration test task
- Each library → CLI implementation task [P]
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models → Services → API → Frontend
- Library order: Core utilities → Business logic → Integration
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 35-40 numbered, ordered tasks in tasks.md covering:
- 8-10 contract test tasks
- 6-8 model creation tasks  
- 5-6 library development tasks
- 8-10 service implementation tasks
- 6-8 frontend component tasks
- 4-6 integration and E2E test tasks

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No constitutional violations requiring justification*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - Enhanced with OCR+Parsing research
- [x] Phase 1: Design complete (/plan command) - Enhanced with OCR data models and API contracts
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)
- [x] OCR+Parsing requirements integrated into all artifacts

**OCR+Parsing Integration Status**:
- [x] Technical Context updated with OCR focus and acceptance criteria
- [x] Research.md enhanced with OCR pipeline architecture and error handling
- [x] Data-model.md extended with OCR extraction, player detection, and fusion models
- [x] API contracts updated with OCR debug endpoints and schemas
- [x] Quickstart.md enhanced with OCR validation workflows and testing

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*