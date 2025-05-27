package models

import (
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type IssueLabel struct {
	ID             uuid.UUID `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string    `json:"name" gorm:"size:100;not null"`
	Description    string    `json:"description" gorm:"type:text"`
	Color          string    `json:"color" gorm:"size:20;not null"`
	OrganizationID uuid.UUID `json:"organization_id" gorm:"type:uuid;not null"`
	CreatedAt      time.Time `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time `json:"updated_at" gorm:"autoUpdateTime"`
}

func (IssueLabel) TableName() string {
	return "app_issuelabel"
}

func (il IssueLabel) String() string {
	return il.Name
}

type Issue struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Title          string     `json:"title" gorm:"size:255;not null"`
	Description    string     `json:"description" gorm:"type:text"`
	IssueType      string     `json:"issue_type" gorm:"size:20;not null;default:'task'"`
	Priority       string     `json:"priority" gorm:"size:20;not null;default:'medium'"`
	Status         string     `json:"status" gorm:"size:20;not null;default:'open'"`
	ReporterID     uuid.UUID  `json:"reporter_id" gorm:"type:uuid;not null"`
	AssigneeID     *uuid.UUID `json:"assignee_id" gorm:"type:uuid"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	WorkspaceID    *uuid.UUID `json:"workspace_id" gorm:"type:uuid"`
	ExternalID     string     `json:"external_id" gorm:"size:100"`
	ExternalURL    string     `json:"external_url"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
	ClosedAt       *time.Time `json:"closed_at"`
	DueDate        *time.Time `json:"due_date"`
	Metadata       db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
}

const (
	IssueTypeBug         = "bug"
	IssueTypeFeature     = "feature"
	IssueTypeTask        = "task"
	IssueTypeImprovement = "improvement"
	IssueTypeQuestion    = "question"
)

const (
	IssuePriorityLow      = "low"
	IssuePriorityMedium   = "medium"
	IssuePriorityHigh     = "high"
	IssuePriorityCritical = "critical"
)

const (
	IssueStatusOpen       = "open"
	IssueStatusInProgress = "in_progress"
	IssueStatusReview     = "review"
	IssueStatusDone       = "done"
	IssueStatusClosed     = "closed"
)

func (Issue) TableName() string {
	return "app_issue"
}

func (i Issue) String() string {
	return i.Title
}

type IssueIssueLabel struct {
	IssueID      uuid.UUID `json:"issue_id" gorm:"primaryKey;type:uuid"`
	IssueLabelID uuid.UUID `json:"issue_label_id" gorm:"primaryKey;type:uuid"`
}

func (IssueIssueLabel) TableName() string {
	return "app_issue_labels"
}

type IssueComment struct {
	ID        uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	IssueID   uuid.UUID  `json:"issue_id" gorm:"type:uuid;not null"`
	Content   string     `json:"content" gorm:"type:text;not null"`
	AuthorID  uuid.UUID  `json:"author_id" gorm:"type:uuid;not null"`
	ParentID  *uuid.UUID `json:"parent_id" gorm:"type:uuid"`
	CreatedAt time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
	Metadata  db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
}

func (IssueComment) TableName() string {
	return "app_issuecomment"
}

func (ic IssueComment) String() string {
	return "Comment on Issue"
}

type IssueAttachment struct {
	ID         uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	IssueID    uuid.UUID  `json:"issue_id" gorm:"type:uuid;not null"`
	Filename   string     `json:"filename" gorm:"size:255;not null"`
	FileURL    string     `json:"file_url" gorm:"not null"`
	FileSize   int        `json:"file_size" gorm:"not null"`
	FileType   string     `json:"file_type" gorm:"size:100;not null"`
	UploadedByID uuid.UUID  `json:"uploaded_by_id" gorm:"type:uuid;not null"`
	CreatedAt  time.Time  `json:"created_at" gorm:"autoCreateTime"`
	Metadata   db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
}

func (IssueAttachment) TableName() string {
	return "app_issueattachment"
}

func (ia IssueAttachment) String() string {
	return ia.Filename
}

type IssueRelationship struct {
	ID               uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	RelationshipType string     `json:"relationship_type" gorm:"size:20;not null"`
	SourceIssueID    uuid.UUID  `json:"source_issue_id" gorm:"type:uuid;not null"`
	TargetIssueID    uuid.UUID  `json:"target_issue_id" gorm:"type:uuid;not null"`
	CreatedByID      *uuid.UUID `json:"created_by_id" gorm:"type:uuid"`
	CreatedAt        time.Time  `json:"created_at" gorm:"autoCreateTime"`
}

const (
	RelationshipTypeBlocks      = "blocks"
	RelationshipTypeBlockedBy   = "blocked_by"
	RelationshipTypeRelatesTo   = "relates_to"
	RelationshipTypeDuplicates  = "duplicates"
	RelationshipTypeDuplicatedBy = "duplicated_by"
	RelationshipTypeParentOf    = "parent_of"
	RelationshipTypeChildOf     = "child_of"
)

func (IssueRelationship) TableName() string {
	return "app_issuerelationship"
}

func (ir IssueRelationship) String() string {
	return ir.RelationshipType
}

func init() {
	db.RegisterModel("IssueLabel", IssueLabel{})
	db.RegisterModel("Issue", Issue{})
	db.RegisterModel("IssueIssueLabel", IssueIssueLabel{})
	db.RegisterModel("IssueComment", IssueComment{})
	db.RegisterModel("IssueAttachment", IssueAttachment{})
	db.RegisterModel("IssueRelationship", IssueRelationship{})
}
