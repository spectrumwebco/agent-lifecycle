# Agent Runtime Django Backend

This Django backend serves as the progressive consolidation platform for all Python code in the agent_runtime repository. It provides REST and gRPC APIs for interacting with the agent runtime system and ML infrastructure.

## Features

- REST API for agent runtime operations
- ML infrastructure API integration
- gRPC server for Go FFI integration
- Pydantic model integration
- Support for multiple programming languages via LibreChat Code Interpreter API

## Architecture

The Django backend is designed to progressively integrate all Python code from the agent_runtime repository, following the Manus AI agent architecture:

1. **Agent Loop** - Core execution loop for agent operation
2. **Modules** - Modular components for different capabilities
3. **Event Stream** - Processes chronological events
4. **Tool Registry** - Manages available tools and their execution

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Start the development server:
   ```bash
   python manage.py runserver
   ```

4. Start the gRPC server:
   ```bash
   python manage.py run_grpc_server
   ```

## API Endpoints

### Agent API

- `GET /api/` - API root
- `GET /api/users/` - List users
- `POST /api/tasks/` - Execute agent task

### ML API

- `GET /ml-api/` - ML API root
- `GET /ml-api/models/` - List ML models
- `GET /ml-api/models/{id}/` - Get ML model details
- `GET /ml-api/fine-tuning-jobs/` - List fine-tuning jobs
- `POST /ml-api/fine-tuning-jobs/` - Create fine-tuning job
- `GET /ml-api/fine-tuning-jobs/{id}/` - Get fine-tuning job details
- `POST /ml-api/fine-tuning-jobs/{id}/cancel/` - Cancel fine-tuning job

## Integration with Go Codebase

The Django backend integrates with the Go codebase through:

1. **gRPC Server** - Provides gRPC endpoints for Go FFI integration
2. **Pydantic Models** - Shared data models between Python and Go
3. **FFI System** - Enables execution of Python code from Go

## Multi-Language Support

The backend supports multiple programming languages for code execution:

- Python
- C++
- C#
- TypeScript
- Go
- Rust
- PHP

This is enabled through integration with the LibreChat Code Interpreter API.
