package serializers

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type SecretGroupSerializer struct {
	core.Serializer
}

func NewSecretGroupSerializer() *SecretGroupSerializer {
	serializer := &SecretGroupSerializer{
		Serializer: core.NewSerializer("SecretGroup"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "group_type", "organization",
		"organization_name", "metadata", "secrets_count", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name", "secrets_count",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddMethodField("secrets_count", "GetSecretsCount")

	return serializer
}

func (s *SecretGroupSerializer) GetSecretsCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "secrets.count")
}

type SecretSerializer struct {
	core.Serializer
}

func NewSecretSerializer() *SecretSerializer {
	serializer := &SecretSerializer{
		Serializer: core.NewSerializer("Secret"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "secret_type", "value", "group",
		"group_name", "organization", "organization_name", "metadata",
		"expires_at", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name", "group_name",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("group_name", "group.name")
	
	serializer.SetWriteOnlyFields([]string{
		"value",
	})

	return serializer
}

type SecretAccessSerializer struct {
	core.Serializer
}

func NewSecretAccessSerializer() *SecretAccessSerializer {
	serializer := &SecretAccessSerializer{
		Serializer: core.NewSerializer("SecretAccess"),
	}

	serializer.SetFields([]string{
		"id", "user", "user_username", "secret", "secret_name",
		"access_level", "created_at", "expires_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "user_username", "secret_name",
	})
	
	serializer.AddReadOnlyField("user_username", "user.username")
	serializer.AddReadOnlyField("secret_name", "secret.name")

	return serializer
}

type SecretAuditSerializer struct {
	core.Serializer
}

func NewSecretAuditSerializer() *SecretAuditSerializer {
	serializer := &SecretAuditSerializer{
		Serializer: core.NewSerializer("SecretAudit"),
	}

	serializer.SetFields([]string{
		"id", "action", "user", "user_username", "secret", "secret_name",
		"ip_address", "user_agent", "metadata", "timestamp",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "timestamp", "user_username", "secret_name",
	})
	
	serializer.AddReadOnlyField("user_username", "user.username")
	serializer.AddReadOnlyField("secret_name", "secret.name")

	return serializer
}

func init() {
	core.RegisterSerializer("SecretGroupSerializer", NewSecretGroupSerializer())
	core.RegisterSerializer("SecretSerializer", NewSecretSerializer())
	core.RegisterSerializer("SecretAccessSerializer", NewSecretAccessSerializer())
	core.RegisterSerializer("SecretAuditSerializer", NewSecretAuditSerializer())
}
