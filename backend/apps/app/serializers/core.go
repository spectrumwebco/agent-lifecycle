package serializers

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type UserSerializer struct {
	core.Serializer
}

func NewUserSerializer() *UserSerializer {
	serializer := &UserSerializer{
		Serializer: core.NewSerializer("User"),
	}

	serializer.SetFields([]string{
		"id", "username", "email", "first_name", "last_name",
		"bio", "avatar", "organization", "date_joined", "is_active",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "date_joined",
	})
	
	serializer.SetWriteOnlyFields([]string{
		"password",
	})

	return serializer
}

type OrganizationSerializer struct {
	core.Serializer
}

func NewOrganizationSerializer() *OrganizationSerializer {
	serializer := &OrganizationSerializer{
		Serializer: core.NewSerializer("Organization"),
	}

	serializer.SetFields([]string{
		"id", "name", "slug", "description", "logo",
		"website", "created_at", "updated_at", "members_count",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at",
	})
	
	serializer.AddMethodField("members_count", "GetMembersCount")

	return serializer
}

func (s *OrganizationSerializer) GetMembersCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "members.count")
}

type WorkspaceSerializer struct {
	core.Serializer
}

func NewWorkspaceSerializer() *WorkspaceSerializer {
	serializer := &WorkspaceSerializer{
		Serializer: core.NewSerializer("Workspace"),
	}

	serializer.SetFields([]string{
		"id", "name", "slug", "description", "organization",
		"organization_name", "created_by", "created_by_username",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at",
		"organization_name", "created_by_username",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("created_by_username", "created_by.username")

	return serializer
}

type ApiKeySerializer struct {
	core.Serializer
}

func NewApiKeySerializer() *ApiKeySerializer {
	serializer := &ApiKeySerializer{
		Serializer: core.NewSerializer("ApiKey"),
	}

	serializer.SetFields([]string{
		"id", "name", "key", "user", "user_username",
		"organization", "organization_name", "scopes",
		"expires_at", "last_used_at", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "key", "created_at", "updated_at",
		"user_username", "organization_name", "last_used_at",
	})
	
	serializer.AddReadOnlyField("user_username", "user.username")
	serializer.AddReadOnlyField("organization_name", "organization.name")
	
	serializer.SetWriteOnlyFields([]string{
		"key",
	})

	return serializer
}

func init() {
	core.RegisterSerializer("UserSerializer", NewUserSerializer())
	core.RegisterSerializer("OrganizationSerializer", NewOrganizationSerializer())
	core.RegisterSerializer("WorkspaceSerializer", NewWorkspaceSerializer())
	core.RegisterSerializer("ApiKeySerializer", NewApiKeySerializer())
}
