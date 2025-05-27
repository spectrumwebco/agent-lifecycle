package models

import (
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type WikiSpace struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	Slug           string     `json:"slug" gorm:"uniqueIndex;not null"`
	Description    string     `json:"description" gorm:"type:text"`
	SpaceType      string     `json:"space_type" gorm:"size:20;not null;default:'general'"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	CreatedByID    *uuid.UUID `json:"created_by_id" gorm:"type:uuid"`
	Icon           string     `json:"icon" gorm:"size:50"`
	Color          string     `json:"color" gorm:"size:20"`
	Config         db.JSONMap `json:"config" gorm:"type:jsonb;default:'{}'"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	SpaceTypeProject = "project"
	SpaceTypeTeam    = "team"
	SpaceTypeDomain  = "domain"
	SpaceTypeGeneral = "general"
)

func (WikiSpace) TableName() string {
	return "app_wikispace"
}

func (ws WikiSpace) String() string {
	return ws.Name
}

type WikiSection struct {
	ID          uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name        string     `json:"name" gorm:"size:255;not null"`
	Slug        string     `json:"slug" gorm:"not null"`
	Description string     `json:"description" gorm:"type:text"`
	ParentID    *uuid.UUID `json:"parent_id" gorm:"type:uuid"`
	SpaceID     uuid.UUID  `json:"space_id" gorm:"type:uuid;not null"`
	CreatedByID *uuid.UUID `json:"created_by_id" gorm:"type:uuid"`
	Order       int        `json:"order" gorm:"default:0"`
	CreatedAt   time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

func (WikiSection) TableName() string {
	return "app_wikisection"
}

func (ws WikiSection) String() string {
	return ws.Name
}

type WikiTag struct {
	ID          uuid.UUID `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name        string    `json:"name" gorm:"size:100;not null"`
	Slug        string    `json:"slug" gorm:"not null"`
	Description string    `json:"description" gorm:"type:text"`
	SpaceID     uuid.UUID `json:"space_id" gorm:"type:uuid;not null"`
	Color       string    `json:"color" gorm:"size:20"`
	CreatedAt   time.Time `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time `json:"updated_at" gorm:"autoUpdateTime"`
}

func (WikiTag) TableName() string {
	return "app_wikitag"
}

func (wt WikiTag) String() string {
	return wt.Name
}

type WikiPage struct {
	ID              uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Title           string     `json:"title" gorm:"size:255;not null"`
	Slug            string     `json:"slug" gorm:"not null"`
	Content         string     `json:"content" gorm:"type:text;not null"`
	PageType        string     `json:"page_type" gorm:"size:20;not null;default:'article'"`
	SpaceID         uuid.UUID  `json:"space_id" gorm:"type:uuid;not null"`
	SectionID       *uuid.UUID `json:"section_id" gorm:"type:uuid"`
	ParentID        *uuid.UUID `json:"parent_id" gorm:"type:uuid"`
	CreatedByID     *uuid.UUID `json:"created_by_id" gorm:"type:uuid"`
	UpdatedByID     *uuid.UUID `json:"updated_by_id" gorm:"type:uuid"`
	Order           int        `json:"order" gorm:"default:0"`
	Status          string     `json:"status" gorm:"size:20;not null;default:'draft'"`
	VectorEmbedding []byte     `json:"vector_embedding" gorm:"type:bytea"`
	Metadata        db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
	CreatedAt       time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt       time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
	PublishedAt     *time.Time `json:"published_at"`
}

const (
	PageTypeArticle       = "article"
	PageTypeDocumentation = "documentation"
	PageTypeTutorial      = "tutorial"
	PageTypeReference     = "reference"
	PageTypeGuide         = "guide"
)

const (
	PageStatusDraft       = "draft"
	PageStatusPublished   = "published"
	PageStatusArchived    = "archived"
	PageStatusNeedsReview = "needs_review"
)

func (WikiPage) TableName() string {
	return "app_wikipage"
}

func (wp WikiPage) String() string {
	return wp.Title
}

type WikiPageTag struct {
	WikiPageID uuid.UUID `json:"wiki_page_id" gorm:"primaryKey;type:uuid"`
	WikiTagID  uuid.UUID `json:"wiki_tag_id" gorm:"primaryKey;type:uuid"`
}

func (WikiPageTag) TableName() string {
	return "app_wikipage_tags"
}

type WikiRevision struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	PageID         uuid.UUID  `json:"page_id" gorm:"type:uuid;not null"`
	Title          string     `json:"title" gorm:"size:255;not null"`
	Content        string     `json:"content" gorm:"type:text;not null"`
	CreatedByID    *uuid.UUID `json:"created_by_id" gorm:"type:uuid"`
	RevisionNumber int        `json:"revision_number" gorm:"not null"`
	CommitMessage  string     `json:"commit_message" gorm:"type:text"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
}

func (WikiRevision) TableName() string {
	return "app_wikirevision"
}

func (wr WikiRevision) String() string {
	return "Revision " + string(wr.RevisionNumber)
}

type WikiComment struct {
	ID          uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	PageID      uuid.UUID  `json:"page_id" gorm:"type:uuid;not null"`
	Content     string     `json:"content" gorm:"type:text;not null"`
	CreatedByID uuid.UUID  `json:"created_by_id" gorm:"type:uuid;not null"`
	ParentID    *uuid.UUID `json:"parent_id" gorm:"type:uuid"`
	Status      string     `json:"status" gorm:"size:20;not null;default:'active'"`
	CreatedAt   time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	CommentStatusActive   = "active"
	CommentStatusResolved = "resolved"
	CommentStatusHidden   = "hidden"
)

func (WikiComment) TableName() string {
	return "app_wikicomment"
}

func (wc WikiComment) String() string {
	return "Comment on Wiki Page"
}

func init() {
	db.RegisterModel("WikiSpace", WikiSpace{})
	db.RegisterModel("WikiSection", WikiSection{})
	db.RegisterModel("WikiTag", WikiTag{})
	db.RegisterModel("WikiPage", WikiPage{})
	db.RegisterModel("WikiPageTag", WikiPageTag{})
	db.RegisterModel("WikiRevision", WikiRevision{})
	db.RegisterModel("WikiComment", WikiComment{})
}
