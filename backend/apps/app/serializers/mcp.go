package serializers

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type McpServerSerializer struct {
	core.Serializer
}

func NewMcpServerSerializer() *McpServerSerializer {
	serializer := &McpServerSerializer{
		Serializer: core.NewSerializer("McpServer"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "server_type", "host", "port",
		"organization", "organization_name", "workspace", "workspace_name",
		"config", "status", "clients_count", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name",
		"workspace_name", "clients_count",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("workspace_name", "workspace.name")
	serializer.AddMethodField("clients_count", "GetClientsCount")

	return serializer
}

func (s *McpServerSerializer) GetClientsCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "clients.count")
}

type McpClientSerializer struct {
	core.Serializer
}

func NewMcpClientSerializer() *McpClientSerializer {
	serializer := &McpClientSerializer{
		Serializer: core.NewSerializer("McpClient"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "client_type", "agent_type",
		"organization", "organization_name", "config", "status",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")

	return serializer
}

type McpConnectionSerializer struct {
	core.Serializer
}

func NewMcpConnectionSerializer() *McpConnectionSerializer {
	serializer := &McpConnectionSerializer{
		Serializer: core.NewSerializer("McpConnection"),
	}

	serializer.SetFields([]string{
		"id", "server", "server_name", "client", "client_name",
		"connection_type", "status", "last_heartbeat", "metadata",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "server_name",
		"client_name", "last_heartbeat",
	})
	
	serializer.AddReadOnlyField("server_name", "server.name")
	serializer.AddReadOnlyField("client_name", "client.name")

	return serializer
}

type McpCommandSerializer struct {
	core.Serializer
}

func NewMcpCommandSerializer() *McpCommandSerializer {
	serializer := &McpCommandSerializer{
		Serializer: core.NewSerializer("McpCommand"),
	}

	serializer.SetFields([]string{
		"id", "connection", "connection_id", "server_name", "client_name",
		"command_type", "direction", "payload", "status", "response",
		"error_message", "executed_at", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "connection_id",
		"server_name", "client_name", "executed_at",
	})
	
	serializer.AddReadOnlyField("connection_id", "connection.id")
	serializer.AddReadOnlyField("server_name", "connection.server.name")
	serializer.AddReadOnlyField("client_name", "connection.client.name")

	return serializer
}

func init() {
	core.RegisterSerializer("McpServerSerializer", NewMcpServerSerializer())
	core.RegisterSerializer("McpClientSerializer", NewMcpClientSerializer())
	core.RegisterSerializer("McpConnectionSerializer", NewMcpConnectionSerializer())
	core.RegisterSerializer("McpCommandSerializer", NewMcpCommandSerializer())
}
