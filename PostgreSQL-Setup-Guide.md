# 🐘 **PostgreSQL Setup Guide for MLBB AI Project**

**Complete Beginner's Guide to Setting Up PostgreSQL for SkillShift AI**

---

## **📋 What We'll Build**

By the end of this guide, you'll have:
- PostgreSQL running on your macOS
- A dedicated database for your MLBB AI project
- Python connection working with sample data
- Understanding of how to manage your database
- Foundation for adding Redis caching later

---

## **📦 Step 1: Install PostgreSQL via Homebrew**

### **1.1 Install Homebrew (if you don't have it)**

```bash
# Check if you have Homebrew
brew --version

# If not installed, install it:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### **1.2 Install PostgreSQL**

```bash
# Install PostgreSQL (this gets the latest stable version)
brew install postgresql@15

# Start PostgreSQL service (this runs it in the background)
brew services start postgresql@15
```

**What this does:**
- Downloads and installs PostgreSQL version 15
- Sets it up to run automatically when your Mac starts
- Creates initial system databases

### **1.3 Verify Installation**

```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# You should see something like:
# postgresql@15  started  your-username  ~/Library/LaunchAgents/homebrew.mxcl.postgresql@15.plist
```

---

## **🔧 Step 2: Initial Database Setup**

### **2.1 Connect to PostgreSQL**

```bash
# Connect as the default superuser (your macOS username)
psql postgres

# You should see a prompt like:
# postgres=#
```

**What this does:**
- `psql` is the PostgreSQL command-line interface
- `postgres` is the default database that always exists
- You're now inside the PostgreSQL shell

### **2.2 Create Your Project Database and User**

Inside the PostgreSQL shell (`postgres=#`), run these commands:

```sql
-- Create a new user for your MLBB project
CREATE USER mlbb_admin WITH PASSWORD 'your_secure_password_here';

-- Create your project database
CREATE DATABASE mlbb_coaching_db OWNER mlbb_admin;

-- Give your user permission to create additional databases (useful for testing)
ALTER USER mlbb_admin CREATEDB;

-- Connect to your new database
\c mlbb_coaching_db

-- Grant all privileges on your database to your user
GRANT ALL PRIVILEGES ON DATABASE mlbb_coaching_db TO mlbb_admin;
GRANT ALL ON SCHEMA public TO mlbb_admin;

-- Exit PostgreSQL shell
\q
```

**What each command does:**
- `CREATE USER`: Makes a new database user (like a login account)
- `CREATE DATABASE`: Creates your project's database
- `GRANT`: Gives permissions to your user
- `\c`: Connects to a different database
- `\q`: Quits the PostgreSQL shell

### **2.3 Test Your New User Connection**

```bash
# Connect using your new user credentials
psql -U mlbb_admin -d mlbb_coaching_db -h localhost

# Enter the password when prompted
# You should see: mlbb_coaching_db=#
```

---

## **🗂️ Step 3: Create Your Database Schema**

### **3.1 Design Your Main Table**

Still in the PostgreSQL shell, create your main table:

```sql
-- Create the match analyses table
CREATE TABLE match_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    hero_name VARCHAR(50) NOT NULL,
    performance_metrics JSONB NOT NULL,
    coaching_feedback JSONB NOT NULL,
    meta_version VARCHAR(20) NOT NULL DEFAULT '1.8.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_match_analyses_user_id ON match_analyses(user_id);
CREATE INDEX idx_match_analyses_hero ON match_analyses(hero_name);
CREATE INDEX idx_match_analyses_created_at ON match_analyses(created_at);

-- Index for searching inside JSON data
CREATE INDEX idx_match_analyses_performance ON match_analyses USING GIN(performance_metrics);
CREATE INDEX idx_match_analyses_feedback ON match_analyses USING GIN(coaching_feedback);
```

**What this creates:**
- `id`: Unique identifier for each analysis
- `user_id`: Links to a specific player
- `hero_name`: Which MLBB hero was analyzed
- `performance_metrics`: JSON data with stats (KDA, GPM, etc.)
- `coaching_feedback`: JSON data with advice and recommendations
- `meta_version`: Tracks which game version the analysis is for
- `created_at/updated_at`: Timestamps for data tracking

### **3.2 Create Additional Helper Tables**

```sql
-- Create a users table for player profiles
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    ign VARCHAR(100), -- In-game name
    preferred_role VARCHAR(20),
    skill_level VARCHAR(20) DEFAULT 'beginner',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create a heroes table for metadata
CREATE TABLE heroes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL,
    difficulty VARCHAR(20) DEFAULT 'medium',
    is_active BOOLEAN DEFAULT true,
    meta_tier VARCHAR(1) DEFAULT 'C'
);

-- Create sessions table for tracking analysis sessions
CREATE TABLE analysis_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_name VARCHAR(100),
    total_analyses INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);
```

### **3.3 Insert Sample Heroes Data**

```sql
-- Add some MLBB heroes
INSERT INTO heroes (name, role, difficulty, meta_tier) VALUES
('Miya', 'Marksman', 'easy', 'B'),
('Hayabusa', 'Assassin', 'hard', 'A'),
('Chou', 'Fighter', 'hard', 'S'),
('Franco', 'Tank', 'medium', 'A'),
('Kagura', 'Mage', 'hard', 'S'),
('Estes', 'Support', 'easy', 'B');
```

---

## **🐍 Step 4: Connect from Python**

### **4.1 Install Required Python Packages**

```bash
# Navigate to your project directory
cd /Users/lesz/Documents/Project-AI/skillshift-ai

# Install database packages
pip install asyncpg sqlalchemy[asyncio] psycopg2-binary
```

### **4.2 Create Database Connection Module**

Create a new file: `core/database.py`

```python
# core/database.py
import asyncio
import asyncpg
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

class DatabaseManager:
    """Manages PostgreSQL connections for MLBB AI project."""
    
    def __init__(self):
        self.pool = None
        self.connection_params = {
            'host': 'localhost',
            'port': 5432,
            'user': 'mlbb_admin',
            'password': 'your_secure_password_here',  # Replace with your password
            'database': 'mlbb_coaching_db'
        }
    
    async def initialize(self):
        """Create connection pool."""
        try:
            self.pool = await asyncpg.create_pool(**self.connection_params)
            print("✅ Database connection pool created successfully")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            print("🔒 Database connection pool closed")
    
    async def create_user(self, username: str, ign: str = None, 
                         preferred_role: str = None) -> str:
        """Create a new user and return their ID."""
        async with self.pool.acquire() as conn:
            user_id = await conn.fetchval("""
                INSERT INTO users (username, ign, preferred_role)
                VALUES ($1, $2, $3)
                RETURNING id
            """, username, ign, preferred_role)
            return str(user_id)
    
    async def save_match_analysis(self, user_id: str, hero_name: str,
                                performance_metrics: Dict[str, Any],
                                coaching_feedback: Dict[str, Any],
                                meta_version: str = "1.8.0") -> str:
        """Save a match analysis and return the analysis ID."""
        async with self.pool.acquire() as conn:
            analysis_id = await conn.fetchval("""
                INSERT INTO match_analyses 
                (user_id, hero_name, performance_metrics, coaching_feedback, meta_version)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, 
            uuid.UUID(user_id), 
            hero_name, 
            json.dumps(performance_metrics),
            json.dumps(coaching_feedback),
            meta_version)
            return str(analysis_id)
    
    async def get_user_analyses(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent analyses for a user."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, hero_name, performance_metrics, coaching_feedback, 
                       meta_version, created_at
                FROM match_analyses 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT $2
            """, uuid.UUID(user_id), limit)
            
            return [dict(row) for row in rows]
    
    async def get_hero_statistics(self, hero_name: str) -> Dict[str, Any]:
        """Get aggregated statistics for a hero."""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_analyses,
                    AVG((performance_metrics->>'kda')::float) as avg_kda,
                    AVG((performance_metrics->>'gpm')::float) as avg_gpm,
                    MAX(created_at) as last_analysis
                FROM match_analyses 
                WHERE hero_name = $1
                AND performance_metrics->>'kda' IS NOT NULL
            """, hero_name)
            
            return dict(stats) if stats else {}

# Global database instance
db_manager = DatabaseManager()
```

### **4.3 Create Test Script**

Create `test_database.py` in your project root:

```python
# test_database.py
import asyncio
from core.database import db_manager

async def test_database_operations():
    """Test all database operations."""
    
    try:
        # Initialize database connection
        await db_manager.initialize()
        print("🔌 Connected to database successfully!")
        
        # Test 1: Create a test user
        print("\n📝 Creating test user...")
        user_id = await db_manager.create_user(
            username="test_player_1",
            ign="TestPro2024",
            preferred_role="Assassin"
        )
        print(f"✅ Created user with ID: {user_id}")
        
        # Test 2: Save sample match analysis
        print("\n💾 Saving match analysis...")
        
        sample_performance = {
            "kills": 8,
            "deaths": 2,
            "assists": 12,
            "kda": 10.0,
            "gpm": 650,
            "hero_damage": 45000,
            "match_duration": 18
        }
        
        sample_feedback = {
            "overall_rating": "Excellent",
            "strengths": ["Great KDA ratio", "Good farm efficiency"],
            "improvements": ["Focus on turret damage", "Improve late game positioning"],
            "severity_levels": {
                "critical": 0,
                "warning": 1,
                "info": 2,
                "success": 2
            }
        }
        
        analysis_id = await db_manager.save_match_analysis(
            user_id=user_id,
            hero_name="Hayabusa",
            performance_metrics=sample_performance,
            coaching_feedback=sample_feedback
        )
        print(f"✅ Saved analysis with ID: {analysis_id}")
        
        # Test 3: Save another analysis for comparison
        print("\n💾 Saving second analysis...")
        
        sample_performance_2 = {
            "kills": 12,
            "deaths": 1,
            "assists": 8,
            "kda": 20.0,
            "gpm": 750,
            "hero_damage": 52000,
            "match_duration": 20
        }
        
        sample_feedback_2 = {
            "overall_rating": "Outstanding",
            "strengths": ["Perfect execution", "Exceptional farm", "Dominated teamfights"],
            "improvements": ["Maintain consistency"],
            "severity_levels": {
                "critical": 0,
                "warning": 0,
                "info": 1,
                "success": 4
            }
        }
        
        analysis_id_2 = await db_manager.save_match_analysis(
            user_id=user_id,
            hero_name="Hayabusa",
            performance_metrics=sample_performance_2,
            coaching_feedback=sample_feedback_2
        )
        print(f"✅ Saved second analysis with ID: {analysis_id_2}")
        
        # Test 4: Retrieve user's analyses
        print("\n📊 Retrieving user analyses...")
        analyses = await db_manager.get_user_analyses(user_id)
        print(f"✅ Found {len(analyses)} analyses for user")
        
        for i, analysis in enumerate(analyses, 1):
            print(f"\nAnalysis {i}:")
            print(f"  Hero: {analysis['hero_name']}")
            print(f"  KDA: {analysis['performance_metrics']['kda']}")
            print(f"  Rating: {analysis['coaching_feedback']['overall_rating']}")
            print(f"  Date: {analysis['created_at']}")
        
        # Test 5: Get hero statistics
        print("\n📈 Getting hero statistics...")
        hero_stats = await db_manager.get_hero_statistics("Hayabusa")
        print(f"✅ Hayabusa Statistics:")
        print(f"  Total Analyses: {hero_stats.get('total_analyses', 0)}")
        print(f"  Average KDA: {hero_stats.get('avg_kda', 0):.2f}")
        print(f"  Average GPM: {hero_stats.get('avg_gpm', 0):.2f}")
        
        print("\n🎉 All database tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Always close the database connection
        await db_manager.close()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_database_operations())
```

---

## **🧪 Step 5: Test Your Setup**

### **5.1 Run the Test Script**

```bash
# Make sure you're in your project directory
cd /Users/lesz/Documents/Project-AI/skillshift-ai

# Run the database test
python test_database.py
```

**Expected Output:**
```
🔌 Connected to database successfully!

📝 Creating test user...
✅ Created user with ID: 550e8400-e29b-41d4-a716-446655440000

💾 Saving match analysis...
✅ Saved analysis with ID: 6ba7b810-9dad-11d1-80b4-00c04fd430c8

💾 Saving second analysis...
✅ Saved second analysis with ID: 6ba7b811-9dad-11d1-80b4-00c04fd430c8

📊 Retrieving user analyses...
✅ Found 2 analyses for user

Analysis 1:
  Hero: Hayabusa
  KDA: 20.0
  Rating: Outstanding
  Date: 2025-01-12 10:30:45.123456+00:00

Analysis 2:
  Hero: Hayabusa
  KDA: 10.0
  Rating: Excellent
  Date: 2025-01-12 10:30:44.123456+00:00

📈 Getting hero statistics...
✅ Hayabusa Statistics:
  Total Analyses: 2
  Average KDA: 15.00
  Average GPM: 700.00

🎉 All database tests passed successfully!
🔒 Database connection pool closed
```

### **5.2 Manual Database Queries**

You can also query your data manually:

```bash
# Connect to your database
psql -U mlbb_admin -d mlbb_coaching_db -h localhost

# Run some queries
\dt  -- List all tables

SELECT * FROM users;
SELECT * FROM heroes;
SELECT id, hero_name, created_at FROM match_analyses;

# Query JSON data
SELECT 
    hero_name,
    performance_metrics->>'kda' as kda,
    coaching_feedback->>'overall_rating' as rating
FROM match_analyses;

\q  -- Exit
```

---

## **🛠️ Troubleshooting Common Issues**

### **Issue 1: "psql: command not found"**

```bash
# Add PostgreSQL to your PATH
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Or use the full path
/opt/homebrew/bin/psql postgres
```

### **Issue 2: "Connection refused"**

```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# If not running, start it
brew services start postgresql@15

# Check the logs if it won't start
brew services info postgresql@15
```

### **Issue 3: "Password authentication failed"**

```bash
# Reset your user password
psql postgres -c "ALTER USER mlbb_admin PASSWORD 'new_password';"

# Update your Python code with the new password
```

### **Issue 4: "Permission denied for schema public"**

```sql
-- Connect as superuser and grant permissions
psql postgres
GRANT ALL ON SCHEMA public TO mlbb_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mlbb_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mlbb_admin;
```

---

## **💡 GUI Database Clients**

### **Option 1: pgAdmin (Free)**

```bash
# Install pgAdmin
brew install --cask pgadmin4

# Launch it and add your server:
# Host: localhost
# Port: 5432
# Database: mlbb_coaching_db
# Username: mlbb_admin
# Password: your_password
```

### **Option 2: TablePlus (Paid, but excellent)**

1. Download from [TablePlus website](https://tableplus.com/)
2. Create new connection:
   - Host: `localhost`
   - Port: `5432`
   - User: `mlbb_admin`
   - Password: `your_password`
   - Database: `mlbb_coaching_db`

### **Option 3: DBeaver (Free)**

```bash
# Install DBeaver
brew install --cask dbeaver-community

# Configure connection with same credentials as above
```

---

## **🧹 How to Reset Everything**

### **If You Need to Start Over:**

```bash
# Stop PostgreSQL
brew services stop postgresql@15

# Remove all data (CAREFUL - this deletes everything!)
rm -rf /opt/homebrew/var/postgresql@15

# Reinitialize PostgreSQL
brew services start postgresql@15

# Or just drop and recreate your database
psql postgres -c "DROP DATABASE IF EXISTS mlbb_coaching_db;"
psql postgres -c "DROP USER IF EXISTS mlbb_admin;"

# Then follow the setup steps again
```

---

## **🔧 Development Configuration**

### **Recommended Settings for Development**

Create a `.env` file in your project:

```bash
# .env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mlbb_coaching_db
DB_USER=mlbb_admin
DB_PASSWORD=your_secure_password_here
DB_POOL_MIN_SIZE=5
DB_POOL_MAX_SIZE=20
```

### **Updated Database Manager with Environment Variables**

```python
# core/database.py (updated version)
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.pool = None
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'mlbb_admin'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME', 'mlbb_coaching_db'),
            'min_size': int(os.getenv('DB_POOL_MIN_SIZE', 5)),
            'max_size': int(os.getenv('DB_POOL_MAX_SIZE', 20))
        }
```

---

## **🔮 Next Steps: Adding Redis Cache**

Once PostgreSQL is working, you can add Redis caching:

```bash
# Install Redis
brew install redis
brew services start redis

# Install Python Redis package
pip install redis

# Test Redis connection
redis-cli ping  # Should return "PONG"
```

Your caching strategy will look like:
1. **Check Redis** for cached analysis results
2. **If not cached**, run analysis and save to PostgreSQL
3. **Cache the result** in Redis for future requests
4. **Use PostgreSQL** for complex queries and historical data

---

## **🎉 Success Checklist**

- ✅ PostgreSQL installed and running
- ✅ Database and user created
- ✅ Python connection working
- ✅ Sample data inserted and queried
- ✅ Understanding of basic SQL operations
- ✅ GUI client connected (optional)
- ✅ Environment variables configured

**You're now ready to integrate this database with your MLBB AI coaching system!**

The database will store your match analyses, user profiles, and coaching feedback, while Redis (when you add it) will handle caching for fast responses. This foundation will scale with your project as it grows.