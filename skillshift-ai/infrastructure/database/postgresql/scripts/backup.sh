#!/bin/bash

# PostgreSQL Backup Script
# Creates compressed backups with rotation

set -e

# Configuration
BACKUP_DIR="/backups"
DB_HOST="postgres-primary"
DB_PORT="5432"
DB_NAME="mlbb_coach_ai"
DB_USER="mlbb_user"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="mlbb_coach_ai_backup_${TIMESTAMP}.sql.gz"

echo "🗄️  Starting database backup: $BACKUP_FILE"

# Create compressed backup
pg_dump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --verbose \
    --format=custom \
    --no-owner \
    --no-privileges \
    --compress=9 \
    --file="$BACKUP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Backup completed: $BACKUP_FILE"
    
    # Get backup size
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    echo "📊 Backup size: $BACKUP_SIZE"
    
    # Clean up old backups
    echo "🧹 Cleaning up backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -name "mlbb_coach_ai_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
    
    # List remaining backups
    echo "📁 Available backups:"
    ls -lh "$BACKUP_DIR"/mlbb_coach_ai_backup_*.sql.gz | tail -10
    
else
    echo "❌ Backup failed!"
    exit 1
fi
