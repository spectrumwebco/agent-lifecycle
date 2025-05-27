package app

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/api"
)

var router = api.NewDefaultRouter()

func init() {
	router.Register("state/shared", "SharedStateViewSet", "shared-state")
	router.Register("conversations", "ConversationViewSet", "conversation")

	api.RegisterURLPatterns([]api.URLPattern{
		{Path: "", Include: router.URLs()},

		{Path: "auth/login/", View: "login_view", Name: "login"},
		{Path: "auth/register/", View: "register_view", Name: "register"},
		{Path: "auth/logout/", View: "logout_view", Name: "logout"},
		{Path: "auth/github/", View: "github_login_view", Name: "github-auth"},
		{Path: "auth/github/callback/", View: "github_callback_view", Name: "github-callback"},
		{Path: "auth/gitee/", View: "gitee_login_view", Name: "gitee-auth"},
		{Path: "auth/gitee/callback/", View: "gitee_callback_view", Name: "gitee-callback"},
		{Path: "auth/settings/", View: "user_settings_view", Name: "user-settings"},

		{Path: "events/send/", View: "send_event", Name: "send-event"},
		{Path: "events/forward/", View: "forward_to_agent", Name: "forward-to-agent"},
		{Path: "events/<str:conversation_id>/", View: "get_events", Name: "get-events"},
		{Path: "events/<str:conversation_id>/create/", View: "create_event", Name: "create-event"},

		{Path: "options/models/", View: "get_models", Name: "get-models"},
		{Path: "options/agents/", View: "get_agents", Name: "get-agents"},
		{Path: "options/security-analyzers/", View: "get_security_analyzers", Name: "get-security-analyzers"},
		{Path: "options/config/", View: "get_config", Name: "get-config"},

		{Path: "billing/credits/", View: "get_credits", Name: "get-credits"},
		{Path: "billing/credits/add/", View: "add_credits", Name: "add-credits"},

	})
}
