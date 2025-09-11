# Research Phase: MLBB Coach AI Enhancement Opportunities

**Date**: 2025-09-09  
**Feature**: MLBB Enhancement Opportunities  
**Research Status**: Complete ✅

## Research Findings

### 1. Hero Rules Engine Architecture

**Decision**: YAML-based configuration with Python dataclasses and factory pattern  
**Rationale**: 
- Human-readable configuration enables community contributions
- Type-safe validation prevents runtime errors  
- Version control friendly for rule evolution
- Factory pattern enables dynamic rule loading and hot-swapping

**Alternatives Considered**:
- JSON configuration: Less readable, no comments support
- Database storage: Harder to version control, requires migration management
- Python code rules: Higher barrier for non-programmers, requires deployment for changes

**Implementation Pattern**:
```yaml
# heroes/kagura.yml
hero:
  id: kagura
  name: Kagura
  role: mage
  skills:
    passive: 
      name: "Yin Yang Umbrella"
      analysis: check_umbrella_positioning
    s1:
      name: "Seimei Umbrella Open"  
      analysis: check_umbrella_combo_initiation
```

### 2. Real-time WebSocket Performance

**Decision**: Redis pub/sub with WebSocket connection pooling and message compression  
**Rationale**:
- Redis pub/sub enables horizontal scaling across multiple server instances
- Connection pooling reduces resource overhead for high concurrent users
- Message compression (gzip) reduces bandwidth for coaching messages
- Existing Redis infrastructure minimizes additional dependencies

**Alternatives Considered**:
- Server-Sent Events: One-way communication insufficient for interactive coaching
- WebRTC: Too complex for text-based coaching, unnecessary for use case
- Direct WebSocket: No scaling mechanism, single point of failure

**Performance Optimizations**:
- Message batching for rapid analysis updates
- Client-side caching of hero rules and static content  
- Connection heartbeat with exponential backoff
- Priority queuing for critical coaching messages

### 3. Multi-language Localization Framework

**Decision**: React i18next (frontend) + Python Babel (backend) with gaming-specific namespaces  
**Rationale**:
- Mature ecosystem with extensive documentation and community support
- Gaming-specific plugins available for MOBA terminology
- Namespace support allows separation of UI text vs hero/skill names
- ICU message format supports pluralization and complex grammar rules

**Alternatives Considered**:
- Custom solution: Reinventing well-solved problems, maintenance burden
- Weblate: Full translation management platform, overkill for current scale
- Google Translate API: Real-time translation but lacks gaming context

**Localization Strategy**:
- 5 initial languages: English, Chinese (Simplified), Indonesian, Tagalog, Spanish
- Separate namespaces: `ui`, `heroes`, `skills`, `coaching`
- Community translation portal for additional language support
- Cultural adaptation for coaching tone and style preferences

### 4. PWA Mobile Optimization

**Decision**: Workbox with custom service worker for ML preprocessing  
**Rationale**:
- Battle-tested PWA toolkit with Google backing
- Custom worker enables client-side image preprocessing
- Offline-first approach improves reliability on poor mobile connections
- Background sync ensures uploads complete even with intermittent connectivity

**Alternatives Considered**:
- Custom service worker: Reinventing complex caching and sync logic
- PWA Builder: Less control over ML-specific requirements
- Cordova/PhoneGap: Native wrapper adds complexity without significant benefits

**Mobile Optimizations**:
- WebP image format with fallback for older browsers
- Adaptive image quality based on connection speed detection
- Touch-optimized UI with minimum 44px touch targets
- Gesture navigation for one-handed operation
- Progressive image upload with client-side compression

### 5. Analytics Time-Series Storage

**Decision**: PostgreSQL with TimescaleDB extension  
**Rationale**:
- Leverages existing PostgreSQL expertise and infrastructure
- TimescaleDB provides excellent time-series performance without complexity
- Native SQL support enables complex analytical queries
- Automatic partitioning handles data growth efficiently

**Alternatives Considered**:
- InfluxDB: Specialized time-series database, overkill for current scale
- Redis TimeSeries: Limited query capabilities, not suitable for complex analytics
- MongoDB: Document storage less optimal for time-series data patterns

**Data Modeling**:
- Automatic partitioning by day for performance
- Continuous aggregates for common query patterns
- Retention policies for data lifecycle management
- Materialized views for dashboard performance

### 6. Team Composition Analysis

**Decision**: Graph-based analysis with NetworkX and custom synergy algorithms  
**Rationale**:
- Graph structure naturally models hero relationships and synergies
- NetworkX provides visualization and analysis capabilities
- Custom algorithms can incorporate MLBB-specific meta knowledge
- Extensible framework for future meta evolution

**Alternatives Considered**:
- Matrix-based calculations: Less intuitive for relationship modeling
- Rule-based system: Harder to maintain as meta evolves
- Machine learning approach: Insufficient training data for accurate predictions

**Analysis Framework**:
- Hero synergy scores based on role compatibility, skill combinations
- Counter-pick analysis using champion win rates and matchup data
- Team composition strength scoring with role balance considerations
- Meta trend analysis for evolving strategic recommendations

### 7. OCR+Parsing Layer Enhancement

**Decision**: Multi-stage OCR pipeline with template-based anchoring and fuzzy matching  
**Rationale**:
- Template anchoring ensures reliable table region detection
- Fuzzy string matching handles OCR errors in player names
- Confidence scoring provides transparency for debugging
- Separate parsers for KDA vs Damage views enable specialized extraction

**Current Issues Identified**:
- Player row detection fails for "Diary of dolls" (exact match requirement)
- Generic fallbacks return invalid defaults (KDA=0/1/0)
- Low data completeness (28%) due to parsing failures
- Missing cross-view fusion for comprehensive match data

**Technical Approach**:
- **Primary Detection**: Exact IGN matching with normalization
- **Secondary Detection**: Visual anchors (avatar circle + PH flag + level)
- **Tertiary Detection**: MVP crown icon detection with team affiliation
- **Fallback Strategy**: Fuzzy matching (≥0.88 similarity) with contextual clues

**Implementation Architecture**:
```python
/backend/ocr/
├── detectors.py      # Player row detection with fallbacks
├── parsers_kda.py    # KDA view specific extraction
├── parsers_damage.py # Damage view specific extraction  
├── fuse.py          # Cross-view data fusion with confidence
├── normalizers.py   # OCR text cleaning and standardization
└── tests/           # Unit tests with fixture screenshots
```

**Error Handling Strategy**:
- Explicit warnings for each missing field
- Confidence scoring for extracted values
- Never return invented data (0/1/0 defaults)
- Detailed logging for debugging failed extractions

**Performance Requirements**:
- ≥85% data completeness on target screenshots
- player_located=true for known IGNs
- overall_confidence ≥0.85 for successful extractions
- <500ms additional processing time per screenshot pair

## Technical Dependencies Validation

### Backend Dependencies
- **FastAPI 0.104+**: Async support for WebSocket scaling ✅
- **Redis 7.0+**: Pub/sub and TimeSeries modules ✅  
- **PostgreSQL 14+**: TimescaleDB compatibility ✅
- **PyTorch 2.0+**: Model loading performance improvements ✅
- **Pydantic V2**: Type validation performance ✅

### Frontend Dependencies  
- **Next.js 15**: App router and React 19 compatibility ✅
- **React i18next 13+**: React 18+ support ✅
- **shadcn/ui**: Component library consistency ✅
- **Workbox 7**: Latest PWA features ✅
- **Socket.io-client 4+**: WebSocket reliability ✅

### Infrastructure Dependencies
- **TimescaleDB 2.11+**: Latest time-series features ✅
- **Redis Modules**: TimeSeries and Pub/Sub support ✅
- **Node.js 18+**: Next.js 15 requirement ✅
- **Python 3.11+**: Performance improvements for ML workloads ✅

## Risk Mitigation Strategies

### Performance Risks
- **WebSocket scaling**: Implement connection pooling and Redis pub/sub early
- **Mobile performance**: Progressive enhancement, extensive device testing
- **Database performance**: Use TimescaleDB aggregation, implement caching layers

### Technical Risks  
- **Localization accuracy**: Use professional translation services for core languages
- **PWA compatibility**: Test across major mobile browsers, provide fallbacks
- **Hero rule complexity**: Start simple, build complexity incrementally

### Business Risks
- **User adoption**: Feature flags for gradual rollout, user feedback integration  
- **Maintenance complexity**: Comprehensive testing, modular architecture
- **Performance degradation**: Load testing, performance monitoring, graceful degradation

## Implementation Readiness Assessment

**Architecture Foundation**: ✅ Existing system provides solid base  
**Technical Expertise**: ✅ Team familiar with all chosen technologies  
**Infrastructure Readiness**: ✅ Current infrastructure supports planned enhancements  
**Performance Requirements**: ✅ Benchmarks achievable with planned optimizations  
**Scalability Path**: ✅ Horizontal scaling strategy defined  

**Status**: All research complete, ready for Phase 1 design and contracts.