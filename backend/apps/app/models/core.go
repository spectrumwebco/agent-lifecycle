package models

import (
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type User struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Username       string     `json:"username" gorm:"size:150;uniqueIndex;not null"`
	Password       string     `json:"password" gorm:"size:128;not null"`
	FirstName      string     `json:"first_name" gorm:"size:150"`
	LastName       string     `json:"last_name" gorm:"size:150"`
	Email          string     `json:"email" gorm:"size:254;index"`
	IsStaff        bool       `json:"is_staff" gorm:"default:false"`
	IsActive       bool       `json:"is_active" gorm:"default:true"`
	IsSuperuser    bool       `json:"is_superuser" gorm:"default:false"`
	DateJoined     time.Time  `json:"date_joined" gorm:"not null"`
	LastLogin      *time.Time `json:"last_login"`
	Bio            string     `json:"bio" gorm:"type:text"`
	Avatar         string     `json:"avatar"`
	OrganizationID *uuid.UUID `json:"organization_id" gorm:"type:uuid"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

func (User) TableName() string {
	return "app_user"
}

func (u User) String() string {
	return u.Username
}

type Organization struct {
	ID          uuid.UUID `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name        string    `json:"name" gorm:"size:255;not null"`
	Slug        string    `json:"slug" gorm:"uniqueIndex;not null"`
	Description string    `json:"description" gorm:"type:text"`
	Logo        string    `json:"logo"`
	Website     string    `json:"website"`
	CreatedAt   time.Time `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time `json:"updated_at" gorm:"autoUpdateTime"`
}

func (Organization) TableName() string {
	return "app_organization"
}

func (o Organization) String() string {
	return o.Name
}

type Workspace struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	Slug           string     `json:"slug" gorm:"not null"`
	Description    string     `json:"description" gorm:"type:text"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	CreatedByID    *uuid.UUID `json:"created_by_id" gorm:"type:uuid"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

func (Workspace) TableName() string {
	return "app_workspace"
}

func (w Workspace) String() string {
	return w.Name
}

type ApiKey struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	Key            string     `json:"key" gorm:"size:64;uniqueIndex;not null"`
	UserID         uuid.UUID  `json:"user_id" gorm:"type:uuid;not null"`
	OrganizationID *uuid.UUID `json:"organization_id" gorm:"type:uuid"`
	Scopes         db.JSONMap `json:"scopes" gorm:"type:jsonb;default:'[]'"`
	ExpiresAt      *time.Time `json:"expires_at"`
	LastUsedAt     *time.Time `json:"last_used_at"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

func (ApiKey) TableName() string {
	return "app_apikey"
}

func (a ApiKey) String() string {
	return a.Name
}

type UserManager struct{}

func (um *UserManager) CreateUser(username, email, password string) (*User, error) {
	return db.CallPythonMethod("django.contrib.auth.models", "UserManager", "create_user", 
		map[string]interface{}{
			"username": username,
			"email":    email,
			"password": password,
		}).(func() (*User, error))()
}

func (um *UserManager) CreateSuperuser(username, email, password string) (*User, error) {
	return db.CallPythonMethod("django.contrib.auth.models", "UserManager", "create_superuser", 
		map[string]interface{}{
			"username": username,
			"email":    email,
			"password": password,
		}).(func() (*User, error))()
}

func (um *UserManager) GetByNaturalKey(username string) (*User, error) {
	return db.CallPythonMethod("django.contrib.auth.models", "UserManager", "get_by_natural_key", 
		map[string]interface{}{
			"username": username,
		}).(func() (*User, error))()
}

var Users = &UserManager{}

func init() {
	db.RegisterModel("User", User{})
	db.RegisterModel("Organization", Organization{})
	db.RegisterModel("Workspace", Workspace{})
	db.RegisterModel("ApiKey", ApiKey{})
	
	db.RegisterManager("UserManager", Users)
}
