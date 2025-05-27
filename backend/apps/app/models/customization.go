package models

import (
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type Theme struct {
	ID              uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name            string     `json:"name" gorm:"size:255;not null"`
	Description     string     `json:"description" gorm:"type:text"`
	ThemeType       string     `json:"theme_type" gorm:"size:20;not null;default:'light'"`
	PrimaryColor    string     `json:"primary_color" gorm:"size:20;not null;default:'#3498db'"`
	SecondaryColor  string     `json:"secondary_color" gorm:"size:20;not null;default:'#2ecc71'"`
	BackgroundColor string     `json:"background_color" gorm:"size:20;not null;default:'#ffffff'"`
	TextColor       string     `json:"text_color" gorm:"size:20;not null;default:'#333333'"`
	AccentColor     string     `json:"accent_color" gorm:"size:20;not null;default:'#e74c3c'"`
	FontFamily      string     `json:"font_family" gorm:"size:100;not null;default:'Inter, sans-serif'"`
	FontSizeBase    string     `json:"font_size_base" gorm:"size:20;not null;default:'16px'"`
	UserID          *uuid.UUID `json:"user_id" gorm:"type:uuid"`
	OrganizationID  *uuid.UUID `json:"organization_id" gorm:"type:uuid"`
	IsSystem        bool       `json:"is_system" gorm:"default:false"`
	IsDefault       bool       `json:"is_default" gorm:"default:false"`
	CustomCSS       string     `json:"custom_css" gorm:"type:text"`
	CreatedAt       time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt       time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	ThemeTypeLight  = "light"
	ThemeTypeDark   = "dark"
	ThemeTypeCustom = "custom"
)

func (Theme) TableName() string {
	return "app_theme"
}

func (t Theme) String() string {
	return t.Name
}

type CustomField struct {
	ID              uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name            string     `json:"name" gorm:"size:255;not null"`
	Description     string     `json:"description" gorm:"type:text"`
	FieldType       string     `json:"field_type" gorm:"size:20;not null;default:'text'"`
	EntityType      string     `json:"entity_type" gorm:"size:20;not null"`
	IsRequired      bool       `json:"is_required" gorm:"default:false"`
	IsSearchable    bool       `json:"is_searchable" gorm:"default:true"`
	DefaultValue    string     `json:"default_value" gorm:"type:text"`
	Options         db.JSONMap `json:"options" gorm:"type:jsonb;default:'[]'"`
	ValidationRegex string     `json:"validation_regex" gorm:"size:255"`
	MinValue        *float64   `json:"min_value"`
	MaxValue        *float64   `json:"max_value"`
	OrganizationID  uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	CreatedAt       time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt       time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	CustomFieldTypeText        = "text"
	CustomFieldTypeNumber      = "number"
	CustomFieldTypeDate        = "date"
	CustomFieldTypeBoolean     = "boolean"
	CustomFieldTypeSelect      = "select"
	CustomFieldTypeMultiselect = "multiselect"
	CustomFieldTypeURL         = "url"
	CustomFieldTypeEmail       = "email"
)

const (
	CustomFieldEntitySession      = "session"
	CustomFieldEntityIssue        = "issue"
	CustomFieldEntityKnowledge    = "knowledge"
	CustomFieldEntityWiki         = "wiki"
	CustomFieldEntityUser         = "user"
	CustomFieldEntityOrganization = "organization"
)

func (CustomField) TableName() string {
	return "app_customfield"
}

func (cf CustomField) String() string {
	return cf.Name + " (" + cf.EntityType + ")"
}

type UIComponent struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	Description    string     `json:"description" gorm:"type:text"`
	ComponentType  string     `json:"component_type" gorm:"size:20;not null"`
	Config         db.JSONMap `json:"config" gorm:"type:jsonb;not null;default:'{}'"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	IsSystem       bool       `json:"is_system" gorm:"default:false"`
	IsActive       bool       `json:"is_active" gorm:"default:true"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	UIComponentTypeDashboard = "dashboard"
	UIComponentTypeSidebar   = "sidebar"
	UIComponentTypeNavbar    = "navbar"
	UIComponentTypeWidget    = "widget"
	UIComponentTypeCard      = "card"
	UIComponentTypeTable     = "table"
	UIComponentTypeForm      = "form"
)

func (UIComponent) TableName() string {
	return "app_uicomponent"
}

func (ui UIComponent) String() string {
	return ui.Name + " (" + ui.ComponentType + ")"
}

type UserPreference struct {
	ID                   uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	UserID               uuid.UUID  `json:"user_id" gorm:"type:uuid;not null;uniqueIndex"`
	ThemeID              *uuid.UUID `json:"theme_id" gorm:"type:uuid"`
	SidebarCollapsed     bool       `json:"sidebar_collapsed" gorm:"default:false"`
	EnableAnimations     bool       `json:"enable_animations" gorm:"default:true"`
	EnableSounds         bool       `json:"enable_sounds" gorm:"default:true"`
	EnableNotifications  bool       `json:"enable_notifications" gorm:"default:true"`
	ItemsPerPage         int        `json:"items_per_page" gorm:"default:20"`
	DateFormat           string     `json:"date_format" gorm:"size:50;not null;default:'YYYY-MM-DD'"`
	TimeFormat           string     `json:"time_format" gorm:"size:50;not null;default:'HH:mm:ss'"`
	Language             string     `json:"language" gorm:"size:10;not null;default:'en'"`
	Timezone             string     `json:"timezone" gorm:"size:50;not null;default:'UTC'"`
	DashboardLayout      db.JSONMap `json:"dashboard_layout" gorm:"type:jsonb;default:'{}'"`
	AdditionalPreferences db.JSONMap `json:"additional_preferences" gorm:"type:jsonb;default:'{}'"`
	CreatedAt            time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt            time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

func (UserPreference) TableName() string {
	return "app_userpreference"
}

func (up UserPreference) String() string {
	return "User Preferences"
}

func init() {
	db.RegisterModel("Theme", Theme{})
	db.RegisterModel("CustomField", CustomField{})
	db.RegisterModel("UIComponent", UIComponent{})
	db.RegisterModel("UserPreference", UserPreference{})
}
