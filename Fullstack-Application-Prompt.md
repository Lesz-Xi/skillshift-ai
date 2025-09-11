# SkillShift AI - MLBB Coach AI Platform

## Full-Stack AI-Powered Esports Coaching Application

### PROJECT OVERVIEW

Create a production-ready, full-stack AI coaching platform for Mobile Legends: Bang Bang (MLBB) that analyzes gameplay screenshots and videos to provide personalized coaching feedback. The system combines advanced OCR, computer vision, and AI to deliver 95%+ accuracy analysis with real-time coaching insights.

### CORE REQUIREMENTS

#### 1. BACKEND ARCHITECTURE (FastAPI + Python)

- **Framework**: FastAPI with async/await support
- **AI/ML Stack**: EasyOCR, Tesseract, YOLOv8, OpenCV, PyTorch
- **Database**: Redis for caching + job queues
- **Performance**: <3s processing time, 1000+ concurrent users
- **API Design**: RESTful with WebSocket support for real-time updates

#### 2. FRONTEND ARCHITECTURE (Next.js 15 + React)

- **Framework**: Next.js 15 with App Router
- **Styling**: Tailwind CSS with custom design system
- **UI Components**: Radix UI primitives with custom components
- **State Management**: React hooks + context
- **Features**: Drag-and-drop upload, real-time analysis, responsive design

#### 3. AI/ML PIPELINE REQUIREMENTS

**OCR System (95%+ Accuracy)**

- Multi-engine ensemble (EasyOCR + Tesseract)
- Game-specific image preprocessing
- MLBB UI region detection
- Confidence scoring and validation
- Caching for performance optimization

**Hero Detection System**

- YOLO-based object detection
- 100+ hero database with aliases and roles
- Fuzzy matching with confidence scoring
- Role-specific analysis thresholds
- Meta tier classification (S/A/B/C/D)

**Analysis Pipeline**

- Multi-tier processing (Basic → Enhanced → Ultimate)
- Intelligent data completion
- Performance metrics extraction (KDA, GPM, damage, etc.)
- Quality validation and error handling
- Session management for multi-screenshot analysis

#### 4. CORE FEATURES

**Screenshot Analysis**

- Upload multiple screenshots (PNG, JPG, JPEG)
- Real-time processing with progress indicators
- Hero identification and role detection
- KDA extraction and performance metrics
- Medal recognition and MVP detection
- Confidence scoring and quality validation

**Video Analysis**

- MP4/AVI/MOV video processing
- Frame extraction and analysis
- Temporal event detection
- Behavioral pattern recognition
- Performance trend analysis

**Coaching System**

- Role-specific feedback (Marksman, Assassin, Mage, Tank, Support, Fighter)
- Severity-based coaching (Critical, Warning, Info, Success)
- Mental coaching with trend analysis
- Performance comparison vs meta
- Improvement roadmap generation

**Counter-Pick Analysis**

- Enemy team composition analysis
- Strategic counter-pick recommendations
- Ban suggestion system
- Meta-aware recommendations
- Win condition mapping

#### 5. TECHNICAL SPECIFICATIONS

**Backend APIs**
POST /api/analyze - Screenshot analysis
POST /api/analyze-enhanced - Advanced analysis
POST /api/analyze-video - Video analysis
POST /api/counter-pick-analysis - Counter-pick recommendations
GET /api/health - Health check
GET /api/hero-database/search - Hero search
POST /api/jobs - Async job creation
GET /api/jobs/{id} - Job status

**Data Models**

```python
# Core match data structure
class MatchData:
    hero: str
    kills: int
    deaths: int
    assists: int
    kda: str
    gpm: int
    hero_damage: int
    turret_damage: int
    damage_taken: int
    teamfight_participation: int
    match_duration: float
    positioning_rating: str
    ult_usage: str
    rank: str
    battle_id: str
```

**Configuration System**

- YAML-based thresholds for role-specific analysis
- Hero-specific overrides and customizations
- Severity level definitions
- Performance benchmarks and scaling

#### 6. PERFORMANCE REQUIREMENTS

**Processing Speed**

- Screenshot analysis: <3 seconds
- Video analysis: <30 seconds
- Batch processing: 1000+ users concurrently
- Cache hit rate: >80% for repeated analyses

**Accuracy Targets**

- Hero detection: 95%+ accuracy
- KDA extraction: 98%+ accuracy
- OCR text recognition: 90%+ accuracy
- Overall analysis confidence: 95%+

**Scalability**

- Horizontal scaling with Redis job queues
- GPU acceleration for ML models
- CDN integration for image optimization
- Database connection pooling

#### 7. USER INTERFACE REQUIREMENTS

**Landing Page**

- Modern, professional design
- Feature showcase with animations
- API pricing tiers
- Company information and principles

**Dashboard**

- Multi-section navigation (Overview, Heroes, Coaching, etc.)
- Real-time status indicators
- Analysis history and trends
- Player insights and recommendations

**Analysis Interface**

- Drag-and-drop file upload
- Real-time processing indicators
- Results modal with detailed feedback
- Export capabilities for analysis data

#### 8. DEPLOYMENT & INFRASTRUCTURE

**Development Setup**

```bash
# Backend
cd skillshift-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn web.app:app --reload --port 8000

# Frontend
cd dashboard-ui-new
npm install
npm run dev
```

**Production Requirements**

- Docker containerization
- Redis for caching and job queues
- File storage for uploads
- Monitoring and logging
- Health checks and metrics

#### 9. TESTING STRATEGY

**Backend Testing**

- Unit tests for core components
- Integration tests for API endpoints
- Performance tests for OCR pipeline
- Mock data fixtures for consistent testing

**Frontend Testing**

- Component unit tests
- Integration tests for user flows
- E2E tests for critical paths
- Accessibility testing

#### 10. SECURITY & COMPLIANCE

**Data Protection**

- Secure file upload handling
- Input validation and sanitization
- Rate limiting for API endpoints
- CORS configuration for frontend

**Performance Monitoring**

- Application metrics collection
- Error tracking and alerting
- Performance profiling
- User analytics (privacy-compliant)

### IMPLEMENTATION PRIORITIES

1. **Phase 1**: Core OCR and hero detection system
2. **Phase 2**: Basic screenshot analysis API
3. **Phase 3**: Frontend dashboard and upload interface
4. **Phase 4**: Advanced analysis features and video processing
5. **Phase 5**: Counter-pick system and mental coaching
6. **Phase 6**: Performance optimization and scaling

### SUCCESS METRICS

- **Technical**: 95%+ analysis accuracy, <3s processing time
- **User Experience**: Intuitive interface, real-time feedback
- **Performance**: 1000+ concurrent users, 99.9% uptime
- **Business**: Scalable architecture, production-ready deployment

### ADDITIONAL CONSIDERATIONS

- **Internationalization**: Support for multiple languages
- **Mobile Responsiveness**: PWA capabilities for mobile users
- **API Documentation**: Comprehensive OpenAPI/Swagger docs
- **Monitoring**: Application performance monitoring (APM)
- **Backup & Recovery**: Data persistence and disaster recovery
- **Compliance**: GDPR/privacy compliance for user data

This is a sophisticated AI-powered platform that requires expertise in computer vision, machine learning, full-stack development, and esports domain knowledge. The system should be built with production scalability in mind while maintaining high accuracy and user experience standards.

