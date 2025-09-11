"""
Database Connection Manager for MLBB Coach AI
Advanced connection pooling, read/write splitting, and performance optimization
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncpg
import psycopg2
from psycopg2 import pool
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """Database connection types."""
    READ_WRITE = "read_write"
    READ_ONLY = "read_only"
    ANALYTICS = "analytics"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str
    port: int = 5432
    database: str = "mlbb_coach_ai"
    username: str = "mlbb_user"
    password: str = "mlbb_password_2025"
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False


@dataclass
class ConnectionStats:
    """Connection pool statistics."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    checked_out: int = 0
    overflow: int = 0
    invalidated: int = 0


class DatabaseConnectionManager:
    """Advanced database connection manager with read/write splitting."""
    
    def __init__(
        self,
        primary_config: DatabaseConfig,
        replica_configs: List[DatabaseConfig] = None,
        use_pgbouncer: bool = True,
        pgbouncer_host: str = "localhost",
        pgbouncer_port: int = 6432
    ):
        """Initialize connection manager."""
        self.primary_config = primary_config
        self.replica_configs = replica_configs or []
        self.use_pgbouncer = use_pgbouncer
        self.pgbouncer_host = pgbouncer_host
        self.pgbouncer_port = pgbouncer_port
        
        # Connection pools
        self.engines: Dict[ConnectionType, Any] = {}
        self.async_engines: Dict[ConnectionType, Any] = {}
        self.session_makers: Dict[ConnectionType, Any] = {}
        
        # Statistics
        self.stats: Dict[ConnectionType, ConnectionStats] = {}
        
        # Health monitoring
        self.health_status: Dict[str, bool] = {}
        self.last_health_check = {}
        
        # Read replica round-robin index
        self.replica_index = 0
        
    async def initialize(self):
        """Initialize database connections and pools."""
        try:
            # Initialize primary (read-write) connections
            await self._initialize_primary_connections()
            
            # Initialize replica (read-only) connections
            await self._initialize_replica_connections()
            
            # Initialize analytics connections (if separate)
            await self._initialize_analytics_connections()
            
            # Start health monitoring
            asyncio.create_task(self._monitor_health())
            
            logger.info("Database connection manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    async def _initialize_primary_connections(self):
        """Initialize primary database connections."""
        if self.use_pgbouncer:
            # Use PgBouncer for connection pooling
            primary_url = self._build_connection_url(
                host=self.pgbouncer_host,
                port=self.pgbouncer_port,
                database=self.primary_config.database,
                username=self.primary_config.username,
                password=self.primary_config.password
            )
        else:
            # Direct connection to primary
            primary_url = self._build_connection_url(
                host=self.primary_config.host,
                port=self.primary_config.port,
                database=self.primary_config.database,
                username=self.primary_config.username,
                password=self.primary_config.password
            )
        
        # Create SQLAlchemy engines
        self.engines[ConnectionType.READ_WRITE] = create_engine(
            primary_url,
            poolclass=QueuePool,
            pool_size=self.primary_config.pool_size,
            max_overflow=self.primary_config.max_overflow,
            pool_timeout=self.primary_config.pool_timeout,
            pool_recycle=self.primary_config.pool_recycle,
            echo=self.primary_config.echo
        )
        
        # Async engine
        async_primary_url = primary_url.replace("postgresql://", "postgresql+asyncpg://")
        self.async_engines[ConnectionType.READ_WRITE] = create_async_engine(
            async_primary_url,
            pool_size=self.primary_config.pool_size,
            max_overflow=self.primary_config.max_overflow,
            pool_timeout=self.primary_config.pool_timeout,
            pool_recycle=self.primary_config.pool_recycle,
            echo=self.primary_config.echo
        )
        
        # Session makers
        self.session_makers[ConnectionType.READ_WRITE] = sessionmaker(
            bind=self.engines[ConnectionType.READ_WRITE]
        )
        
        logger.info("Primary database connections initialized")
    
    async def _initialize_replica_connections(self):
        """Initialize read replica connections."""
        if not self.replica_configs:
            # Use primary for read-only queries if no replicas configured
            self.engines[ConnectionType.READ_ONLY] = self.engines[ConnectionType.READ_WRITE]
            self.async_engines[ConnectionType.READ_ONLY] = self.async_engines[ConnectionType.READ_WRITE]
            self.session_makers[ConnectionType.READ_ONLY] = self.session_makers[ConnectionType.READ_WRITE]
            logger.info("No replicas configured, using primary for read-only queries")
            return
        
        # Use first replica for read-only connections
        replica_config = self.replica_configs[0]
        
        if self.use_pgbouncer:
            # Use PgBouncer read-only database
            replica_url = self._build_connection_url(
                host=self.pgbouncer_host,
                port=self.pgbouncer_port,
                database=f"{replica_config.database}_ro",
                username=replica_config.username,
                password=replica_config.password
            )
        else:
            # Direct connection to replica
            replica_url = self._build_connection_url(
                host=replica_config.host,
                port=replica_config.port,
                database=replica_config.database,
                username=replica_config.username,
                password=replica_config.password
            )
        
        # Create SQLAlchemy engines for read-only
        self.engines[ConnectionType.READ_ONLY] = create_engine(
            replica_url,
            poolclass=QueuePool,
            pool_size=replica_config.pool_size,
            max_overflow=replica_config.max_overflow,
            pool_timeout=replica_config.pool_timeout,
            pool_recycle=replica_config.pool_recycle,
            echo=replica_config.echo
        )
        
        # Async engine
        async_replica_url = replica_url.replace("postgresql://", "postgresql+asyncpg://")
        self.async_engines[ConnectionType.READ_ONLY] = create_async_engine(
            async_replica_url,
            pool_size=replica_config.pool_size,
            max_overflow=replica_config.max_overflow,
            pool_timeout=replica_config.pool_timeout,
            pool_recycle=replica_config.pool_recycle,
            echo=replica_config.echo
        )
        
        # Session makers
        self.session_makers[ConnectionType.READ_ONLY] = sessionmaker(
            bind=self.engines[ConnectionType.READ_ONLY]
        )
        
        logger.info("Read replica connections initialized")
    
    async def _initialize_analytics_connections(self):
        """Initialize analytics connections (typically pointing to replica)."""
        # For now, use read-only connections for analytics
        self.engines[ConnectionType.ANALYTICS] = self.engines[ConnectionType.READ_ONLY]
        self.async_engines[ConnectionType.ANALYTICS] = self.async_engines[ConnectionType.READ_ONLY]
        self.session_makers[ConnectionType.ANALYTICS] = self.session_makers[ConnectionType.READ_ONLY]
        
        logger.info("Analytics connections initialized")
    
    def _build_connection_url(
        self, 
        host: str, 
        port: int, 
        database: str, 
        username: str, 
        password: str
    ) -> str:
        """Build database connection URL."""
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    @asynccontextmanager
    async def get_connection(self, connection_type: ConnectionType = ConnectionType.READ_WRITE):
        """Get database connection with context manager."""
        engine = self.async_engines.get(connection_type)
        if not engine:
            raise ValueError(f"No engine configured for connection type: {connection_type}")
        
        async with engine.begin() as conn:
            try:
                yield conn
            except Exception as e:
                logger.error(f"Database error in {connection_type.value} connection: {e}")
                raise
    
    @asynccontextmanager
    async def get_session(self, connection_type: ConnectionType = ConnectionType.READ_WRITE):
        """Get database session with context manager."""
        engine = self.async_engines.get(connection_type)
        if not engine:
            raise ValueError(f"No engine configured for connection type: {connection_type}")
        
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error in {connection_type.value}: {e}")
                raise
    
    async def execute_query(
        self, 
        query: str, 
        params: Dict[str, Any] = None,
        connection_type: ConnectionType = ConnectionType.READ_ONLY
    ) -> List[Dict[str, Any]]:
        """Execute query and return results."""
        async with self.get_connection(connection_type) as conn:
            result = await conn.execute(text(query), params or {})
            return [dict(row._mapping) for row in result.fetchall()]
    
    async def execute_command(
        self,
        command: str,
        params: Dict[str, Any] = None,
        connection_type: ConnectionType = ConnectionType.READ_WRITE
    ) -> int:
        """Execute command and return affected rows count."""
        async with self.get_connection(connection_type) as conn:
            result = await conn.execute(text(command), params or {})
            return result.rowcount
    
    async def get_connection_stats(self) -> Dict[str, ConnectionStats]:
        """Get connection pool statistics."""
        stats = {}
        
        for conn_type, engine in self.engines.items():
            pool = engine.pool
            stats[conn_type.value] = ConnectionStats(
                total_connections=pool.size(),
                active_connections=pool.checkedout(),
                idle_connections=pool.checkedin(),
                checked_out=pool.checkedout(),
                overflow=pool.overflow(),
                invalidated=pool.invalidated()
            )
        
        return stats
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all database connections."""
        health = {}
        
        for conn_type, engine in self.async_engines.items():
            try:
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                health[conn_type.value] = True
                self.health_status[conn_type.value] = True
            except Exception as e:
                logger.error(f"Health check failed for {conn_type.value}: {e}")
                health[conn_type.value] = False
                self.health_status[conn_type.value] = False
        
        return health
    
    async def _monitor_health(self):
        """Background task to monitor database health."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self.health_check()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
    
    async def close(self):
        """Close all database connections."""
        try:
            for engine in self.async_engines.values():
                await engine.dispose()
            
            for engine in self.engines.values():
                engine.dispose()
            
            logger.info("Database connections closed")
            
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")


# Global connection manager instance
_connection_manager: Optional[DatabaseConnectionManager] = None


async def get_connection_manager() -> DatabaseConnectionManager:
    """Get global connection manager instance."""
    global _connection_manager
    
    if _connection_manager is None:
        # Default configuration
        primary_config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="mlbb_coach_ai",
            username="mlbb_user",
            password="mlbb_password_2025",
            pool_size=20,
            max_overflow=30
        )
        
        replica_configs = [
            DatabaseConfig(
                host="localhost",
                port=5433,
                database="mlbb_coach_ai",
                username="mlbb_user",
                password="mlbb_password_2025",
                pool_size=15,
                max_overflow=20
            )
        ]
        
        _connection_manager = DatabaseConnectionManager(
            primary_config=primary_config,
            replica_configs=replica_configs,
            use_pgbouncer=True
        )
        
        await _connection_manager.initialize()
    
    return _connection_manager


# Convenience functions
async def execute_query(
    query: str,
    params: Dict[str, Any] = None,
    read_only: bool = True
) -> List[Dict[str, Any]]:
    """Execute query using global connection manager."""
    manager = await get_connection_manager()
    connection_type = ConnectionType.READ_ONLY if read_only else ConnectionType.READ_WRITE
    return await manager.execute_query(query, params, connection_type)


async def execute_command(
    command: str,
    params: Dict[str, Any] = None
) -> int:
    """Execute command using global connection manager."""
    manager = await get_connection_manager()
    return await manager.execute_command(command, params, ConnectionType.READ_WRITE)
