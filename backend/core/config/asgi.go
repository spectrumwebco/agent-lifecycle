package config

import (
	"log"
	"net/http"

	"github.com/gorilla/mux"
	"github.com/gorilla/websocket"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/wsgi"
)

type WebSocketHandler interface {
	HandleConnection(conn *websocket.Conn, params map[string]string)
}

type AgentConsumer struct{}

func (c *AgentConsumer) HandleConnection(conn *websocket.Conn, params map[string]string) {
	wsgi.CallPythonWebSocketHandler("api.websocket.AgentConsumer", conn, params)
}

type SharedStateConsumer struct{}

func (c *SharedStateConsumer) HandleConnection(conn *websocket.Conn, params map[string]string) {
	wsgi.CallPythonWebSocketHandler("api.websocket_state.SharedStateConsumer", conn, params)
}

type OpenHandsSocketIOConsumer struct{}

func (c *OpenHandsSocketIOConsumer) HandleConnection(conn *websocket.Conn, params map[string]string) {
	wsgi.CallPythonWebSocketHandler("api.socketio_consumer.OpenHandsSocketIOConsumer", conn, params)
}

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all origins
	},
}

func WebSocketHandler(consumer WebSocketHandler) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			log.Printf("Error upgrading connection: %v", err)
			return
		}
		defer conn.Close()

		consumer.HandleConnection(conn, vars)
	}
}

func SetupASGIApplication() http.Handler {
	router := mux.NewRouter()

	agentConsumer := &AgentConsumer{}
	sharedStateConsumer := &SharedStateConsumer{}
	socketIOConsumer := &OpenHandsSocketIOConsumer{}

	router.HandleFunc("/ws/agent/{client_id}/", WebSocketHandler(agentConsumer))
	router.HandleFunc("/ws/agent/{client_id}/{task_id}/", WebSocketHandler(agentConsumer))
	router.HandleFunc("/ws/state/{state_type}/{state_id}/", WebSocketHandler(sharedStateConsumer))
	router.HandleFunc("/ws/state/", WebSocketHandler(sharedStateConsumer))
	router.HandleFunc("/socket.io/", WebSocketHandler(socketIOConsumer))

	router.PathPrefix("/").Handler(wsgi.DjangoHandler())

	return router
}

var Application = SetupASGIApplication()

func init() {
	core.RegisterConfig("asgi", map[string]interface{}{
		"application": Application,
	})
}
