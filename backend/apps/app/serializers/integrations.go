package serializers

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type IntegrationAuthSerializer struct {
	core.Serializer
}

func NewIntegrationAuthSerializer() *IntegrationAuthSerializer {
	serializer := &IntegrationAuthSerializer{
		Serializer: core.NewSerializer("IntegrationAuth"),
	}

	serializer.SetFields([]string{
		"id", "integration", "integration_name", "auth_type",
		"credentials", "expires_at", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "integration_name",
	})
	
	serializer.AddReadOnlyField("integration_name", "integration.name")
	
	serializer.SetWriteOnlyFields([]string{
		"credentials",
	})

	return serializer
}

type IntegrationConfigSerializer struct {
	core.Serializer
}

func NewIntegrationConfigSerializer() *IntegrationConfigSerializer {
	serializer := &IntegrationConfigSerializer{
		Serializer: core.NewSerializer("IntegrationConfig"),
	}

	serializer.SetFields([]string{
		"id", "integration", "integration_name", "config",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "integration_name",
	})
	
	serializer.AddReadOnlyField("integration_name", "integration.name")

	return serializer
}

type IntegrationEventSerializer struct {
	core.Serializer
}

func NewIntegrationEventSerializer() *IntegrationEventSerializer {
	serializer := &IntegrationEventSerializer{
		Serializer: core.NewSerializer("IntegrationEvent"),
	}

	serializer.SetFields([]string{
		"id", "integration", "integration_name", "event_type",
		"payload", "status", "error_message", "timestamp",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "timestamp", "integration_name",
	})
	
	serializer.AddReadOnlyField("integration_name", "integration.name")

	return serializer
}

type IntegrationSerializer struct {
	core.Serializer
}

func NewIntegrationSerializer() *IntegrationSerializer {
	serializer := &IntegrationSerializer{
		Serializer: core.NewSerializer("Integration"),
	}

	serializer.SetFields([]string{
		"id", "name", "integration_type", "description", "organization",
		"organization_name", "webhook_url", "api_url", "icon", "is_active",
		"auth", "config", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddNestedSerializer("auth", NewIntegrationAuthSerializer(), true)
	serializer.AddNestedSerializer("config", NewIntegrationConfigSerializer(), true)

	return serializer
}

func init() {
	core.RegisterSerializer("IntegrationAuthSerializer", NewIntegrationAuthSerializer())
	core.RegisterSerializer("IntegrationConfigSerializer", NewIntegrationConfigSerializer())
	core.RegisterSerializer("IntegrationEventSerializer", NewIntegrationEventSerializer())
	core.RegisterSerializer("IntegrationSerializer", NewIntegrationSerializer())
}
