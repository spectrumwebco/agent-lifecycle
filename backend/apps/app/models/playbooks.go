package models

import (
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type Playbook struct {
	ID           uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name         string     `json:"name" gorm:"size:255;not null"`
	Description  string     `json:"description" gorm:"type:text"`
	PlaybookType string     `json:"playbook_type" gorm:"size:20;not null;default:'standard'"`
	CreatedByID  uuid.UUID  `json:"created_by_id" gorm:"type:uuid;not null"`
	OrganizationID *uuid.UUID `json:"organization_id" gorm:"type:uuid"`
	WorkspaceID  *uuid.UUID `json:"workspace_id" gorm:"type:uuid"`
	IsActive     bool       `json:"is_active" gorm:"default:true"`
	IsPublic     bool       `json:"is_public" gorm:"default:false"`
	CreatedAt    time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt    time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	PlaybookTypeStandard = "standard"
	PlaybookTypeTemplate = "template"
	PlaybookTypeSystem   = "system"
	PlaybookTypeCustom   = "custom"
)

func (Playbook) TableName() string {
	return "app_playbook"
}

func (p Playbook) String() string {
	return p.Name
}

type PlaybookVersion struct {
	ID          uuid.UUID `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	PlaybookID  uuid.UUID `json:"playbook_id" gorm:"type:uuid;not null"`
	Version     string    `json:"version" gorm:"size:50;not null"`
	Description string    `json:"description" gorm:"type:text"`
	Content     string    `json:"content" gorm:"type:text;not null"`
	CreatedByID uuid.UUID `json:"created_by_id" gorm:"type:uuid;not null"`
	IsActive    bool      `json:"is_active" gorm:"default:true"`
	IsLatest    bool      `json:"is_latest" gorm:"default:true"`
	CreatedAt   time.Time `json:"created_at" gorm:"autoCreateTime"`
}

func (PlaybookVersion) TableName() string {
	return "app_playbookversion"
}

func (pv PlaybookVersion) String() string {
	return "Playbook Version " + pv.Version
}

type PlaybookStep struct {
	ID               uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	PlaybookVersionID uuid.UUID  `json:"playbook_version_id" gorm:"type:uuid;not null"`
	Name             string     `json:"name" gorm:"size:255;not null"`
	Description      string     `json:"description" gorm:"type:text"`
	Order            int        `json:"order" gorm:"not null"`
	StepType         string     `json:"step_type" gorm:"size:20;not null;default:'command'"`
	Content          string     `json:"content" gorm:"type:text;not null"`
	Config           db.JSONMap `json:"config" gorm:"type:jsonb;default:'{}'"`
	CreatedAt        time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt        time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	StepTypeCommand    = "command"
	StepTypeScript     = "script"
	StepTypeCondition  = "condition"
	StepTypeLoop       = "loop"
	StepTypePrompt     = "prompt"
	StepTypeWait       = "wait"
)

func (PlaybookStep) TableName() string {
	return "app_playbookstep"
}

func (ps PlaybookStep) String() string {
	return "Playbook Step " + ps.Name
}

type Lookbook struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	Description    string     `json:"description" gorm:"type:text"`
	LookbookType   string     `json:"lookbook_type" gorm:"size:20;not null;default:'general'"`
	CreatedByID    uuid.UUID  `json:"created_by_id" gorm:"type:uuid;not null"`
	OrganizationID *uuid.UUID `json:"organization_id" gorm:"type:uuid"`
	WorkspaceID    *uuid.UUID `json:"workspace_id" gorm:"type:uuid"`
	IsActive       bool       `json:"is_active" gorm:"default:true"`
	IsPublic       bool       `json:"is_public" gorm:"default:false"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	LookbookTypeGeneral  = "general"
	LookbookTypeCode     = "code"
	LookbookTypeDesign   = "design"
	LookbookTypeWorkflow = "workflow"
)

func (Lookbook) TableName() string {
	return "app_lookbook"
}

func (l Lookbook) String() string {
	return l.Name
}

type LookbookItem struct {
	ID          uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	LookbookID  uuid.UUID  `json:"lookbook_id" gorm:"type:uuid;not null"`
	Title       string     `json:"title" gorm:"size:255;not null"`
	Description string     `json:"description" gorm:"type:text"`
	Content     string     `json:"content" gorm:"type:text;not null"`
	Order       int        `json:"order" gorm:"default:0"`
	ItemType    string     `json:"item_type" gorm:"size:20;not null;default:'text'"`
	CreatedByID uuid.UUID  `json:"created_by_id" gorm:"type:uuid;not null"`
	Metadata    db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
	CreatedAt   time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	ItemTypeText  = "text"
	ItemTypeCode  = "code"
	ItemTypeImage = "image"
	ItemTypeLink  = "link"
	ItemTypeEmbed = "embed"
)

func (LookbookItem) TableName() string {
	return "app_lookbookitem"
}

func (li LookbookItem) String() string {
	return "Lookbook Item " + li.Title
}

func init() {
	db.RegisterModel("Playbook", Playbook{})
	db.RegisterModel("PlaybookVersion", PlaybookVersion{})
	db.RegisterModel("PlaybookStep", PlaybookStep{})
	db.RegisterModel("Lookbook", Lookbook{})
	db.RegisterModel("LookbookItem", LookbookItem{})
}
