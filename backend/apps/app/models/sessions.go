package models

import (
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type Session struct {
	ID                     uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Title                  string     `json:"title" gorm:"size:255;not null"`
	Description            string     `json:"description" gorm:"type:text"`
	Status                 string     `json:"status" gorm:"size:20;not null;default:'active'"`
	Repository             string     `json:"repository" gorm:"size:255"`
	RepositoryURL          string     `json:"repository_url" gorm:"type:varchar(255)"`
	Branch                 string     `json:"branch" gorm:"size:255"`
	UserID                 uuid.UUID  `json:"user_id" gorm:"type:uuid;not null"`
	OrganizationID         *uuid.UUID `json:"organization_id" gorm:"type:uuid"`
	WorkspaceID            *uuid.UUID `json:"workspace_id" gorm:"type:uuid"`
	Model                  string     `json:"model" gorm:"size:50;not null;default:'gemini_2_5_pro'"`
	CreatedAt              time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt              time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
	LastActiveAt           *time.Time `json:"last_active_at"`
	CompletedAt            *time.Time `json:"completed_at"`
	Config                 db.JSONMap `json:"config" gorm:"type:jsonb;default:'{}'"`
	TokenCount             int        `json:"token_count" gorm:"default:0"`
	TokenLimit             int        `json:"token_limit" gorm:"default:1000000"`
	KnowledgeSuggestions   bool       `json:"knowledge_suggestions" gorm:"default:true"`
	DocumentationSuggestions bool     `json:"documentation_suggestions" gorm:"default:true"`
	AutoTaskStart          bool       `json:"auto_task_start" gorm:"default:true"`
}

const (
	SessionStatusActive    = "active"
	SessionStatusInactive  = "inactive"
	SessionStatusSleeping  = "sleeping"
	SessionStatusCompleted = "completed"
	SessionStatusArchived  = "archived"
	SessionStatusError     = "error"
)

const (
	SessionModelGemini       = "gemini_2_5_pro"
	SessionModelLlamaMaverick = "llama_4_maverick"
	SessionModelLlamaScout   = "llama_4_scout"
)

func (Session) TableName() string {
	return "app_session"
}

func (s Session) String() string {
	return s.Title
}

type SessionGroup struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	Description    string     `json:"description" gorm:"type:text"`
	GroupType      string     `json:"group_type" gorm:"size:20;not null;default:'manual'"`
	UserID         uuid.UUID  `json:"user_id" gorm:"type:uuid;not null"`
	OrganizationID *uuid.UUID `json:"organization_id" gorm:"type:uuid"`
	WorkspaceID    *uuid.UUID `json:"workspace_id" gorm:"type:uuid"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	SessionGroupTypeManual  = "manual"
	SessionGroupTypeAuto    = "auto"
	SessionGroupTypeProject = "project"
	SessionGroupTypeFeature = "feature"
)

func (SessionGroup) TableName() string {
	return "app_sessiongroup"
}

func (sg SessionGroup) String() string {
	return sg.Name
}

type SessionRelationship struct {
	ID               uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	RelationshipType string     `json:"relationship_type" gorm:"size:20;not null;default:'reference'"`
	SourceSessionID  uuid.UUID  `json:"source_session_id" gorm:"type:uuid;not null"`
	TargetSessionID  uuid.UUID  `json:"target_session_id" gorm:"type:uuid;not null"`
	Metadata         db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
	CreatedAt        time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt        time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	SessionRelationshipTypeParentChild   = "parent_child"
	SessionRelationshipTypeContinuation  = "continuation"
	SessionRelationshipTypeReference     = "reference"
	SessionRelationshipTypeDependency    = "dependency"
)

func (SessionRelationship) TableName() string {
	return "app_sessionrelationship"
}

func (sr SessionRelationship) String() string {
	return "Session Relationship"
}

type ContextMetrics struct {
	ID                   uuid.UUID `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	SessionID            uuid.UUID `json:"session_id" gorm:"type:uuid;not null"`
	TokenCount           int       `json:"token_count" gorm:"default:0"`
	TokenLimit           int       `json:"token_limit" gorm:"default:1000000"`
	TokenUsagePercentage float64   `json:"token_usage_percentage" gorm:"default:0.0"`
	CPUUsage             float64   `json:"cpu_usage" gorm:"default:0.0"`
	MemoryUsage          float64   `json:"memory_usage" gorm:"default:0.0"`
	ResponseTime         float64   `json:"response_time" gorm:"default:0.0"`
	Timestamp            time.Time `json:"timestamp" gorm:"autoCreateTime"`
}

func (ContextMetrics) TableName() string {
	return "app_contextmetrics"
}

func (cm ContextMetrics) String() string {
	return "Context Metrics"
}

type SessionActivity struct {
	ID           uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	SessionID    uuid.UUID  `json:"session_id" gorm:"type:uuid;not null"`
	UserID       uuid.UUID  `json:"user_id" gorm:"type:uuid;not null"`
	ActivityType string     `json:"activity_type" gorm:"size:20;not null"`
	Description  string     `json:"description" gorm:"type:text;not null"`
	Metadata     db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
	Timestamp    time.Time  `json:"timestamp" gorm:"autoCreateTime"`
}

const (
	SessionActivityTypeCreate       = "create"
	SessionActivityTypeUpdate       = "update"
	SessionActivityTypeMessage      = "message"
	SessionActivityTypeCommand      = "command"
	SessionActivityTypeStatusChange = "status_change"
	SessionActivityTypeView         = "view"
)

func (SessionActivity) TableName() string {
	return "app_sessionactivity"
}

func (sa SessionActivity) String() string {
	return "Session Activity"
}

func init() {
	db.RegisterModel("Session", Session{})
	db.RegisterModel("SessionGroup", SessionGroup{})
	db.RegisterModel("SessionRelationship", SessionRelationship{})
	db.RegisterModel("ContextMetrics", ContextMetrics{})
	db.RegisterModel("SessionActivity", SessionActivity{})
}
