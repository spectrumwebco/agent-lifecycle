package models

import (
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type DatabaseConnection struct {
	ID               uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name             string     `json:"name" gorm:"size:255;not null"`
	Description      string     `json:"description" gorm:"type:text"`
	DBType           string     `json:"db_type" gorm:"size:20;not null"`
	Host             string     `json:"host" gorm:"size:255"`
	Port             *int       `json:"port"`
	Database         string     `json:"database" gorm:"size:255"`
	Username         string     `json:"username" gorm:"size:255"`
	Password         string     `json:"password" gorm:"size:255"`
	UseSSL           bool       `json:"use_ssl" gorm:"default:false"`
	SSLCA            string     `json:"ssl_ca" gorm:"type:text"`
	SSLCert          string     `json:"ssl_cert" gorm:"type:text"`
	SSLKey           string     `json:"ssl_key" gorm:"type:text"`
	ConnectionString string     `json:"connection_string" gorm:"type:text"`
	UserID           *uuid.UUID `json:"user_id" gorm:"type:uuid"`
	OrganizationID   uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	WorkspaceID      *uuid.UUID `json:"workspace_id" gorm:"type:uuid"`
	IsActive         bool       `json:"is_active" gorm:"default:true"`
	LastConnectedAt  *time.Time `json:"last_connected_at"`
	CreatedAt        time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt        time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	DBTypePostgreSQL = "postgresql"
	DBTypeMySQL      = "mysql"
	DBTypeMariaDB    = "mariadb"
	DBTypeSQLite     = "sqlite"
	DBTypeOracle     = "oracle"
	DBTypeSQLServer  = "sqlserver"
	DBTypeMongoDB    = "mongodb"
	DBTypeRedis      = "redis"
	DBTypeSupabase   = "supabase"
	DBTypeDragonfly  = "dragonfly"
	DBTypeRAGflow    = "ragflow"
	DBTypeRocketMQ   = "rocketmq"
)

func (DatabaseConnection) TableName() string {
	return "app_databaseconnection"
}

func (dc DatabaseConnection) String() string {
	return dc.Name + " (" + dc.DBType + ")"
}

type DatabaseQuery struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Title          string     `json:"title" gorm:"size:255;not null"`
	Description    string     `json:"description" gorm:"type:text"`
	Query          string     `json:"query" gorm:"type:text;not null"`
	NLDescription  string     `json:"nl_description" gorm:"type:text"`
	ConnectionID   uuid.UUID  `json:"connection_id" gorm:"type:uuid;not null"`
	UserID         uuid.UUID  `json:"user_id" gorm:"type:uuid;not null"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	WorkspaceID    *uuid.UUID `json:"workspace_id" gorm:"type:uuid"`
	QueryType      string     `json:"query_type" gorm:"size:20;not null;default:'select'"`
	Parameters     db.JSONMap `json:"parameters" gorm:"type:jsonb;default:'{}'"`
	IsSaved        bool       `json:"is_saved" gorm:"default:false"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	QueryTypeSelect = "select"
	QueryTypeInsert = "insert"
	QueryTypeUpdate = "update"
	QueryTypeDelete = "delete"
	QueryTypeCreate = "create"
	QueryTypeAlter  = "alter"
	QueryTypeDrop   = "drop"
	QueryTypeOther  = "other"
)

func (DatabaseQuery) TableName() string {
	return "app_databasequery"
}

func (dq DatabaseQuery) String() string {
	return dq.Title
}

type QueryHistory struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	QueryID        *uuid.UUID `json:"query_id" gorm:"type:uuid"`
	QueryText      string     `json:"query_text" gorm:"type:text;not null"`
	ConnectionID   *uuid.UUID `json:"connection_id" gorm:"type:uuid"`
	UserID         uuid.UUID  `json:"user_id" gorm:"type:uuid;not null"`
	ExecutionTime  float64    `json:"execution_time" gorm:"not null"`
	RowCount       *int       `json:"row_count"`
	Status         string     `json:"status" gorm:"size:20;not null;default:'success'"`
	ErrorMessage   string     `json:"error_message" gorm:"type:text"`
	Results        db.JSONMap `json:"results" gorm:"type:jsonb;default:'{}'"`
	ExecutedAt     time.Time  `json:"executed_at" gorm:"autoCreateTime"`
}

const (
	QueryStatusSuccess   = "success"
	QueryStatusError     = "error"
	QueryStatusTimeout   = "timeout"
	QueryStatusCancelled = "cancelled"
)

func (QueryHistory) TableName() string {
	return "app_queryhistory"
}

func (qh QueryHistory) String() string {
	return "Query History"
}

type QueryTemplate struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	Description    string     `json:"description" gorm:"type:text"`
	Template       string     `json:"template" gorm:"type:text;not null"`
	DBType         string     `json:"db_type" gorm:"size:20;not null"`
	UserID         *uuid.UUID `json:"user_id" gorm:"type:uuid"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	Variables      db.JSONMap `json:"variables" gorm:"type:jsonb;default:'[]'"`
	IsPublic       bool       `json:"is_public" gorm:"default:false"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

func (QueryTemplate) TableName() string {
	return "app_querytemplate"
}

func (qt QueryTemplate) String() string {
	return qt.Name + " (" + qt.DBType + ")"
}

func init() {
	db.RegisterModel("DatabaseConnection", DatabaseConnection{})
	db.RegisterModel("DatabaseQuery", DatabaseQuery{})
	db.RegisterModel("QueryHistory", QueryHistory{})
	db.RegisterModel("QueryTemplate", QueryTemplate{})
}
