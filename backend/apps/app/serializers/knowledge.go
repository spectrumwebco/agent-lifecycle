package serializers

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type KnowledgeTagSerializer struct {
	core.Serializer
}

func NewKnowledgeTagSerializer() *KnowledgeTagSerializer {
	serializer := &KnowledgeTagSerializer{
		Serializer: core.NewSerializer("KnowledgeTag"),
	}

	serializer.SetFields([]string{
		"id", "name", "color", "organization", "organization_name", "created_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "organization_name",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")

	return serializer
}

type KnowledgeCategorySerializer struct {
	core.Serializer
}

func NewKnowledgeCategorySerializer() *KnowledgeCategorySerializer {
	serializer := &KnowledgeCategorySerializer{
		Serializer: core.NewSerializer("KnowledgeCategory"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "organization", "organization_name", "created_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "organization_name",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")

	return serializer
}

type KnowledgeBaseSerializer struct {
	core.Serializer
}

func NewKnowledgeBaseSerializer() *KnowledgeBaseSerializer {
	serializer := &KnowledgeBaseSerializer{
		Serializer: core.NewSerializer("KnowledgeBase"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "organization", "organization_name",
		"embedding_model", "vector_store", "config", "items_count",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name", "items_count",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddMethodField("items_count", "GetItemsCount")

	return serializer
}

func (s *KnowledgeBaseSerializer) GetItemsCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "items.count")
}

type KnowledgeItemSerializer struct {
	core.Serializer
}

func NewKnowledgeItemSerializer() *KnowledgeItemSerializer {
	serializer := &KnowledgeItemSerializer{
		Serializer: core.NewSerializer("KnowledgeItem"),
	}

	serializer.SetFields([]string{
		"id", "title", "content", "knowledge_base", "knowledge_base_name",
		"item_type", "source_url", "source_file", "embedding_vector",
		"metadata", "tags", "category", "category_name", "created_by",
		"created_by_username", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "knowledge_base_name",
		"category_name", "created_by_username", "embedding_vector",
	})
	
	serializer.AddReadOnlyField("knowledge_base_name", "knowledge_base.name")
	serializer.AddReadOnlyField("category_name", "category.name")
	serializer.AddReadOnlyField("created_by_username", "created_by.username")
	serializer.AddNestedSerializer("tags", NewKnowledgeTagSerializer(), true)

	return serializer
}

func init() {
	core.RegisterSerializer("KnowledgeTagSerializer", NewKnowledgeTagSerializer())
	core.RegisterSerializer("KnowledgeCategorySerializer", NewKnowledgeCategorySerializer())
	core.RegisterSerializer("KnowledgeBaseSerializer", NewKnowledgeBaseSerializer())
	core.RegisterSerializer("KnowledgeItemSerializer", NewKnowledgeItemSerializer())
}
