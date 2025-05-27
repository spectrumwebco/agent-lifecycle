package managers

import (
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type AgentSessionManager struct {
	db.Manager
}

func NewAgentSessionManager() *AgentSessionManager {
	return &AgentSessionManager{
		Manager: db.NewManager("AgentSession"),
	}
}

func (m *AgentSessionManager) Active() *db.QuerySet {
	return m.Filter(db.Q{
		"status__in": []string{"running", "paused"},
	})
}

func (m *AgentSessionManager) Completed() *db.QuerySet {
	return m.Filter(db.Q{
		"status": "completed",
	})
}

func (m *AgentSessionManager) Failed() *db.QuerySet {
	return m.Filter(db.Q{
		"status": "failed",
	})
}

func (m *AgentSessionManager) Recent(days int) *db.QuerySet {
	if days == 0 {
		days = 7
	}
	
	recentDate := time.Now().AddDate(0, 0, -days)
	
	return m.Filter(db.Q{
		"created_at__gte": recentDate,
	})
}

func (m *AgentSessionManager) WithEventCount() *db.QuerySet {
	return m.Annotate(db.Annotation{
		"event_count": db.Count("events"),
	})
}

func (m *AgentSessionManager) WithDuration() *db.QuerySet {
	return m.Annotate(db.Annotation{
		"duration": db.ExpressionWrapper(
			db.Coalesce("completed_at", time.Now()).Sub(db.F("created_at")),
			"DateTimeField",
		),
	})
}

func (m *AgentSessionManager) WithStats() *db.QuerySet {
	return m.WithEventCount().WithDuration()
}

func (m *AgentSessionManager) ByUser(user interface{}) *db.QuerySet {
	return m.Filter(db.Q{
		"user": user,
	})
}

func (m *AgentSessionManager) ByOrganization(organization interface{}) *db.QuerySet {
	return m.Filter(db.Q{
		"organization": organization,
	})
}

func (m *AgentSessionManager) ByWorkspace(workspace interface{}) *db.QuerySet {
	return m.Filter(db.Q{
		"workspace": workspace,
	})
}

func (m *AgentSessionManager) ByTag(tagName string) *db.QuerySet {
	return m.Filter(db.Q{
		"tags__name": tagName,
	})
}

type AgentEventManager struct {
	db.Manager
}

func NewAgentEventManager() *AgentEventManager {
	return &AgentEventManager{
		Manager: db.NewManager("AgentEvent"),
	}
}

func (m *AgentEventManager) ByType(eventType string) *db.QuerySet {
	return m.Filter(db.Q{
		"event_type": eventType,
	})
}

func (m *AgentEventManager) BySession(session interface{}) *db.QuerySet {
	return m.Filter(db.Q{
		"session": session,
	})
}

func (m *AgentEventManager) Recent(days int) *db.QuerySet {
	if days == 0 {
		days = 1
	}
	
	recentDate := time.Now().AddDate(0, 0, -days)
	
	return m.Filter(db.Q{
		"timestamp__gte": recentDate,
	})
}

func (m *AgentEventManager) Errors() *db.QuerySet {
	return m.Filter(db.Q{
		"event_type__contains": "error",
	})
}

func (m *AgentEventManager) Warnings() *db.QuerySet {
	return m.Filter(db.Q{
		"event_type__contains": "warning",
	})
}

func (m *AgentEventManager) Chronological() *db.QuerySet {
	return m.OrderBy("timestamp")
}

func (m *AgentEventManager) ReverseChronological() *db.QuerySet {
	return m.OrderBy("-timestamp")
}

type SessionTagManager struct {
	db.Manager
}

func NewSessionTagManager() *SessionTagManager {
	return &SessionTagManager{
		Manager: db.NewManager("SessionTag"),
	}
}

func (m *SessionTagManager) WithSessionCount() *db.QuerySet {
	return m.Annotate(db.Annotation{
		"session_count": db.Count("sessions"),
	})
}

func (m *SessionTagManager) Popular(limit int) *db.QuerySet {
	if limit == 0 {
		limit = 10
	}
	
	return m.WithSessionCount().OrderBy("-session_count").Limit(limit)
}

func (m *SessionTagManager) ByOrganization(organization interface{}) *db.QuerySet {
	return m.Filter(db.Q{
		"organization": organization,
	})
}

func init() {
	core.RegisterManager("AgentSessionManager", NewAgentSessionManager())
	core.RegisterManager("AgentEventManager", NewAgentEventManager())
	core.RegisterManager("SessionTagManager", NewSessionTagManager())
}
