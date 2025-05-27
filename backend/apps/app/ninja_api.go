package app

import (
	"os"
	"log"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/api"
)

var (
	logger = log.New(os.Stdout, "[NinjaAPI] ", log.LstdFlags)
	
	PYDANTIC_MODELS_AVAILABLE = false
)

func init() {
	if core.PythonImportExists("models.api.ml_infrastructure_api_models") {
		PYDANTIC_MODELS_AVAILABLE = true
	}
}

type ApiKey struct {
	api.APIKeyHeader
}

func NewApiKey() *ApiKey {
	auth := &ApiKey{
		APIKeyHeader: api.NewAPIKeyHeader("X-API-Key"),
	}
	return auth
}

func (a *ApiKey) Authenticate(request *api.Request, key string) interface{} {
	apiKey := core.GetSetting("API_KEY")
	if key == apiKey {
		return key
	}
	return nil
}

type TaskInput struct {
	Prompt  string                 `json:"prompt"`
	Context map[string]interface{} `json:"context,omitempty"`
	Tools   []string               `json:"tools,omitempty"`
}

type TaskOutput struct {
	TaskID  string `json:"task_id"`
	Status  string `json:"status"`
	Message string `json:"message"`
}

var ninjaAPI = api.NewNinjaAPI(api.NinjaAPIConfig{
	Title:          "Agent Runtime API",
	Version:        "1.0.0",
	Description:    "API for the Agent Runtime system",
	Auth:           NewApiKey(),
	CSRF:           false,
	URLsNamespace:  "agent_runtime_api",
})

func APIRoot(request *api.Request) map[string]interface{} {
	return map[string]interface{}{
		"status":                   "online",
		"version":                  "1.0.0",
		"message":                  "Agent Runtime API is running",
		"pydantic_models_available": PYDANTIC_MODELS_AVAILABLE,
	}
}

func ExecuteTask(request *api.Request, taskInput *TaskInput) *TaskOutput {
	return &TaskOutput{
		TaskID:  "placeholder-task-id",
		Status:  "accepted",
		Message: "Task submitted for execution",
	}
}

type ModelDetail struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Version     string                 `json:"version"`
	Description string                 `json:"description"`
	Parameters  map[string]interface{} `json:"parameters"`
	CreatedAt   string                 `json:"created_at"`
	UpdatedAt   string                 `json:"updated_at"`
}

func ListModels(request *api.Request) []ModelDetail {
	return []ModelDetail{}
}

func GetModel(request *api.Request, modelID string) ModelDetail {
	return ModelDetail{
		ID:          modelID,
		Name:        "Placeholder Model",
		Version:     "1.0.0",
		Description: "Placeholder model for API testing",
		Parameters:  map[string]interface{}{},
		CreatedAt:   "2025-04-15T00:00:00Z",
		UpdatedAt:   "2025-04-15T00:00:00Z",
	}
}

func init() {
	ninjaAPI.Get("/", APIRoot, api.EndpointConfig{Auth: false})
	ninjaAPI.Post("/tasks", ExecuteTask, api.EndpointConfig{Response: "TaskOutput"})
	
	if PYDANTIC_MODELS_AVAILABLE {
		ninjaAPI.Get("/models", ListModels, api.EndpointConfig{Response: "[]ModelDetail"})
		ninjaAPI.Get("/models/{model_id}", GetModel, api.EndpointConfig{Response: "ModelDetail"})
	}
	
	api.RegisterAPI("ninja_api", ninjaAPI)
}
