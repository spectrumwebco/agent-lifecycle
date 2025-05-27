package config

import (
	"net/http"

	"github.com/gorilla/mux"
	"github.com/gorilla/websocket"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/wsgi"
)

type PythonAgentConsumer struct{}

func (c *PythonAgentConsumer) HandleConnection(conn *websocket.Conn, params map[string]string) {
	wsgi.CallPythonWebSocketHandler("apps.python_agent.agent.django_views.consumers.AgentConsumer", conn, params)
}

func SetupWebSocketRoutes() *mux.Router {
	router := mux.NewRouter()

	agentConsumer := &AgentConsumer{}
	sharedStateConsumer := &SharedStateConsumer{}
	socketIOConsumer := &OpenHandsSocketIOConsumer{}
	pythonAgentConsumer := &PythonAgentConsumer{}

	router.HandleFunc("/ws/agent/{client_id}/", WebSocketHandler(agentConsumer))
	router.HandleFunc("/ws/agent/{client_id}/{task_id}/", WebSocketHandler(agentConsumer))
	router.HandleFunc("/ws/state/{state_type}/{state_id}/", WebSocketHandler(sharedStateConsumer))
	router.HandleFunc("/ws/state/", WebSocketHandler(sharedStateConsumer))
	router.HandleFunc("/socket.io/", WebSocketHandler(socketIOConsumer))
	router.HandleFunc("/ws/python_agent/{thread_id}/", WebSocketHandler(pythonAgentConsumer))

	return router
}

func SetupRoutingApplication() http.Handler {
	router := SetupWebSocketRoutes()

	router.PathPrefix("/").Handler(wsgi.DjangoHandler())

	handler := wsgi.AllowedHostsOriginValidator(router)
	handler = wsgi.AuthMiddlewareStack(handler)

	return handler
}

var RoutingApplication = SetupRoutingApplication()

func init() {
	core.RegisterConfig("routing", map[string]interface{}{
		"application":            RoutingApplication,
		"websocket_urlpatterns": SetupWebSocketRoutes(),
	})
}
