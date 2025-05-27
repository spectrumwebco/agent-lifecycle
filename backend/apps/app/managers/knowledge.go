package managers

import (
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type KnowledgeBaseManager struct {
	db.Manager
}

func NewKnowledgeBaseManager() *KnowledgeBaseManager {
	return &KnowledgeBaseManager{
		Manager: db.NewManager("KnowledgeBase"),
	}
}

func (m *KnowledgeBaseManager) Active() *db.QuerySet {
	return m.Filter(db.Q{
		"is_active": true,
	})
}

func (m *KnowledgeBaseManager) WithItemCount() *db.QuerySet {
	return m.Annotate(db.Annotation{
		"item_count": db.Count("items"),
	})
}

func (m *KnowledgeBaseManager) ByOrganization(organization interface{}) *db.QuerySet {
	return m.Filter(db.Q{
		"organization": organization,
	})
}

func (m *KnowledgeBaseManager) ByEmbeddingModel(embeddingModel string) *db.QuerySet {
	return m.Filter(db.Q{
		"embedding_model": embeddingModel,
	})
}

func (m *KnowledgeBaseManager) ByVectorStore(vectorStore string) *db.QuerySet {
	return m.Filter(db.Q{
		"vector_store": vectorStore,
	})
}

func (m *KnowledgeBaseManager) WithStats() *db.QuerySet {
	return m.WithItemCount()
}

type KnowledgeItemManager struct {
	db.Manager
}

func NewKnowledgeItemManager() *KnowledgeItemManager {
	return &KnowledgeItemManager{
		Manager: db.NewManager("KnowledgeItem"),
	}
}

func (m *KnowledgeItemManager) ByKnowledgeBase(knowledgeBase interface{}) *db.QuerySet {
	return m.Filter(db.Q{
		"knowledge_base": knowledgeBase,
	})
}

func (m *KnowledgeItemManager) ByItemType(itemType string) *db.QuerySet {
	return m.Filter(db.Q{
		"item_type": itemType,
	})
}

func (m *KnowledgeItemManager) ByCategory(category interface{}) *db.QuerySet {
	return m.Filter(db.Q{
		"category": category,
	})
}

func (m *KnowledgeItemManager) ByTag(tagName string) *db.QuerySet {
	return m.Filter(db.Q{
		"tags__name": tagName,
	})
}

func (m *KnowledgeItemManager) Recent(days int) *db.QuerySet {
	if days == 0 {
		days = 30
	}
	
	recentDate := time.Now().AddDate(0, 0, -days)
	
	return m.Filter(db.Q{
		"$or": []db.Q{
			{"created_at__gte": recentDate},
			{"updated_at__gte": recentDate},
		},
	})
}

func (m *KnowledgeItemManager) Search(query string) *db.QuerySet {
	return m.Filter(db.Q{
		"$or": []db.Q{
			{"title__icontains": query},
			{"content__icontains": query},
		},
	})
}

func (m *KnowledgeItemManager) WithTagCount() *db.QuerySet {
	return m.Annotate(db.Annotation{
		"tag_count": db.Count("tags"),
	})
}

type KnowledgeTagManager struct {
	db.Manager
}

func NewKnowledgeTagManager() *KnowledgeTagManager {
	return &KnowledgeTagManager{
		Manager: db.NewManager("KnowledgeTag"),
	}
}

func (m *KnowledgeTagManager) WithItemCount() *db.QuerySet {
	return m.Annotate(db.Annotation{
		"item_count": db.Count("items"),
	})
}

func (m *KnowledgeTagManager) Popular(limit int) *db.QuerySet {
	if limit == 0 {
		limit = 10
	}
	
	return m.WithItemCount().OrderBy("-item_count").Limit(limit)
}

func (m *KnowledgeTagManager) ByOrganization(organization interface{}) *db.QuerySet {
	return m.Filter(db.Q{
		"organization": organization,
	})
}

type KnowledgeCategoryManager struct {
	db.Manager
}

func NewKnowledgeCategoryManager() *KnowledgeCategoryManager {
	return &KnowledgeCategoryManager{
		Manager: db.NewManager("KnowledgeCategory"),
	}
}

func (m *KnowledgeCategoryManager) WithItemCount() *db.QuerySet {
	return m.Annotate(db.Annotation{
		"item_count": db.Count("items"),
	})
}

func (m *KnowledgeCategoryManager) Popular(limit int) *db.QuerySet {
	if limit == 0 {
		limit = 10
	}
	
	return m.WithItemCount().OrderBy("-item_count").Limit(limit)
}

func (m *KnowledgeCategoryManager) ByOrganization(organization interface{}) *db.QuerySet {
	return m.Filter(db.Q{
		"organization": organization,
	})
}

func init() {
	core.RegisterManager("KnowledgeBaseManager", NewKnowledgeBaseManager())
	core.RegisterManager("KnowledgeItemManager", NewKnowledgeItemManager())
	core.RegisterManager("KnowledgeTagManager", NewKnowledgeTagManager())
	core.RegisterManager("KnowledgeCategoryManager", NewKnowledgeCategoryManager())
}
