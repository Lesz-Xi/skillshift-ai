# Quickstart Guide: MLBB Coach AI Enhancement Implementation

**Feature**: Enhanced MLBB Coach AI with expanded hero coverage, analytics, and real-time coaching  
**Date**: 2025-09-09  
**Estimated Setup Time**: 30-45 minutes  

## Prerequisites

### Development Environment
- **Python**: 3.11+ with pip and virtual environment support
- **Node.js**: 18+ with npm or yarn
- **Redis**: 7.0+ with TimeSeries and Pub/Sub modules
- **PostgreSQL**: 14+ with TimescaleDB extension
- **Git**: Latest version for source control

### External Services
- **OpenAI API**: For enhanced coaching intelligence (optional)
- **Translation Service**: Google Translate API or similar (for localization)
- **CDN**: For static asset delivery (production)

### Hardware Requirements
- **Development**: 8GB RAM, 4 CPU cores, 20GB storage
- **Production**: 16GB RAM, 8 CPU cores, 100GB+ storage, SSD recommended

## Quick Setup (Development)

### 1. Environment Setup (5 minutes)

```bash
# Clone repository and create feature branch
git clone <repository-url>
cd mlbb-coach-ai
git checkout 001-mlbb-enhancement-opportunities

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend setup  
cd ../frontend
npm install

# Install development dependencies
npm install -D @types/node @types/react typescript
```

### 2. Database Setup (10 minutes)

```bash
# Start PostgreSQL and Redis (using Docker)
docker-compose up -d postgres redis

# Wait for services to be ready
sleep 10

# Create databases
createdb mlbb_coach_ai_dev
createdb mlbb_coach_ai_test

# Install TimescaleDB extension
psql mlbb_coach_ai_dev -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Run database migrations
cd backend
python -m alembic upgrade head

# Seed initial data (heroes, roles, basic rules)
python scripts/seed_heroes.py
python scripts/seed_base_rules.py
```

### 3. Configuration (5 minutes)

```bash
# Backend configuration
cd backend
cp .env.example .env

# Edit .env file with your settings:
# DATABASE_URL=postgresql://localhost/mlbb_coach_ai_dev
# REDIS_URL=redis://localhost:6379/0
# OPENAI_API_KEY=your_openai_key_here (optional)
# GOOGLE_TRANSLATE_API_KEY=your_translate_key_here (optional)

# Frontend configuration
cd ../frontend
cp .env.local.example .env.local

# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000/v2
# NEXT_PUBLIC_WS_URL=ws://localhost:8000/v2/ws
```

### 4. Start Development Servers (2 minutes)

```bash
# Terminal 1: Backend API server
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend development server  
cd frontend
npm run dev

# Terminal 3: WebSocket server (if separate)
cd backend
python -m uvicorn websocket_server:app --reload --port 8001
```

### 5. Verify Installation (5 minutes)

```bash
# Test API endpoints
curl http://localhost:8000/v2/heroes
curl http://localhost:8000/v2/analytics/performance

# Test WebSocket connection
# Use browser console or wscat:
# wscat -c ws://localhost:8000/v2/ws/realtime-coaching

# Access frontend
open http://localhost:3000

# Run initial tests
cd backend && python -m pytest tests/test_setup.py
cd frontend && npm run test:quick
```

## Feature Validation Workflow

### 1. Hero Coverage Expansion (10 minutes)

```bash
# Test hero rule loading
curl http://localhost:8000/v2/heroes/kagura/rules
curl http://localhost:8000/v2/heroes/tigreal/rules

# Add new hero (example: Gusion)
cd backend
python scripts/add_hero.py --hero-id gusion --role assassin --config heroes/gusion.yml

# Verify new hero is available
curl http://localhost:8000/v2/heroes | grep gusion
```

### 2. Analytics Dashboard (5 minutes)

```bash
# Generate sample analytics data
cd backend  
python scripts/generate_sample_data.py --days 30 --sessions 100

# Test analytics endpoints
curl "http://localhost:8000/v2/analytics/performance?period=week"
curl "http://localhost:8000/v2/analytics/trends?metric=kda"

# Access analytics dashboard
open http://localhost:3000/analytics
```

### 3. Real-time Coaching (5 minutes)

```bash
# Start real-time coaching session
# In browser console at http://localhost:3000:

const ws = new WebSocket('ws://localhost:8000/v2/ws/realtime-coaching');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'session_start',
    id: 'test_001',
    timestamp: new Date().toISOString(),
    session_id: 'session_test',
    data: {
      hero_id: 'kagura',
      preferences: { coaching_frequency: 'normal' }
    }
  }));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

### 4. Localization Testing (3 minutes)

```bash
# Test translation endpoint
curl -X POST http://localhost:8000/v2/localization/translate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Great positioning!",
    "to_language": "es",
    "namespace": "coaching"
  }'

# Test UI language switching
open http://localhost:3000?lang=es
```

### 5. OCR+Parsing Validation (10 minutes)

```bash
# Test OCR debug endpoint with sample screenshots
cd backend/tests/fixtures
curl -X POST http://localhost:8000/v2/ocr/debug \
  -F "kda_image=@IMG_1767.png" \
  -F "target_ign=Diary of dolls" \
  -F "expected_hero=kagura" \
  -F "expected_kda=9/2/12"

# Expected response validation:
# - player_located: true
# - overall_confidence: >= 0.85
# - data_completeness: >= 0.85
# - hero: "kagura"
# - kda: {k: 9, d: 2, a: 12}

# Test cross-view fusion
curl -X POST http://localhost:8000/v2/ocr/fusion \
  -H "Content-Type: application/json" \
  -d '{
    "kda_result": { /* KDA extraction result */ },
    "damage_result": { /* Damage extraction result */ },
    "target_ign": "Diary of dolls"
  }'

# Run OCR debug script
python -m backend.ocr.debug --img IMG_1767.png --img IMG_1768.png

# Verify no "No numeric data found" warnings
# Verify player detection success rate >= 95%
```

## Testing Framework

### Backend Tests

```bash
cd backend

# Unit tests
python -m pytest tests/unit/ -v

# OCR-specific tests
python -m pytest tests/unit/ocr/ -v
python -m pytest tests/integration/test_ocr_pipeline.py -v

# Integration tests  
python -m pytest tests/integration/ -v

# Contract tests (API validation)
python -m pytest tests/contract/ -v

# Performance tests
python -m pytest tests/performance/ -v --benchmark-only

# OCR accuracy tests (requires test fixtures)
python -m pytest tests/ocr_accuracy/ -v
```

### Frontend Tests

```bash
cd frontend

# Unit tests
npm run test

# Component integration tests
npm run test:integration

# End-to-end tests
npm run test:e2e

# Performance tests
npm run lighthouse:dev
```

### Full System Test

```bash
# Run complete test suite
cd scripts
./run_full_test_suite.sh

# Expected output:
# ✅ Backend unit tests: 45/45 passed
# ✅ Frontend unit tests: 32/32 passed  
# ✅ API contract tests: 12/12 passed
# ✅ E2E tests: 8/8 passed
# ✅ Performance tests: All benchmarks within limits
```

## Common Issues & Solutions

### Database Connection Issues
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check TimescaleDB extension
psql mlbb_coach_ai_dev -c "SELECT default_version FROM pg_available_extensions WHERE name = 'timescaledb';"

# Reset database if needed
dropdb mlbb_coach_ai_dev && createdb mlbb_coach_ai_dev
python -m alembic upgrade head
```

### Redis Connection Issues
```bash
# Check Redis is running
redis-cli ping

# Check Redis modules
redis-cli MODULE LIST

# Restart Redis with modules
redis-server --loadmodule /usr/lib/redis/modules/redistimeseries.so
```

### WebSocket Connection Issues
```bash
# Check if WebSocket server is running
netstat -tulpn | grep :8000

# Test WebSocket connection
wscat -c ws://localhost:8000/v2/ws/realtime-coaching

# Check WebSocket logs
tail -f backend/logs/websocket.log
```

### Frontend Build Issues
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run type-check

# Build for production
npm run build
```

## Production Deployment Checklist

### Infrastructure Setup
- [ ] PostgreSQL with TimescaleDB extension configured
- [ ] Redis with required modules (TimeSeries, Pub/Sub)
- [ ] Load balancer configured for WebSocket sticky sessions
- [ ] CDN configured for static assets
- [ ] SSL certificates installed and configured

### Application Configuration
- [ ] Environment variables set for production
- [ ] Database migrations applied
- [ ] Hero rules and initial data seeded
- [ ] Localization data loaded for target languages
- [ ] Performance monitoring configured
- [ ] Error tracking and logging configured

### Security Configuration
- [ ] API rate limiting configured
- [ ] WebSocket authentication enabled
- [ ] CORS settings configured for production domains
- [ ] Input validation enabled for all endpoints
- [ ] Security headers configured (HTTPS, CSP, etc.)

### Performance Optimization
- [ ] Database indexes optimized for production queries
- [ ] Redis caching configured with appropriate TTL values
- [ ] Frontend bundle optimization and code splitting enabled
- [ ] Image optimization and WebP conversion enabled
- [ ] CDN caching rules configured

### Monitoring & Alerting
- [ ] Application performance monitoring (APM) configured
- [ ] Database performance monitoring enabled
- [ ] WebSocket connection monitoring configured
- [ ] Error rate and latency alerts configured
- [ ] Resource usage alerts (CPU, memory, disk) configured

## Next Steps

After completing this quickstart:

1. **Review the generated tasks.md** (created by `/tasks` command)
2. **Implement features in TDD order** (tests first, then implementation)
3. **Monitor performance metrics** during development
4. **Gather user feedback** from beta testing
5. **Iterate on coaching quality** based on analytics

For detailed implementation guidance, refer to:
- [Data Model Documentation](./data-model.md)
- [API Contract Specifications](./contracts/api-v2.yaml)
- [WebSocket Protocol Guide](./contracts/websocket-protocol.md)

**Happy coding! 🎮⚡**