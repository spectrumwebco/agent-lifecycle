package serializers

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type PlaybookStepSerializer struct {
	core.Serializer
}

func NewPlaybookStepSerializer() *PlaybookStepSerializer {
	serializer := &PlaybookStepSerializer{
		Serializer: core.NewSerializer("PlaybookStep"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "playbook_version", "playbook_version_number",
		"step_type", "content", "order", "is_required", "metadata",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "playbook_version_number",
	})
	
	serializer.AddReadOnlyField("playbook_version_number", "playbook_version.version")

	return serializer
}

type PlaybookVersionSerializer struct {
	core.Serializer
}

func NewPlaybookVersionSerializer() *PlaybookVersionSerializer {
	serializer := &PlaybookVersionSerializer{
		Serializer: core.NewSerializer("PlaybookVersion"),
	}

	serializer.SetFields([]string{
		"id", "playbook", "playbook_name", "version", "description",
		"is_published", "steps", "steps_count", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "playbook_name", "steps_count",
	})
	
	serializer.AddReadOnlyField("playbook_name", "playbook.name")
	serializer.AddNestedSerializer("steps", NewPlaybookStepSerializer(), true)
	serializer.AddMethodField("steps_count", "GetStepsCount")

	return serializer
}

func (s *PlaybookVersionSerializer) GetStepsCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "steps.count")
}

type PlaybookSerializer struct {
	core.Serializer
}

func NewPlaybookSerializer() *PlaybookSerializer {
	serializer := &PlaybookSerializer{
		Serializer: core.NewSerializer("Playbook"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "playbook_type", "organization",
		"organization_name", "created_by", "created_by_username",
		"is_public", "tags", "versions_count", "latest_version",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name",
		"created_by_username", "versions_count", "latest_version",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("created_by_username", "created_by.username")
	serializer.AddMethodField("versions_count", "GetVersionsCount")
	serializer.AddMethodField("latest_version", "GetLatestVersion")

	return serializer
}

func (s *PlaybookSerializer) GetVersionsCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "versions.count")
}

func (s *PlaybookSerializer) GetLatestVersion(obj interface{}) (interface{}, error) {
	latest, err := core.CallObjectMethod(obj, "versions.order_by", "-version")
	if err != nil {
		return nil, err
	}
	
	first, err := core.CallObjectMethod(latest, "first")
	if err != nil {
		return nil, err
	}
	
	if first == nil {
		return nil, nil
	}
	
	serializer := NewPlaybookVersionSerializer()
	return serializer.Serialize(first)
}

type LookbookItemSerializer struct {
	core.Serializer
}

func NewLookbookItemSerializer() *LookbookItemSerializer {
	serializer := &LookbookItemSerializer{
		Serializer: core.NewSerializer("LookbookItem"),
	}

	serializer.SetFields([]string{
		"id", "title", "description", "lookbook", "lookbook_name",
		"item_type", "content", "image", "order", "metadata",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "lookbook_name",
	})
	
	serializer.AddReadOnlyField("lookbook_name", "lookbook.name")

	return serializer
}

type LookbookSerializer struct {
	core.Serializer
}

func NewLookbookSerializer() *LookbookSerializer {
	serializer := &LookbookSerializer{
		Serializer: core.NewSerializer("Lookbook"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "lookbook_type", "organization",
		"organization_name", "created_by", "created_by_username",
		"is_public", "tags", "items", "items_count", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name",
		"created_by_username", "items_count",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("created_by_username", "created_by.username")
	serializer.AddNestedSerializer("items", NewLookbookItemSerializer(), true)
	serializer.AddMethodField("items_count", "GetItemsCount")

	return serializer
}

func (s *LookbookSerializer) GetItemsCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "items.count")
}

func init() {
	core.RegisterSerializer("PlaybookStepSerializer", NewPlaybookStepSerializer())
	core.RegisterSerializer("PlaybookVersionSerializer", NewPlaybookVersionSerializer())
	core.RegisterSerializer("PlaybookSerializer", NewPlaybookSerializer())
	core.RegisterSerializer("LookbookItemSerializer", NewLookbookItemSerializer())
	core.RegisterSerializer("LookbookSerializer", NewLookbookSerializer())
}
