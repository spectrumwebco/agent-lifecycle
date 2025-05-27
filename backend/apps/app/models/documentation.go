package models

import (
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type DocumentationProject struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	Slug           string     `json:"slug" gorm:"uniqueIndex;not null"`
	Description    string     `json:"description" gorm:"type:text"`
	ProjectType    string     `json:"project_type" gorm:"size:20;not null;default:'user_guide'"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	Version        string     `json:"version" gorm:"size:50;not null;default:'1.0.0'"`
	Status         string     `json:"status" gorm:"size:20;not null;default:'draft'"`
	Config         db.JSONMap `json:"config" gorm:"type:jsonb;default:'{}'"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
	PublishedAt    *time.Time `json:"published_at"`
}

const (
	DocProjectTypeAPI        = "api"
	DocProjectTypeUserGuide  = "user_guide"
	DocProjectTypeDeveloper  = "developer"
	DocProjectTypeAdmin      = "admin"
	DocProjectTypeReference  = "reference"
)

const (
	DocProjectStatusDraft     = "draft"
	DocProjectStatusPublished = "published"
	DocProjectStatusArchived  = "archived"
)

func (DocumentationProject) TableName() string {
	return "app_documentationproject"
}

func (dp DocumentationProject) String() string {
	return dp.Name + " v" + dp.Version
}

type DocumentationSection struct {
	ID          uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Title       string     `json:"title" gorm:"size:255;not null"`
	Slug        string     `json:"slug" gorm:"not null"`
	Description string     `json:"description" gorm:"type:text"`
	ProjectID   uuid.UUID  `json:"project_id" gorm:"type:uuid;not null"`
	ParentID    *uuid.UUID `json:"parent_id" gorm:"type:uuid"`
	Order       int        `json:"order" gorm:"default:0"`
	CreatedAt   time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

func (DocumentationSection) TableName() string {
	return "app_documentationsection"
}

func (ds DocumentationSection) String() string {
	return ds.Title
}

type DocumentationPage struct {
	ID          uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Title       string     `json:"title" gorm:"size:255;not null"`
	Slug        string     `json:"slug" gorm:"not null"`
	Content     string     `json:"content" gorm:"type:text;not null"`
	ProjectID   uuid.UUID  `json:"project_id" gorm:"type:uuid;not null"`
	SectionID   *uuid.UUID `json:"section_id" gorm:"type:uuid"`
	Order       int        `json:"order" gorm:"default:0"`
	CreatedByID *uuid.UUID `json:"created_by_id" gorm:"type:uuid"`
	UpdatedByID *uuid.UUID `json:"updated_by_id" gorm:"type:uuid"`
	Status      string     `json:"status" gorm:"size:20;not null;default:'draft'"`
	Metadata    db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
	CreatedAt   time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
	PublishedAt *time.Time `json:"published_at"`
}

const (
	DocPageStatusDraft       = "draft"
	DocPageStatusPublished   = "published"
	DocPageStatusArchived    = "archived"
	DocPageStatusNeedsReview = "needs_review"
)

func (DocumentationPage) TableName() string {
	return "app_documentationpage"
}

func (dp DocumentationPage) String() string {
	return dp.Title
}

type DocumentationFeedback struct {
	ID           uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	PageID       uuid.UUID  `json:"page_id" gorm:"type:uuid;not null"`
	FeedbackType string     `json:"feedback_type" gorm:"size:20;not null"`
	Content      string     `json:"content" gorm:"type:text"`
	UserID       *uuid.UUID `json:"user_id" gorm:"type:uuid"`
	Status       string     `json:"status" gorm:"size:20;not null;default:'new'"`
	CreatedAt    time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt    time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	DocFeedbackTypeHelpful    = "helpful"
	DocFeedbackTypeNotHelpful = "not_helpful"
	DocFeedbackTypeSuggestion = "suggestion"
	DocFeedbackTypeError      = "error"
	DocFeedbackTypeQuestion   = "question"
)

const (
	DocFeedbackStatusNew      = "new"
	DocFeedbackStatusReviewed = "reviewed"
	DocFeedbackStatusResolved = "resolved"
	DocFeedbackStatusIgnored  = "ignored"
)

func (DocumentationFeedback) TableName() string {
	return "app_documentationfeedback"
}

func (df DocumentationFeedback) String() string {
	return "Documentation Feedback"
}

func init() {
	db.RegisterModel("DocumentationProject", DocumentationProject{})
	db.RegisterModel("DocumentationSection", DocumentationSection{})
	db.RegisterModel("DocumentationPage", DocumentationPage{})
	db.RegisterModel("DocumentationFeedback", DocumentationFeedback{})
}
