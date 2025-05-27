package models

import (
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type McpServer struct {
	ID          uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name        string     `json:"name" gorm:"size:255;not null"`
	Description string     `json:"description" gorm:"type:text"`
	ServerType  string     `json:"server_type" gorm:"size:20;not null;default:'standard'"`
	Host        string     `json:"host" gorm:"size:255;not null"`
	Port        int        `json:"port" gorm:"not null"`
	APIKey      string     `json:"api_key" gorm:"size:255"`
	OrganizationID uuid.UUID `json:"organization_id" gorm:"type:uuid;not null"`
	Config      db.JSONMap `json:"config" gorm:"type:jsonb;default:'{}'"`
	IsActive    bool       `json:"is_active" gorm:"default:true"`
	LastPingAt  *time.Time `json:"last_ping_at"`
	CreatedAt   time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	McpServerTypeStandard  = "standard"
	McpServerTypeDedicated = "dedicated"
	McpServerTypeShared    = "shared"
)

func (McpServer) TableName() string {
	return "app_mcpserver"
}

func (ms McpServer) String() string {
	return ms.Name + " (" + ms.Host + ":" + string(ms.Port) + ")"
}

type McpClient struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	Description    string     `json:"description" gorm:"type:text"`
	ClientType     string     `json:"client_type" gorm:"size:20;not null;default:'agent'"`
	ClientID       string     `json:"client_id" gorm:"size:255;not null;uniqueIndex"`
	ClientSecret   string     `json:"client_secret" gorm:"size:255"`
	ServerID       uuid.UUID  `json:"server_id" gorm:"type:uuid;not null"`
	UserID         *uuid.UUID `json:"user_id" gorm:"type:uuid"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	Config         db.JSONMap `json:"config" gorm:"type:jsonb;default:'{}'"`
	IsActive       bool       `json:"is_active" gorm:"default:true"`
	LastConnectedAt *time.Time `json:"last_connected_at"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	McpClientTypeAgent       = "agent"
	McpClientTypeApplication = "application"
	McpClientTypeService     = "service"
)

func (McpClient) TableName() string {
	return "app_mcpclient"
}

func (mc McpClient) String() string {
	return mc.Name + " (" + mc.ClientID + ")"
}

type McpModel struct {
	ID               uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name             string     `json:"name" gorm:"size:255;not null"`
	Description      string     `json:"description" gorm:"type:text"`
	ModelType        string     `json:"model_type" gorm:"size:20;not null;default:'llm'"`
	Provider         string     `json:"provider" gorm:"size:20;not null;default:'kluster'"`
	ModelID          string     `json:"model_id" gorm:"size:255;not null"`
	Version          string     `json:"version" gorm:"size:50"`
	ContextWindow    int        `json:"context_window" gorm:"default:8192"`
	SupportsFunctions bool      `json:"supports_functions" gorm:"default:false"`
	SupportsVision    bool      `json:"supports_vision" gorm:"default:false"`
	SupportsStreaming bool      `json:"supports_streaming" gorm:"default:true"`
	ServerID         uuid.UUID  `json:"server_id" gorm:"type:uuid;not null"`
	OrganizationID   *uuid.UUID `json:"organization_id" gorm:"type:uuid"`
	Config           db.JSONMap `json:"config" gorm:"type:jsonb;default:'{}'"`
	IsActive         bool       `json:"is_active" gorm:"default:true"`
	CreatedAt        time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt        time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	McpModelTypeLLM        = "llm"
	McpModelTypeEmbedding  = "embedding"
	McpModelTypeVision     = "vision"
	McpModelTypeAudio      = "audio"
	McpModelTypeMultimodal = "multimodal"
)

const (
	McpModelProviderKluster   = "kluster"
	McpModelProviderOpenAI    = "openai"
	McpModelProviderAnthropic = "anthropic"
	McpModelProviderGoogle    = "google"
	McpModelProviderMistral   = "mistral"
	McpModelProviderLlama     = "llama"
)

func (McpModel) TableName() string {
	return "app_mcpmodel"
}

func (mm McpModel) String() string {
	return mm.Name + " (" + mm.Provider + "/" + mm.ModelID + ")"
}

type McpSession struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	ClientID       uuid.UUID  `json:"client_id" gorm:"type:uuid;not null"`
	ModelID        uuid.UUID  `json:"model_id" gorm:"type:uuid;not null"`
	SessionID      string     `json:"session_id" gorm:"size:255;not null;uniqueIndex"`
	UserID         *uuid.UUID `json:"user_id" gorm:"type:uuid"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	InputTokens    int        `json:"input_tokens" gorm:"default:0"`
	OutputTokens   int        `json:"output_tokens" gorm:"default:0"`
	TotalTokens    int        `json:"total_tokens" gorm:"default:0"`
	RequestCount   int        `json:"request_count" gorm:"default:0"`
	Status         string     `json:"status" gorm:"size:20;not null;default:'active'"`
	ErrorMessage   string     `json:"error_message" gorm:"type:text"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
	CompletedAt    *time.Time `json:"completed_at"`
}

const (
	McpSessionStatusActive    = "active"
	McpSessionStatusCompleted = "completed"
	McpSessionStatusError     = "error"
)

func (McpSession) TableName() string {
	return "app_mcpsession"
}

func (ms McpSession) String() string {
	return "Session " + ms.SessionID
}

func init() {
	db.RegisterModel("McpServer", McpServer{})
	db.RegisterModel("McpClient", McpClient{})
	db.RegisterModel("McpModel", McpModel{})
	db.RegisterModel("McpSession", McpSession{})
}
