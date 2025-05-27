package managers

import (
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type OrganizationManager struct {
	db.Manager
}

func NewOrganizationManager() *OrganizationManager {
	return &OrganizationManager{
		Manager: db.NewManager("Organization"),
	}
}

func (m *OrganizationManager) Active() *db.QuerySet {
	return m.Filter(db.Q{
		"is_active": true,
	})
}

func (m *OrganizationManager) WithUserCount() *db.QuerySet {
	return m.Annotate(db.Annotation{
		"user_count": db.Count("users"),
	})
}

func (m *OrganizationManager) WithWorkspaceCount() *db.QuerySet {
	return m.Annotate(db.Annotation{
		"workspace_count": db.Count("workspaces"),
	})
}

func (m *OrganizationManager) WithSessionCount() *db.QuerySet {
	return m.Annotate(db.Annotation{
		"session_count": db.Count("sessions"),
	})
}

func (m *OrganizationManager) WithStats() *db.QuerySet {
	return m.WithUserCount().WithWorkspaceCount().WithSessionCount()
}

func (m *OrganizationManager) GetByNaturalKey(name string) (interface{}, error) {
	var org interface{}
	err := m.Get(db.Q{
		"name": name,
	}, &org)
	return org, err
}

type WorkspaceManager struct {
	db.Manager
}

func NewWorkspaceManager() *WorkspaceManager {
	return &WorkspaceManager{
		Manager: db.NewManager("Workspace"),
	}
}

func (m *WorkspaceManager) Active() *db.QuerySet {
	return m.Filter(db.Q{
		"is_active": true,
	})
}

func (m *WorkspaceManager) WithSessionCount() *db.QuerySet {
	return m.Annotate(db.Annotation{
		"session_count": db.Count("sessions"),
	})
}

func (m *WorkspaceManager) WithRecentActivity() *db.QuerySet {
	thirtyDaysAgo := time.Now().AddDate(0, 0, -30)
	
	return m.Annotate(db.Annotation{
		"recent_sessions": db.Count("sessions", db.Q{
			"sessions__created_at__gte": thirtyDaysAgo,
		}),
	})
}

func (m *WorkspaceManager) WithStats() *db.QuerySet {
	return m.WithSessionCount().WithRecentActivity()
}

func (m *WorkspaceManager) GetByNaturalKey(organization, name string) (interface{}, error) {
	var workspace interface{}
	err := m.Get(db.Q{
		"organization__name": organization,
		"name":               name,
	}, &workspace)
	return workspace, err
}

type ApiKeyManager struct {
	db.Manager
}

func NewApiKeyManager() *ApiKeyManager {
	return &ApiKeyManager{
		Manager: db.NewManager("ApiKey"),
	}
}

func (m *ApiKeyManager) Active() *db.QuerySet {
	now := time.Now()
	
	return m.Filter(db.Q{
		"is_active":       true,
		"expires_at__gt":  now,
	})
}

func (m *ApiKeyManager) Expired() *db.QuerySet {
	now := time.Now()
	
	return m.Filter(db.Q{
		"expires_at__lte": now,
	})
}

func (m *ApiKeyManager) ExpiringSoon(days int) *db.QuerySet {
	if days == 0 {
		days = 7
	}
	
	now := time.Now()
	expiryThreshold := now.AddDate(0, 0, days)
	
	return m.Filter(db.Q{
		"is_active":       true,
		"expires_at__lte": expiryThreshold,
		"expires_at__gt":  now,
	})
}

func (m *ApiKeyManager) WithUsageStats() *db.QuerySet {
	now := time.Now()
	
	return m.Annotate(db.Annotation{
		"last_used_days_ago": db.ExpressionWrapper(
			now.Sub(db.Coalesce("last_used_at", now)),
			"DateTimeField",
		),
	})
}

func init() {
	core.RegisterManager("OrganizationManager", NewOrganizationManager())
	core.RegisterManager("WorkspaceManager", NewWorkspaceManager())
	core.RegisterManager("ApiKeyManager", NewApiKeyManager())
}
