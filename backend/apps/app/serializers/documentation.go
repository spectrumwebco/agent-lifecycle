package serializers

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type DocumentationProjectSerializer struct {
	core.Serializer
}

func NewDocumentationProjectSerializer() *DocumentationProjectSerializer {
	serializer := &DocumentationProjectSerializer{
		Serializer: core.NewSerializer("DocumentationProject"),
	}

	serializer.SetFields([]string{
		"id", "name", "slug", "description", "project_type", "organization",
		"organization_name", "version", "is_published", "metadata",
		"sections_count", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name", "sections_count",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddMethodField("sections_count", "GetSectionsCount")

	return serializer
}

func (s *DocumentationProjectSerializer) GetSectionsCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "sections.count")
}

type DocumentationSectionSerializer struct {
	core.Serializer
}

func NewDocumentationSectionSerializer() *DocumentationSectionSerializer {
	serializer := &DocumentationSectionSerializer{
		Serializer: core.NewSerializer("DocumentationSection"),
	}

	serializer.SetFields([]string{
		"id", "title", "slug", "description", "project", "project_name",
		"order", "icon", "is_published", "pages_count", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "project_name", "pages_count",
	})
	
	serializer.AddReadOnlyField("project_name", "project.name")
	serializer.AddMethodField("pages_count", "GetPagesCount")

	return serializer
}

func (s *DocumentationSectionSerializer) GetPagesCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "pages.count")
}

type DocumentationPageSerializer struct {
	core.Serializer
}

func NewDocumentationPageSerializer() *DocumentationPageSerializer {
	serializer := &DocumentationPageSerializer{
		Serializer: core.NewSerializer("DocumentationPage"),
	}

	serializer.SetFields([]string{
		"id", "title", "slug", "content", "section", "section_title",
		"project_name", "order", "is_published", "metadata", "created_by",
		"created_by_username", "last_updated_by", "last_updated_by_username",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "section_title", "project_name",
		"created_by_username", "last_updated_by_username",
	})
	
	serializer.AddReadOnlyField("section_title", "section.title")
	serializer.AddReadOnlyField("project_name", "section.project.name")
	serializer.AddReadOnlyField("created_by_username", "created_by.username")
	serializer.AddReadOnlyField("last_updated_by_username", "last_updated_by.username")

	return serializer
}

type DocumentationFeedbackSerializer struct {
	core.Serializer
}

func NewDocumentationFeedbackSerializer() *DocumentationFeedbackSerializer {
	serializer := &DocumentationFeedbackSerializer{
		Serializer: core.NewSerializer("DocumentationFeedback"),
	}

	serializer.SetFields([]string{
		"id", "page", "page_title", "user", "user_username", "feedback_type",
		"content", "status", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "page_title", "user_username",
	})
	
	serializer.AddReadOnlyField("page_title", "page.title")
	serializer.AddReadOnlyField("user_username", "user.username")

	return serializer
}

func init() {
	core.RegisterSerializer("DocumentationProjectSerializer", NewDocumentationProjectSerializer())
	core.RegisterSerializer("DocumentationSectionSerializer", NewDocumentationSectionSerializer())
	core.RegisterSerializer("DocumentationPageSerializer", NewDocumentationPageSerializer())
	core.RegisterSerializer("DocumentationFeedbackSerializer", NewDocumentationFeedbackSerializer())
}
