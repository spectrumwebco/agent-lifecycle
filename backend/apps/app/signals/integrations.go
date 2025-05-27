package signals

import (
	"encoding/json"
	"log"
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/backend/apps/app/models"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

var logger = log.New(log.Writer(), "kled.signals: ", log.LstdFlags)

func HandleIntegrationCreation(integration *models.Integration, created bool) {
	if created {
		logger.Printf("New integration created: %s (type: %s)", integration.ID, integration.IntegrationType)

		defaultConfig, _ := json.Marshal(map[string]interface{}{"default": true})
		
		config := &models.IntegrationConfig{
			Integration: integration,
			Config:      string(defaultConfig),
		}
		
		err := core.CreateModel("IntegrationConfig", config)
		if err != nil {
			logger.Printf("Error creating integration config: %v", err)
		}

		notifyGoFramework(integration)
	}
}

func HandleIntegrationAuthCreation(auth *models.IntegrationAuth, created bool) {
	if created {
		logger.Printf("New integration auth created for integration %s", auth.Integration.ID)
	} else {
		if tokenRefreshed, ok := core.GetObjectAttribute(auth, "_token_refreshed").(bool); ok && tokenRefreshed {
			logger.Printf("Integration auth token refreshed for integration %s", auth.Integration.ID)

			payload, _ := json.Marshal(map[string]interface{}{
				"integration_id": auth.Integration.ID.String(),
				"auth_id":        auth.ID.String(),
				"refreshed_at":   time.Now().Format(time.RFC3339),
			})

			event := &models.IntegrationEvent{
				Integration: auth.Integration,
				EventType:   "token_refreshed",
				Status:      "success",
				Payload:     string(payload),
			}

			err := core.CreateModel("IntegrationEvent", event)
			if err != nil {
				logger.Printf("Error creating integration event: %v", err)
			}
		}
	}
}

func TrackIntegrationAuthChanges(auth *models.IntegrationAuth) {
	if auth.ID != uuid.Nil {
		var previous models.IntegrationAuth
		err := core.GetModelByID("IntegrationAuth", auth.ID, &previous)
		if err != nil {
			logger.Printf("Error getting previous integration auth: %v", err)
			core.SetObjectAttribute(auth, "_token_refreshed", false)
			return
		}

		if previous.AccessToken != auth.AccessToken {
			core.SetObjectAttribute(auth, "_token_refreshed", true)
		} else {
			core.SetObjectAttribute(auth, "_token_refreshed", false)
		}
	} else {
		core.SetObjectAttribute(auth, "_token_refreshed", false)
	}
}

func HandleIntegrationEventCreation(event *models.IntegrationEvent, created bool) {
	if created {
		logger.Printf("New integration event created: %s (type: %s)", event.ID, event.EventType)

		if event.Status == "failed" {
			logger.Printf("Integration event %s failed: %s", event.ID, event.ErrorMessage)
		}
	}
}

func notifyGoFramework(integration *models.Integration) {
	defer func() {
		if r := recover(); r != nil {
			logger.Printf("Recovered from panic in notifyGoFramework: %v", r)
		}
	}()

	goIntegrationModule, err := core.ImportPythonModule("apps.python_agent.go_integration")
	if err != nil {
		logger.Printf("Failed to import go_integration module: %v", err)
		return
	}

	getGoRuntimeIntegration, err := goIntegrationModule.GetAttr("get_go_runtime_integration")
	if err != nil {
		logger.Printf("Failed to get get_go_runtime_integration function: %v", err)
		return
	}

	goRuntime, err := getGoRuntimeIntegration.Call()
	if err != nil {
		logger.Printf("Failed to call get_go_runtime_integration: %v", err)
		return
	}

	publishEvent, err := goRuntime.GetAttr("publish_event")
	if err != nil {
		logger.Printf("Failed to get publish_event method: %v", err)
		return
	}

	var organizationID interface{} = nil
	if integration.Organization != nil {
		organizationID = integration.Organization.ID
	}

	eventData := map[string]interface{}{
		"integration_id":   integration.ID.String(),
		"integration_type": integration.IntegrationType,
		"organization_id":  organizationID,
	}

	metadata := map[string]interface{}{
		"integration_id": integration.ID.String(),
	}

	_, err = publishEvent.Call(
		"integration_created",
		eventData,
		"django",
		metadata,
	)

	if err != nil {
		logger.Printf("Failed to notify Go framework about new integration: %v", err)
	}
}

func init() {
	core.RegisterSignalHandler("post_save", "Integration", HandleIntegrationCreation)
	core.RegisterSignalHandler("post_save", "IntegrationAuth", HandleIntegrationAuthCreation)
	core.RegisterSignalHandler("pre_save", "IntegrationAuth", TrackIntegrationAuthChanges)
	core.RegisterSignalHandler("post_save", "IntegrationEvent", HandleIntegrationEventCreation)
}
