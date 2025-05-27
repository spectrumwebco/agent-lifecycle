package models

import (
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type GitProvider struct {
	ID           uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name         string     `json:"name" gorm:"size:255;not null"`
	ProviderType string     `json:"provider_type" gorm:"size:20;not null"`
	URL          string     `json:"url" gorm:"not null"`
	APIURL       string     `json:"api_url"`
	AuthToken    string     `json:"auth_token" gorm:"size:255"`
	Username     string     `json:"username" gorm:"size:255"`
	UserID       *uuid.UUID `json:"user_id" gorm:"type:uuid"`
	OrganizationID *uuid.UUID `json:"organization_id" gorm:"type:uuid"`
	Config       db.JSONMap `json:"config" gorm:"type:jsonb;default:'{}'"`
	IsActive     bool       `json:"is_active" gorm:"default:true"`
	LastSyncAt   *time.Time `json:"last_sync_at"`
	CreatedAt    time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt    time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	GitProviderTypeGitHub    = "github"
	GitProviderTypeGitea     = "gitea"
	GitProviderTypeGitLab    = "gitlab"
	GitProviderTypeBitbucket = "bitbucket"
	GitProviderTypeGitee     = "gitee"
)

func (GitProvider) TableName() string {
	return "app_gitprovider"
}

func (gp GitProvider) String() string {
	return gp.Name + " (" + gp.ProviderType + ")"
}

type IssueTracker struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	ProviderType   string     `json:"provider_type" gorm:"size:20;not null"`
	URL            string     `json:"url" gorm:"not null"`
	APIURL         string     `json:"api_url"`
	APIKey         string     `json:"api_key" gorm:"size:255"`
	Username       string     `json:"username" gorm:"size:255"`
	Password       string     `json:"password" gorm:"size:255"`
	UserID         *uuid.UUID `json:"user_id" gorm:"type:uuid"`
	OrganizationID *uuid.UUID `json:"organization_id" gorm:"type:uuid"`
	ProjectKey     string     `json:"project_key" gorm:"size:255"`
	Config         db.JSONMap `json:"config" gorm:"type:jsonb;default:'{}'"`
	IsActive       bool       `json:"is_active" gorm:"default:true"`
	LastSyncAt     *time.Time `json:"last_sync_at"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	IssueTrackerTypeLinear = "linear"
	IssueTrackerTypeJira   = "jira"
	IssueTrackerTypePlane  = "plane"
	IssueTrackerTypeGitHub = "github"
	IssueTrackerTypeGitLab = "gitlab"
)

func (IssueTracker) TableName() string {
	return "app_issuetracker"
}

func (it IssueTracker) String() string {
	return it.Name + " (" + it.ProviderType + ")"
}

type IdeIntegration struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	IdeType        string     `json:"ide_type" gorm:"size:20;not null"`
	UserID         uuid.UUID  `json:"user_id" gorm:"type:uuid;not null"`
	OrganizationID *uuid.UUID `json:"organization_id" gorm:"type:uuid"`
	Config         db.JSONMap `json:"config" gorm:"type:jsonb;default:'{}'"`
	IsActive       bool       `json:"is_active" gorm:"default:true"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	IdeTypeWindsurf  = "windsurf"
	IdeTypeVSCode    = "vscode"
	IdeTypeJetBrains = "jetbrains"
)

func (IdeIntegration) TableName() string {
	return "app_ideintegration"
}

func (ii IdeIntegration) String() string {
	return ii.Name + " (" + ii.IdeType + ")"
}

type SlackIntegration struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	WorkspaceID    string     `json:"workspace_id" gorm:"size:255;not null"`
	WorkspaceName  string     `json:"workspace_name" gorm:"size:255;not null"`
	BotToken       string     `json:"bot_token" gorm:"size:255"`
	UserToken      string     `json:"user_token" gorm:"size:255"`
	UserID         *uuid.UUID `json:"user_id" gorm:"type:uuid"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	DefaultChannel string     `json:"default_channel" gorm:"size:255"`
	Config         db.JSONMap `json:"config" gorm:"type:jsonb;default:'{}'"`
	IsActive       bool       `json:"is_active" gorm:"default:true"`
	LastSyncAt     *time.Time `json:"last_sync_at"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

func (SlackIntegration) TableName() string {
	return "app_slackintegration"
}

func (si SlackIntegration) String() string {
	return si.Name + " (" + si.WorkspaceName + ")"
}

type AuthProvider struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	ProviderType   string     `json:"provider_type" gorm:"size:20;not null"`
	URL            string     `json:"url"`
	ClientID       string     `json:"client_id" gorm:"size:255"`
	ClientSecret   string     `json:"client_secret" gorm:"size:255"`
	Config         db.JSONMap `json:"config" gorm:"type:jsonb;default:'{}'"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	IsActive       bool       `json:"is_active" gorm:"default:true"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	AuthProviderTypeOAuth = "oauth"
	AuthProviderTypeSAML  = "saml"
	AuthProviderTypeLDAP  = "ldap"
	AuthProviderTypeOIDC  = "oidc"
)

func (AuthProvider) TableName() string {
	return "app_authprovider"
}

func (ap AuthProvider) String() string {
	return ap.Name + " (" + ap.ProviderType + ")"
}

func init() {
	db.RegisterModel("GitProvider", GitProvider{})
	db.RegisterModel("IssueTracker", IssueTracker{})
	db.RegisterModel("IdeIntegration", IdeIntegration{})
	db.RegisterModel("SlackIntegration", SlackIntegration{})
	db.RegisterModel("AuthProvider", AuthProvider{})
}
