# Agent Runtime API Documentation

This document provides comprehensive documentation for the Agent Runtime API, designed for integration with Devin and other systems.

## Authentication

The API uses API key authentication. Include the API key in the `X-API-Key` header with all requests.

```
X-API-Key: your-api-key-here
```

For development, the default API key is `dev-api-key`. In production, a secure API key should be set using the `AGENT_API_KEY` environment variable.

## REST API Endpoints

### API Root

```
GET /api/
```

Returns basic information about the API.

**Response:**
```json
{
  "status": "online",
  "version": "1.0.0",
  "message": "Agent Runtime API is running"
}
```

### Execute Agent Task

```
POST /api/tasks/
```

Executes a task using the agent runtime.

**Request Body:**
```json
{
  "prompt": "Create a React component that displays a list of items",
  "context": {
    "project": "e-commerce-site",
    "language": "typescript"
  },
  "tools": ["code-generator", "documentation-search"]
}
```

**Response:**
```json
{
  "task_id": "task-123456",
  "status": "accepted",
  "message": "Task submitted for execution"
}
```

### List Users

```
GET /api/users/
```

Lists all users (requires authentication).

**Response:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com"
  }
]
```

## ML API Endpoints

### ML API Root

```
GET /ml-api/
```

Returns basic information about the ML API.

**Response:**
```json
{
  "status": "online",
  "version": "1.0.0",
  "message": "ML Infrastructure API is running",
  "ml_client_available": true
}
```

### List Models

```
GET /ml-api/models/
```

Lists all available ML models.

**Response:**
```json
[
  {
    "id": "llama-4-maverick",
    "name": "Llama 4 Maverick",
    "version": "1.0.0",
    "description": "Reasoning model for complex tasks",
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 4096
    },
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

### Get Model Details

```
GET /ml-api/models/{model_id}/
```

Gets details for a specific model.

**Response:**
```json
{
  "id": "llama-4-maverick",
  "name": "Llama 4 Maverick",
  "version": "1.0.0",
  "description": "Reasoning model for complex tasks",
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

### List Fine-Tuning Jobs

```
GET /ml-api/fine-tuning-jobs/
```

Lists all fine-tuning jobs.

**Response:**
```json
[
  {
    "id": "ft-123456",
    "model_id": "llama-4-scout",
    "status": "running",
    "created_at": "2025-04-01T00:00:00Z",
    "updated_at": "2025-04-01T01:00:00Z",
    "fine_tuned_model": null,
    "training_file": "file-123456",
    "validation_file": "file-789012",
    "metrics": {
      "loss": 0.1,
      "accuracy": 0.95
    },
    "error": null
  }
]
```

### Create Fine-Tuning Job

```
POST /ml-api/fine-tuning-jobs/
```

Creates a new fine-tuning job.

**Request Body:**
```json
{
  "model_id": "llama-4-scout",
  "training_file": "file-123456",
  "validation_file": "file-789012",
  "suffix": "swe-agent",
  "compute_config": {
    "instance_type": "g4dn.xlarge",
    "instance_count": 1
  }
}
```

**Response:**
```json
{
  "id": "ft-123456",
  "model_id": "llama-4-scout",
  "status": "created",
  "created_at": "2025-04-15T00:00:00Z",
  "updated_at": "2025-04-15T00:00:00Z",
  "fine_tuned_model": null,
  "training_file": "file-123456",
  "validation_file": "file-789012",
  "metrics": null,
  "error": null
}
```

### Get Fine-Tuning Job Details

```
GET /ml-api/fine-tuning-jobs/{job_id}/
```

Gets details for a specific fine-tuning job.

**Response:**
```json
{
  "id": "ft-123456",
  "model_id": "llama-4-scout",
  "status": "running",
  "created_at": "2025-04-01T00:00:00Z",
  "updated_at": "2025-04-01T01:00:00Z",
  "fine_tuned_model": null,
  "training_file": "file-123456",
  "validation_file": "file-789012",
  "metrics": {
    "loss": 0.1,
    "accuracy": 0.95
  },
  "error": null
}
```

### Cancel Fine-Tuning Job

```
POST /ml-api/fine-tuning-jobs/{job_id}/cancel/
```

Cancels a fine-tuning job.

**Response:**
```json
{
  "status": "success",
  "message": "Job ft-123456 cancelled"
}
```

## Django Ninja API Endpoints

### API Root

```
GET /ninja-api/
```

Returns basic information about the API.

**Response:**
```json
{
  "status": "online",
  "version": "1.0.0",
  "message": "Agent Runtime API is running",
  "pydantic_models_available": true
}
```

### Execute Task

```
POST /ninja-api/tasks/
```

Executes a task using the agent runtime.

**Request Body:**
```json
{
  "prompt": "Create a React component that displays a list of items",
  "context": {
    "project": "e-commerce-site",
    "language": "typescript"
  },
  "tools": ["code-generator", "documentation-search"]
}
```

**Response:**
```json
{
  "task_id": "task-123456",
  "status": "accepted",
  "message": "Task submitted for execution"
}
```

## gRPC API

The gRPC API is available on port 50051 by default. The following services are available:

### AgentService

```protobuf
service AgentService {
  rpc ExecuteTask(ExecuteTaskRequest) returns (ExecuteTaskResponse);
  rpc GetTaskStatus(GetTaskStatusRequest) returns (GetTaskStatusResponse);
}

message ExecuteTaskRequest {
  string prompt = 1;
  map<string, string> context = 2;
  repeated string tools = 3;
}

message ExecuteTaskResponse {
  string task_id = 1;
  string status = 2;
  string message = 3;
}

message GetTaskStatusRequest {
  string task_id = 1;
}

message GetTaskStatusResponse {
  string task_id = 1;
  string status = 2;
  string result = 3;
}
```

### MLService

```protobuf
service MLService {
  rpc ListModels(ListModelsRequest) returns (ListModelsResponse);
  rpc GetModel(GetModelRequest) returns (GetModelResponse);
  rpc CreateFineTuningJob(CreateFineTuningJobRequest) returns (FineTuningJobResponse);
  rpc GetFineTuningJob(GetFineTuningJobRequest) returns (FineTuningJobResponse);
  rpc CancelFineTuningJob(CancelFineTuningJobRequest) returns (CancelFineTuningJobResponse);
}

message ListModelsRequest {}

message ListModelsResponse {
  repeated ModelDetail models = 1;
}

message GetModelRequest {
  string model_id = 1;
}

message GetModelResponse {
  ModelDetail model = 1;
}

message ModelDetail {
  string id = 1;
  string name = 2;
  string version = 3;
  string description = 4;
  map<string, string> parameters = 5;
  string created_at = 6;
  string updated_at = 7;
}

message CreateFineTuningJobRequest {
  string model_id = 1;
  string training_file = 2;
  string validation_file = 3;
  string suffix = 4;
  map<string, string> compute_config = 5;
}

message FineTuningJobResponse {
  string id = 1;
  string model_id = 2;
  string status = 3;
  string created_at = 4;
  string updated_at = 5;
  string fine_tuned_model = 6;
  string training_file = 7;
  string validation_file = 8;
  map<string, float> metrics = 9;
  string error = 10;
}

message GetFineTuningJobRequest {
  string job_id = 1;
}

message CancelFineTuningJobRequest {
  string job_id = 1;
}

message CancelFineTuningJobResponse {
  string status = 1;
  string message = 2;
}
```

## Code Examples

### Python

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Execute a task
response = requests.post(
    f"{API_URL}/api/tasks/",
    headers=headers,
    json={
        "prompt": "Create a React component that displays a list of items",
        "context": {
            "project": "e-commerce-site",
            "language": "typescript"
        },
        "tools": ["code-generator", "documentation-search"]
    }
)
print(response.json())

# List models
response = requests.get(f"{API_URL}/ml-api/models/", headers=headers)
print(response.json())
```

### JavaScript

```javascript
const API_URL = "http://localhost:8000";
const API_KEY = "your-api-key-here";

// Execute a task
fetch(`${API_URL}/api/tasks/`, {
  method: "POST",
  headers: {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    prompt: "Create a React component that displays a list of items",
    context: {
      project: "e-commerce-site",
      language: "typescript"
    },
    tools: ["code-generator", "documentation-search"]
  })
})
.then(response => response.json())
.then(data => console.log(data));

// List models
fetch(`${API_URL}/ml-api/models/`, {
  headers: {
    "X-API-Key": API_KEY
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

### Go

```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
)

const (
	APIURL = "http://localhost:8000"
	APIKey = "your-api-key-here"
)

func main() {
	// Execute a task
	taskPayload := map[string]interface{}{
		"prompt": "Create a React component that displays a list of items",
		"context": map[string]string{
			"project":  "e-commerce-site",
			"language": "typescript",
		},
		"tools": []string{"code-generator", "documentation-search"},
	}
	
	taskJSON, _ := json.Marshal(taskPayload)
	
	req, _ := http.NewRequest("POST", APIURL+"/api/tasks/", bytes.NewBuffer(taskJSON))
	req.Header.Set("X-API-Key", APIKey)
	req.Header.Set("Content-Type", "application/json")
	
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	
	body, _ := ioutil.ReadAll(resp.Body)
	fmt.Println(string(body))
	
	// List models
	req, _ = http.NewRequest("GET", APIURL+"/ml-api/models/", nil)
	req.Header.Set("X-API-Key", APIKey)
	
	resp, err = client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	
	body, _ = ioutil.ReadAll(resp.Body)
	fmt.Println(string(body))
}
```

## Error Handling

The API returns standard HTTP status codes:

- 200: Success
- 400: Bad Request (invalid parameters)
- 401: Unauthorized (invalid or missing API key)
- 404: Not Found (resource not found)
- 500: Internal Server Error

Error responses include a JSON object with details:

```json
{
  "error": "Error message",
  "details": {
    "field": "Error details for specific field"
  }
}
```

## Integration Patterns

### Web Application Integration

For web applications, use the REST API endpoints with API key authentication. The API supports CORS for cross-origin requests.

### Desktop Application Integration

For desktop applications (Electron), use either the REST API or gRPC API depending on performance requirements. The gRPC API provides better performance for high-frequency operations.

### Mobile Application Integration

For mobile applications (Lynx), use the REST API with API key authentication. The API is designed to be lightweight and mobile-friendly.

### Devin Integration

For Devin integration, use the REST API with API key authentication. The API is designed to be easily accessible by Devin for automation tasks.
