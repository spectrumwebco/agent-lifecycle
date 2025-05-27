package serializers

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type ThemeSerializer struct {
	core.Serializer
}

func NewThemeSerializer() *ThemeSerializer {
	serializer := &ThemeSerializer{
		Serializer: core.NewSerializer("Theme"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "organization", "organization_name",
		"colors", "fonts", "logo", "is_active", "is_default", "created_by",
		"created_by_username", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name", "created_by_username",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("created_by_username", "created_by.username")

	return serializer
}

type UIComponentSerializer struct {
	core.Serializer
}

func NewUIComponentSerializer() *UIComponentSerializer {
	serializer := &UIComponentSerializer{
		Serializer: core.NewSerializer("UIComponent"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "organization", "organization_name",
		"component_type", "configuration", "is_active", "created_by",
		"created_by_username", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name", "created_by_username",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("created_by_username", "created_by.username")

	return serializer
}

type CustomFieldSerializer struct {
	core.Serializer
}

func NewCustomFieldSerializer() *CustomFieldSerializer {
	serializer := &CustomFieldSerializer{
		Serializer: core.NewSerializer("CustomField"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "organization", "organization_name",
		"field_type", "entity_type", "options", "is_required", "default_value",
		"validation_regex", "is_active", "created_by", "created_by_username",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name", "created_by_username",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("created_by_username", "created_by.username")

	return serializer
}

type WorkflowSerializer struct {
	core.Serializer
}

func NewWorkflowSerializer() *WorkflowSerializer {
	serializer := &WorkflowSerializer{
		Serializer: core.NewSerializer("Workflow"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "organization", "organization_name",
		"workflow_type", "entity_type", "states", "transitions", "is_active",
		"created_by", "created_by_username", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name", "created_by_username",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("created_by_username", "created_by.username")

	return serializer
}

func init() {
	core.RegisterSerializer("ThemeSerializer", NewThemeSerializer())
	core.RegisterSerializer("UIComponentSerializer", NewUIComponentSerializer())
	core.RegisterSerializer("CustomFieldSerializer", NewCustomFieldSerializer())
	core.RegisterSerializer("WorkflowSerializer", NewWorkflowSerializer())
}
