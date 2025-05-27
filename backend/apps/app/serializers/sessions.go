package serializers

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type SessionTagSerializer struct {
	core.Serializer
}

func NewSessionTagSerializer() *SessionTagSerializer {
	serializer := &SessionTagSerializer{
		Serializer: core.NewSerializer("SessionTag"),
	}

	serializer.SetFields([]string{
		"id", "name", "color", "organization", "organization_name", "created_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "organization_name",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")

	return serializer
}

type AgentSessionSerializer struct {
	core.Serializer
}

func NewAgentSessionSerializer() *AgentSessionSerializer {
	serializer := &AgentSessionSerializer{
		Serializer: core.NewSerializer("AgentSession"),
	}

	serializer.SetFields([]string{
		"id", "session_id", "title", "description", "user", "user_username",
		"organization", "organization_name", "agent_type", "status",
		"config", "metadata", "tags", "created_at", "updated_at",
		"completed_at", "duration",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "session_id", "created_at", "updated_at", "completed_at",
		"duration", "user_username", "organization_name",
	})
	
	serializer.AddReadOnlyField("user_username", "user.username")
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddNestedSerializer("tags", NewSessionTagSerializer(), true)

	return serializer
}

type AgentEventSerializer struct {
	core.Serializer
}

func NewAgentEventSerializer() *AgentEventSerializer {
	serializer := &AgentEventSerializer{
		Serializer: core.NewSerializer("AgentEvent"),
	}

	serializer.SetFields([]string{
		"id", "session", "session_id", "event_type", "content",
		"metadata", "timestamp",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "timestamp", "session_id",
	})
	
	serializer.AddReadOnlyField("session_id", "session.session_id")

	return serializer
}

type SessionFeedbackSerializer struct {
	core.Serializer
}

func NewSessionFeedbackSerializer() *SessionFeedbackSerializer {
	serializer := &SessionFeedbackSerializer{
		Serializer: core.NewSerializer("SessionFeedback"),
	}

	serializer.SetFields([]string{
		"id", "session", "session_id", "user", "user_username",
		"rating", "feedback", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "session_id", "user_username",
	})
	
	serializer.AddReadOnlyField("session_id", "session.session_id")
	serializer.AddReadOnlyField("user_username", "user.username")

	return serializer
}

func init() {
	core.RegisterSerializer("SessionTagSerializer", NewSessionTagSerializer())
	core.RegisterSerializer("AgentSessionSerializer", NewAgentSessionSerializer())
	core.RegisterSerializer("AgentEventSerializer", NewAgentEventSerializer())
	core.RegisterSerializer("SessionFeedbackSerializer", NewSessionFeedbackSerializer())
}
