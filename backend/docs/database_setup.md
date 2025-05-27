# Database Setup and Verification

This document explains the database setup and verification process for the Agent Runtime system.

## Database Architecture

The Agent Runtime system uses the following databases:

1. **Supabase (PostgreSQL)** - Four separate databases for different components:
   - Default database - General Django data
   - Agent database - Agent-specific data
   - Trajectory database - Trajectory data
   - ML database - Machine learning data

2. **DragonflyDB** - Redis replacement with memcached functionality
   - Used for Django channels and caching
   - Provides high-performance key-value storage

3. **RAGflow** - Vector database with deep search capabilities
   - Used for semantic search and retrieval
   - Stores embeddings and vector data

4. **RocketMQ** - Go-based messaging system
   - Used for state communication between components
   - Provides reliable message delivery

## Local Development Setup

For local development, the system uses MariaDB as a fallback when Supabase is not available:

```bash
# Install MariaDB
sudo apt-get install -y mariadb-server

# Start MariaDB service
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Create databases and users
sudo mysql -e "CREATE DATABASE IF NOT EXISTS agent_runtime;
CREATE DATABASE IF NOT EXISTS agent_db;
CREATE DATABASE IF NOT EXISTS trajectory_db;
CREATE DATABASE IF NOT EXISTS ml_db;
CREATE USER IF NOT EXISTS 'agent_user'@'localhost' IDENTIFIED BY 'agent_password';
GRANT ALL PRIVILEGES ON agent_runtime.* TO 'agent_user'@'localhost';
GRANT ALL PRIVILEGES ON agent_db.* TO 'agent_user'@'localhost';
GRANT ALL PRIVILEGES ON trajectory_db.* TO 'agent_user'@'localhost';
GRANT ALL PRIVILEGES ON ml_db.* TO 'agent_user'@'localhost';
FLUSH PRIVILEGES;"
```

## Kubernetes Production Setup

In a Kubernetes environment, the system connects to the following services:

- **Supabase**: `supabase-db.default.svc.cluster.local:5432`
- **DragonflyDB**: `dragonfly-db.default.svc.cluster.local:6379`
- **RAGflow**: `ragflow.default.svc.cluster.local:8000`
- **RocketMQ**: `rocketmq.default.svc.cluster.local:9876`

## Database Configuration

The database configuration is defined in `agent_api/database_config.py` and includes:

- Database connection settings for all four Supabase databases
- Redis/DragonflyDB connection settings
- RAGflow vector database settings
- RocketMQ messaging settings

The configuration automatically detects whether the system is running in Kubernetes or local development and adjusts the connection settings accordingly.

## Vault Integration

The system uses Hashicorp Vault for secure credential management in production:

- Vault is used to store and retrieve database credentials
- The system falls back to configuration file settings if Vault is not available
- Vault authentication uses Kubernetes service account tokens in production
- Local development uses a simplified authentication method

## Verifying Database Connections

To verify database connections, use the following command:

```bash
python verify_db_connections.py
```

This script checks connections to all databases and reports their status. In local development, only MariaDB connections are expected to succeed, while other connections will fail unless the services are installed locally.

For Django database connections, use:

```bash
python manage.py verify_db_connections
```

## Troubleshooting

If database connections fail:

1. **Local Development**:
   - Ensure MariaDB is installed and running
   - Verify that the databases and users are created
   - Check connection settings in `database_config.py`

2. **Kubernetes Production**:
   - Verify that the services are deployed and running
   - Check Kubernetes service discovery
   - Ensure Vault is configured correctly
   - Check network policies and firewall rules
