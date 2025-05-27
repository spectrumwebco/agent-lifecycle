package models

import (
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type SecretGroup struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	Description    string     `json:"description" gorm:"type:text"`
	GroupType      string     `json:"group_type" gorm:"size:20;not null;default:'general'"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	CreatedByID    *uuid.UUID `json:"created_by_id" gorm:"type:uuid"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	SecretGroupTypeGeneral     = "general"
	SecretGroupTypeAPI         = "api"
	SecretGroupTypeDatabase    = "database"
	SecretGroupTypeEnvironment = "environment"
	SecretGroupTypeCredentials = "credentials"
)

func (SecretGroup) TableName() string {
	return "app_secretgroup"
}

func (sg SecretGroup) String() string {
	return sg.Name
}

type Secret struct {
	ID               uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name             string     `json:"name" gorm:"size:255;not null"`
	Description      string     `json:"description" gorm:"type:text"`
	SecretType       string     `json:"secret_type" gorm:"size:20;not null"`
	Value            []byte     `json:"value" gorm:"type:bytea;not null"`
	GroupID          uuid.UUID  `json:"group_id" gorm:"type:uuid;not null"`
	OrganizationID   uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	CreatedByID      *uuid.UUID `json:"created_by_id" gorm:"type:uuid"`
	ExpiresAt        *time.Time `json:"expires_at"`
	RotationInterval *int       `json:"rotation_interval"` // Days
	LastRotatedAt    *time.Time `json:"last_rotated_at"`
	Metadata         db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
	CreatedAt        time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt        time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	SecretTypeAPIKey           = "api_key"
	SecretTypePassword         = "password"
	SecretTypeToken            = "token"
	SecretTypeCertificate      = "certificate"
	SecretTypeSSHKey           = "ssh_key"
	SecretTypeEnvVar           = "env_var"
	SecretTypeConnectionString = "connection_string"
)

func (Secret) TableName() string {
	return "app_secret"
}

func (s Secret) String() string {
	return s.Name
}

type SecretAccess struct {
	ID           uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	SecretID     *uuid.UUID `json:"secret_id" gorm:"type:uuid"`
	GroupID      *uuid.UUID `json:"group_id" gorm:"type:uuid"`
	UserID       *uuid.UUID `json:"user_id" gorm:"type:uuid"`
	AccessLevel  string     `json:"access_level" gorm:"size:20;not null;default:'read'"`
	GrantedByID  *uuid.UUID `json:"granted_by_id" gorm:"type:uuid"`
	CreatedAt    time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt    time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
	ExpiresAt    *time.Time `json:"expires_at"`
}

const (
	AccessLevelRead  = "read"
	AccessLevelWrite = "write"
	AccessLevelAdmin = "admin"
)

func (SecretAccess) TableName() string {
	return "app_secretaccess"
}

func (sa SecretAccess) String() string {
	return sa.AccessLevel + " access"
}

type SecretAudit struct {
	ID          uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	SecretID    *uuid.UUID `json:"secret_id" gorm:"type:uuid"`
	GroupID     *uuid.UUID `json:"group_id" gorm:"type:uuid"`
	Action      string     `json:"action" gorm:"size:20;not null"`
	UserID      *uuid.UUID `json:"user_id" gorm:"type:uuid"`
	IPAddress   *string    `json:"ip_address" gorm:"type:inet"`
	UserAgent   string     `json:"user_agent" gorm:"type:text"`
	Details     db.JSONMap `json:"details" gorm:"type:jsonb;default:'{}'"`
	Timestamp   time.Time  `json:"timestamp" gorm:"autoCreateTime"`
}

const (
	AuditActionCreate = "create"
	AuditActionRead   = "read"
	AuditActionUpdate = "update"
	AuditActionDelete = "delete"
	AuditActionRotate = "rotate"
	AuditActionGrant  = "grant"
	AuditActionRevoke = "revoke"
)

func (SecretAudit) TableName() string {
	return "app_secretaudit"
}

func (sa SecretAudit) String() string {
	return sa.Action + " action"
}

func init() {
	db.RegisterModel("SecretGroup", SecretGroup{})
	db.RegisterModel("Secret", Secret{})
	db.RegisterModel("SecretAccess", SecretAccess{})
	db.RegisterModel("SecretAudit", SecretAudit{})
}
