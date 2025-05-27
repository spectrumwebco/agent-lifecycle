package models

import (
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type KnowledgeBase struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	Description    string     `json:"description" gorm:"type:text"`
	BaseType       string     `json:"base_type" gorm:"size:20;not null;default:'general'"`
	UserID         uuid.UUID  `json:"user_id" gorm:"type:uuid;not null"`
	OrganizationID *uuid.UUID `json:"organization_id" gorm:"type:uuid"`
	WorkspaceID    *uuid.UUID `json:"workspace_id" gorm:"type:uuid"`
	Config         db.JSONMap `json:"config" gorm:"type:jsonb;default:'{}'"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	KnowledgeBaseTypeGeneral  = "general"
	KnowledgeBaseTypeProject  = "project"
	KnowledgeBaseTypeDomain   = "domain"
	KnowledgeBaseTypePersonal = "personal"
)

func (KnowledgeBase) TableName() string {
	return "app_knowledgebase"
}

func (kb KnowledgeBase) String() string {
	return kb.Name
}

type KnowledgeCategory struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	Description    string     `json:"description" gorm:"type:text"`
	ParentID       *uuid.UUID `json:"parent_id" gorm:"type:uuid"`
	KnowledgeBaseID uuid.UUID  `json:"knowledge_base_id" gorm:"type:uuid;not null"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

func (KnowledgeCategory) TableName() string {
	return "app_knowledgecategory"
}

func (kc KnowledgeCategory) String() string {
	return kc.Name
}

type KnowledgeTag struct {
	ID             uuid.UUID `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string    `json:"name" gorm:"size:100;not null"`
	Description    string    `json:"description" gorm:"type:text"`
	KnowledgeBaseID uuid.UUID `json:"knowledge_base_id" gorm:"type:uuid;not null"`
	CreatedAt      time.Time `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time `json:"updated_at" gorm:"autoUpdateTime"`
}

func (KnowledgeTag) TableName() string {
	return "app_knowledgetag"
}

func (kt KnowledgeTag) String() string {
	return kt.Name
}

type KnowledgeEntry struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Title          string     `json:"title" gorm:"size:255;not null"`
	Content        string     `json:"content" gorm:"type:text;not null"`
	EntryType      string     `json:"entry_type" gorm:"size:20;not null;default:'article'"`
	KnowledgeBaseID uuid.UUID  `json:"knowledge_base_id" gorm:"type:uuid;not null"`
	CategoryID     *uuid.UUID `json:"category_id" gorm:"type:uuid"`
	CreatedByID    uuid.UUID  `json:"created_by_id" gorm:"type:uuid;not null"`
	VectorEmbedding []byte     `json:"vector_embedding" gorm:"type:bytea"`
	Metadata       db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
	Status         string     `json:"status" gorm:"size:20;not null;default:'draft'"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
	PublishedAt    *time.Time `json:"published_at"`
}

const (
	EntryTypeArticle      = "article"
	EntryTypeSnippet      = "snippet"
	EntryTypeReference    = "reference"
	EntryTypeTutorial     = "tutorial"
	EntryTypeBestPractice = "best_practice"
)

const (
	EntryStatusDraft     = "draft"
	EntryStatusPublished = "published"
	EntryStatusArchived  = "archived"
)

func (KnowledgeEntry) TableName() string {
	return "app_knowledgeentry"
}

func (ke KnowledgeEntry) String() string {
	return ke.Title
}

type KnowledgeEntryTag struct {
	KnowledgeEntryID uuid.UUID `json:"knowledge_entry_id" gorm:"primaryKey;type:uuid"`
	KnowledgeTagID   uuid.UUID `json:"knowledge_tag_id" gorm:"primaryKey;type:uuid"`
}

func (KnowledgeEntryTag) TableName() string {
	return "app_knowledgeentry_tags"
}

type ExternalKnowledge struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Title          string     `json:"title" gorm:"size:255;not null"`
	URL            string     `json:"url" gorm:"not null"`
	Description    string     `json:"description" gorm:"type:text"`
	SourceType     string     `json:"source_type" gorm:"size:20;not null;default:'website'"`
	KnowledgeBaseID uuid.UUID  `json:"knowledge_base_id" gorm:"type:uuid;not null"`
	AddedByID      uuid.UUID  `json:"added_by_id" gorm:"type:uuid;not null"`
	Metadata       db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
	LastAccessedAt *time.Time `json:"last_accessed_at"`
}

const (
	SourceTypeWebsite       = "website"
	SourceTypeDocumentation = "documentation"
	SourceTypeRepository    = "repository"
	SourceTypeArticle       = "article"
	SourceTypePaper         = "paper"
)

func (ExternalKnowledge) TableName() string {
	return "app_externalknowledge"
}

func (ek ExternalKnowledge) String() string {
	return ek.Title
}

type ExternalKnowledgeTag struct {
	ExternalKnowledgeID uuid.UUID `json:"external_knowledge_id" gorm:"primaryKey;type:uuid"`
	KnowledgeTagID      uuid.UUID `json:"knowledge_tag_id" gorm:"primaryKey;type:uuid"`
}

func (ExternalKnowledgeTag) TableName() string {
	return "app_externalknowledge_tags"
}

func init() {
	db.RegisterModel("KnowledgeBase", KnowledgeBase{})
	db.RegisterModel("KnowledgeCategory", KnowledgeCategory{})
	db.RegisterModel("KnowledgeTag", KnowledgeTag{})
	db.RegisterModel("KnowledgeEntry", KnowledgeEntry{})
	db.RegisterModel("KnowledgeEntryTag", KnowledgeEntryTag{})
	db.RegisterModel("ExternalKnowledge", ExternalKnowledge{})
	db.RegisterModel("ExternalKnowledgeTag", ExternalKnowledgeTag{})
}
