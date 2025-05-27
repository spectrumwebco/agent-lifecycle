package serializers

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type WikiSpaceSerializer struct {
	core.Serializer
}

func NewWikiSpaceSerializer() *WikiSpaceSerializer {
	serializer := &WikiSpaceSerializer{
		Serializer: core.NewSerializer("WikiSpace"),
	}

	serializer.SetFields([]string{
		"id", "name", "slug", "description", "organization", "organization_name",
		"icon", "is_public", "pages_count", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name", "pages_count",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddMethodField("pages_count", "GetPagesCount")

	return serializer
}

func (s *WikiSpaceSerializer) GetPagesCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "pages.count")
}

type WikiPageSerializer struct {
	core.Serializer
}

func NewWikiPageSerializer() *WikiPageSerializer {
	serializer := &WikiPageSerializer{
		Serializer: core.NewSerializer("WikiPage"),
	}

	serializer.SetFields([]string{
		"id", "title", "slug", "content", "space", "space_name",
		"parent", "order", "is_published", "created_by", "created_by_username",
		"last_updated_by", "last_updated_by_username", "revisions_count",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "space_name",
		"created_by_username", "last_updated_by_username", "revisions_count",
	})
	
	serializer.AddReadOnlyField("space_name", "space.name")
	serializer.AddReadOnlyField("created_by_username", "created_by.username")
	serializer.AddReadOnlyField("last_updated_by_username", "last_updated_by.username")
	serializer.AddMethodField("revisions_count", "GetRevisionsCount")

	return serializer
}

func (s *WikiPageSerializer) GetRevisionsCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "revisions.count")
}

type WikiRevisionSerializer struct {
	core.Serializer
}

func NewWikiRevisionSerializer() *WikiRevisionSerializer {
	serializer := &WikiRevisionSerializer{
		Serializer: core.NewSerializer("WikiRevision"),
	}

	serializer.SetFields([]string{
		"id", "page", "page_title", "revision_number", "content",
		"change_summary", "created_by", "created_by_username", "created_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "revision_number", "created_at", "page_title", "created_by_username",
	})
	
	serializer.AddReadOnlyField("page_title", "page.title")
	serializer.AddReadOnlyField("created_by_username", "created_by.username")

	return serializer
}

type WikiCommentSerializer struct {
	core.Serializer
}

func NewWikiCommentSerializer() *WikiCommentSerializer {
	serializer := &WikiCommentSerializer{
		Serializer: core.NewSerializer("WikiComment"),
	}

	serializer.SetFields([]string{
		"id", "page", "page_title", "content", "author", "author_username",
		"parent", "is_resolved", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "page_title", "author_username",
	})
	
	serializer.AddReadOnlyField("page_title", "page.title")
	serializer.AddReadOnlyField("author_username", "author.username")

	return serializer
}

func init() {
	core.RegisterSerializer("WikiSpaceSerializer", NewWikiSpaceSerializer())
	core.RegisterSerializer("WikiPageSerializer", NewWikiPageSerializer())
	core.RegisterSerializer("WikiRevisionSerializer", NewWikiRevisionSerializer())
	core.RegisterSerializer("WikiCommentSerializer", NewWikiCommentSerializer())
}
