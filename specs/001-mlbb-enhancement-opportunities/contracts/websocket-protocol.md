# WebSocket Protocol Specification

**Version**: 2.0.0  
**Date**: 2025-09-09  
**Feature**: Real-time Coaching and Team Analysis

## Connection Management

### Connection Endpoint
```
wss://api.mlbbcoach.ai/v2/ws/realtime-coaching
wss://api.mlbbcoach.ai/v2/ws/team-session
```

### Authentication
```javascript
// Connection with JWT token
const ws = new WebSocket('wss://api.mlbbcoach.ai/v2/ws/realtime-coaching', [], {
  headers: {
    'Authorization': 'Bearer <jwt_token>'
  }
});

// Or via query parameter
const ws = new WebSocket('wss://api.mlbbcoach.ai/v2/ws/realtime-coaching?token=<jwt_token>');
```

### Connection Lifecycle
1. **Connect**: Client initiates WebSocket connection with auth
2. **Handshake**: Server validates token and sends session info
3. **Subscribe**: Client subscribes to coaching channels
4. **Active**: Bi-directional message exchange
5. **Disconnect**: Clean session termination

## Message Format

### Base Message Structure
```typescript
interface BaseMessage {
  type: string;
  id: string;  // Unique message ID
  timestamp: string; // ISO 8601 format
  session_id: string;
  data: any;
}
```

### Message Types

#### 1. Session Management

**CLIENT → SERVER: session_start**
```json
{
  "type": "session_start",
  "id": "msg_001",
  "timestamp": "2025-09-09T10:30:00Z",
  "session_id": "session_123",
  "data": {
    "hero_id": "kagura",
    "game_mode": "ranked",
    "preferences": {
      "coaching_frequency": "normal",
      "language": "en",
      "focus_areas": ["positioning", "mechanics"]
    }
  }
}
```

**SERVER → CLIENT: session_started**
```json
{
  "type": "session_started",
  "id": "msg_002", 
  "timestamp": "2025-09-09T10:30:01Z",
  "session_id": "session_123",
  "data": {
    "status": "active",
    "hero_rules_loaded": true,
    "coaching_enabled": true,
    "estimated_latency": 150
  }
}
```

**CLIENT → SERVER: session_end**
```json
{
  "type": "session_end",
  "id": "msg_999",
  "timestamp": "2025-09-09T11:30:00Z", 
  "session_id": "session_123",
  "data": {
    "reason": "game_completed"
  }
}
```

#### 2. Real-time Coaching

**SERVER → CLIENT: coaching_tip**
```json
{
  "type": "coaching_tip",
  "id": "tip_001",
  "timestamp": "2025-09-09T10:35:00Z",
  "session_id": "session_123", 
  "data": {
    "priority": 3,
    "category": "positioning",
    "severity": "warning",
    "title": "Positioning Alert",
    "message": "You're too far forward - consider retreating to safer position",
    "improvement_suggestion": "Stay behind your tank during team fights",
    "duration": 5000,
    "hero_specific": true,
    "localized": {
      "en": "You're too far forward - consider retreating to safer position",
      "es": "Estás demasiado adelante - considera retirarte a una posición más segura"
    }
  }
}
```

**CLIENT → SERVER: coaching_acknowledged**
```json
{
  "type": "coaching_acknowledged",
  "id": "ack_001", 
  "timestamp": "2025-09-09T10:35:05Z",
  "session_id": "session_123",
  "data": {
    "tip_id": "tip_001",
    "helpful": true,
    "implemented": false
  }
}
```

**SERVER → CLIENT: coaching_update**
```json
{
  "type": "coaching_update",
  "id": "update_001",
  "timestamp": "2025-09-09T10:40:00Z", 
  "session_id": "session_123",
  "data": {
    "performance_snapshot": {
      "kda": {"kills": 3, "deaths": 1, "assists": 5},
      "gpm": 450,
      "position_score": 85
    },
    "real_time_score": 78,
    "improvement_areas": ["ultimate_usage", "map_awareness"]
  }
}
```

#### 3. Team Session Management

**CLIENT → SERVER: team_join**
```json
{
  "type": "team_join",
  "id": "team_001",
  "timestamp": "2025-09-09T10:30:00Z",
  "session_id": "team_session_456",
  "data": {
    "team_id": "team_789",
    "player_role": "captain",
    "hero_selection": "kagura"
  }
}
```

**SERVER → CLIENT: team_update**
```json
{
  "type": "team_update", 
  "id": "team_002",
  "timestamp": "2025-09-09T10:30:30Z",
  "session_id": "team_session_456",
  "data": {
    "team_composition": ["kagura", "tigreal", "layla", "gusion", "rafaela"],
    "synergy_score": 85,
    "recommendations": [
      "Strong initiation potential with Tigreal + Kagura combo",
      "Consider protecting Layla in team fights",
      "Gusion can follow up on Kagura's umbrella combos"
    ],
    "counter_warnings": [
      "Vulnerable to high mobility assassins",
      "Lacks sustained damage in late game"
    ]
  }
}
```

#### 4. Performance Monitoring

**CLIENT → SERVER: performance_data**
```json
{
  "type": "performance_data",
  "id": "perf_001",
  "timestamp": "2025-09-09T10:45:00Z",
  "session_id": "session_123", 
  "data": {
    "game_time": 720,
    "metrics": {
      "kills": 4,
      "deaths": 2, 
      "assists": 7,
      "gold": 8500,
      "hero_damage": 35000,
      "position": {"x": 1250, "y": 800}
    },
    "events": [
      {"type": "skill_used", "skill": "s1", "timestamp": "2025-09-09T10:44:55Z"},
      {"type": "kill", "target": "enemy_layla", "timestamp": "2025-09-09T10:44:58Z"}
    ]
  }
}
```

#### 5. Error Handling

**SERVER → CLIENT: error**
```json
{
  "type": "error",
  "id": "err_001",
  "timestamp": "2025-09-09T10:30:00Z",
  "session_id": "session_123",
  "data": {
    "code": "HERO_RULES_NOT_FOUND",
    "message": "Hero rules not available for selected champion", 
    "severity": "warning",
    "recoverable": true,
    "suggested_action": "fallback_to_role_based_coaching"
  }
}
```

#### 6. Connection Health

**CLIENT/SERVER: ping/pong**
```json
{
  "type": "ping",
  "id": "ping_001", 
  "timestamp": "2025-09-09T10:30:00Z",
  "session_id": "session_123",
  "data": {}
}

{
  "type": "pong",
  "id": "pong_001",
  "timestamp": "2025-09-09T10:30:00Z", 
  "session_id": "session_123",
  "data": {
    "latency": 45
  }
}
```

## Quality of Service

### Message Priority Levels
- **5 (Critical)**: Immediate danger warnings, game-breaking errors
- **4 (High)**: Important positioning/timing alerts
- **3 (Normal)**: Regular coaching tips and suggestions  
- **2 (Low)**: General improvements and optimizations
- **1 (Info)**: Performance updates and statistics

### Message Delivery Guarantees
- **Critical/High Priority**: Guaranteed delivery with acknowledgment
- **Normal Priority**: Best effort delivery
- **Low/Info Priority**: Fire-and-forget, may be dropped under load

### Rate Limiting
- **Coaching messages**: Max 10 per minute per session
- **Performance updates**: Max 1 per 5 seconds 
- **Team updates**: Max 5 per minute
- **Connection health**: 1 ping per 30 seconds

## Error Codes

### Connection Errors
- **AUTH_FAILED**: Invalid or expired authentication token
- **SESSION_LIMIT_EXCEEDED**: Too many concurrent sessions
- **RATE_LIMIT_EXCEEDED**: Message rate limit exceeded
- **CONNECTION_TIMEOUT**: Connection idle timeout

### Business Logic Errors  
- **HERO_RULES_NOT_FOUND**: No coaching rules for selected hero
- **INVALID_GAME_MODE**: Unsupported game mode for real-time coaching
- **TEAM_SESSION_FULL**: Team session at capacity
- **INSUFFICIENT_PERMISSIONS**: User lacks required permissions

### System Errors
- **SERVICE_UNAVAILABLE**: Backend service temporarily unavailable
- **PROCESSING_ERROR**: Error processing coaching analysis
- **DATA_CORRUPTION**: Corrupted message or data format

## Client Implementation Examples

### JavaScript/TypeScript Client
```typescript
class MLBBCoachingClient {
  private ws: WebSocket;
  private sessionId: string;
  private messageQueue: Map<string, PendingMessage> = new Map();

  connect(token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(`wss://api.mlbbcoach.ai/v2/ws/realtime-coaching?token=${token}`);
      
      this.ws.onopen = () => {
        this.startHeartbeat();
        resolve();
      };
      
      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      };
      
      this.ws.onerror = reject;
    });
  }

  startSession(heroId: string, preferences: CoachingPreferences): void {
    this.sendMessage({
      type: 'session_start',
      data: {
        hero_id: heroId,
        preferences: preferences
      }
    });
  }

  private sendMessage(message: Partial<BaseMessage>): void {
    const fullMessage: BaseMessage = {
      id: generateId(),
      timestamp: new Date().toISOString(),
      session_id: this.sessionId,
      ...message
    };
    
    this.ws.send(JSON.stringify(fullMessage));
  }
}
```

### React Hook Implementation
```typescript
export function useRealtimeCoaching(heroId: string) {
  const [client, setClient] = useState<MLBBCoachingClient | null>(null);
  const [coachingTips, setCoachingTips] = useState<CoachingTip[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  useEffect(() => {
    const coaching = new MLBBCoachingClient();
    
    coaching.connect(authToken).then(() => {
      setConnectionStatus('connected');
      coaching.startSession(heroId, userPreferences);
      setClient(coaching);
    });

    coaching.onCoachingTip = (tip: CoachingTip) => {
      setCoachingTips(prev => [...prev, tip].slice(-10)); // Keep last 10 tips
    };

    return () => {
      coaching.disconnect();
      setConnectionStatus('disconnected');
    };
  }, [heroId]);

  return {
    client,
    coachingTips,
    connectionStatus,
    acknowledgeCoaching: (tipId: string, helpful: boolean) => {
      client?.acknowledgeCoaching(tipId, helpful);
    }
  };
}
```

## Performance Specifications

### Latency Requirements
- **Message delivery**: <200ms average, <500ms 95th percentile
- **Coaching response**: <150ms from trigger event
- **Connection establishment**: <2s 
- **Heartbeat interval**: 30s

### Throughput Requirements
- **Concurrent connections**: 1,000 per server instance
- **Messages per second**: 10,000 across all connections
- **Peak coaching load**: 50 tips per second system-wide

### Reliability Requirements
- **Connection uptime**: 99.9%
- **Message delivery**: 99.95% for critical messages
- **Automatic reconnection**: <5s recovery time
- **Graceful degradation**: Fallback to polling if WebSocket fails

This WebSocket protocol provides the foundation for real-time coaching and team collaboration features in the enhanced MLBB Coach AI system.