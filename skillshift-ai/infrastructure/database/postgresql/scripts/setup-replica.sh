#!/bin/bash

# PostgreSQL Replica Setup Script
# Sets up streaming replication from primary to replica

set -e

echo "🔄 Setting up PostgreSQL replica..."

# Wait for primary to be ready
echo "⏳ Waiting for primary database to be ready..."
while ! pg_isready -h "$POSTGRES_PRIMARY_HOST" -p "$POSTGRES_PRIMARY_PORT" -U "$POSTGRES_REPLICATION_USER"; do
    echo "Waiting for primary database..."
    sleep 2
done

echo "✅ Primary database is ready"

# Check if data directory is empty (first time setup)
if [ -z "$(ls -A /var/lib/postgresql/data)" ]; then
    echo "📥 Initializing replica from primary backup..."
    
    # Create base backup from primary
    PGPASSWORD="$POSTGRES_REPLICATION_PASSWORD" pg_basebackup \
        -h "$POSTGRES_PRIMARY_HOST" \
        -p "$POSTGRES_PRIMARY_PORT" \
        -U "$POSTGRES_REPLICATION_USER" \
        -D /var/lib/postgresql/data \
        -W \
        -v \
        -P \
        -R \
        -X stream
    
    echo "✅ Base backup completed"
    
    # Set up recovery configuration
    cat > /var/lib/postgresql/data/postgresql.auto.conf << EOF
# Replica-specific settings
hot_standby = on
primary_conninfo = 'host=$POSTGRES_PRIMARY_HOST port=$POSTGRES_PRIMARY_PORT user=$POSTGRES_REPLICATION_USER password=$POSTGRES_REPLICATION_PASSWORD'
restore_command = 'cp /var/lib/postgresql/data/archive/%f %p'
archive_cleanup_command = 'pg_archivecleanup /var/lib/postgresql/data/archive %r'
EOF
    
    # Create standby.signal file to indicate this is a replica
    touch /var/lib/postgresql/data/standby.signal
    
    echo "✅ Replica configuration completed"
else
    echo "📁 Data directory not empty, assuming replica is already configured"
fi

# Set proper permissions
chown -R postgres:postgres /var/lib/postgresql/data
chmod 700 /var/lib/postgresql/data

echo "🎉 Replica setup completed successfully!"
