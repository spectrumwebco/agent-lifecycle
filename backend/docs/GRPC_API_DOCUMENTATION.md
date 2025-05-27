# Agent Runtime gRPC API Documentation

This document provides comprehensive documentation for the Agent Runtime gRPC API, which enables communication between the Django backend and frontend applications (React web app, Electron desktop app, and Lynx mobile app).

## Overview

The Agent Runtime gRPC API provides a standardized interface for executing agent tasks, monitoring task status, and managing task execution. It is implemented using a combination of:

1. **Proto Definitions**: Standard gRPC protocol buffer definitions
2. **Django Ninja API**: REST endpoints that implement the gRPC interface
3. **WebSocket Communication**: Real-time updates for task progress and events
4. **Pydantic Integration**: Type-safe data validation and serialization

## Authentication

All API endpoints require authentication using an API key. The API key should be provided in the `X-API-Key` header for REST endpoints.

```python
headers = {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key'
}
```

For WebSocket connections, the API key should be provided as a query parameter:

```
ws://localhost:8000/ws/agent/client-id/?api_key=your-api-key
```

## API Endpoints

### Execute Task

Executes a task using the agent runtime.

**REST Endpoint**: `POST /ninja-api/grpc/execute_task`

**Request**:
```json
{
  "prompt": "Create a Python function to calculate factorial",
  "context": {
    "language": "python",
    "complexity": "medium"
  },
  "tools": ["code_generation", "code_explanation"]
}
```

**Response**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "message": "Task submitted for execution"
}
```

### Get Task Status

Gets the status of a task.

**REST Endpoint**: `POST /ninja-api/grpc/get_task_status`

**Request**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "result": null,
  "events": ["Task created", "Processing started"]
}
```

### Cancel Task

Cancels a running task.

**REST Endpoint**: `POST /ninja-api/grpc/cancel_task`

**Request**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "message": "Task cancelled successfully"
}
```

## WebSocket API

The WebSocket API provides real-time updates for task progress and events.

### Connection

Connect to the WebSocket API using the following URL:

```
ws://localhost:8000/ws/agent/<client_id>/
```

Or for task-specific updates:

```
ws://localhost:8000/ws/agent/<client_id>/<task_id>/
```

### Messages

#### Connection Established

Sent when a WebSocket connection is established:

```json
{
  "type": "connection_established",
  "message": "Connected as client-123",
  "client_id": "client-123",
  "task_id": "task-456"
}
```

#### Task Update

Sent when a task status is updated:

```json
{
  "type": "task_update",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "message": "Processing step 2 of 5",
  "sender": "system"
}
```

#### Broadcast Message

Sent to all connected clients:

```json
{
  "type": "broadcast",
  "message": "System maintenance scheduled in 10 minutes",
  "sender": "system"
}
```

## Client Example

Here's an example of how to use the Agent Runtime API client:

```python
from agent_runtime_client import AgentRuntimeClient

# Initialize client
client = AgentRuntimeClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Execute a task
task_response = client.execute_task(
    prompt="Create a Python function to calculate factorial",
    context={"language": "python"},
    tools=["code_generation"]
)

task_id = task_response['task_id']
print(f"Task submitted with ID: {task_id}")

# Wait for task completion
final_status = client.wait_for_task_completion(task_id)
print(f"Task completed with status: {final_status['status']}")
if final_status['result']:
    print(f"Result: {final_status['result']}")
```

## Pydantic Integration

The API uses Pydantic models for request and response validation. This ensures type safety and proper validation of all data passing through the API.

Example Pydantic model:

```python
from pydantic import BaseModel
from typing import Dict, List, Optional

class ExecuteTaskRequest(BaseModel):
    prompt: str
    context: Optional[Dict[str, str]] = None
    tools: Optional[List[str]] = None
```

## Error Handling

The API returns standard HTTP status codes for errors:

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid or missing API key
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a message explaining the error:

```json
{
  "detail": "Invalid task_id format"
}
```

## Generating gRPC Code

To generate Python gRPC code from the proto files, use the provided script:

```bash
python django_backend/scripts/generate_grpc_code.py
```

This will generate the necessary Python code in the `django_backend/api/generated` directory.

## Running the Server

To run the server with WebSocket support, use the provided management command:

```bash
python manage.py runserver_daphne
```

This will start the server on `0.0.0.0:8000` with both HTTP and WebSocket support.
