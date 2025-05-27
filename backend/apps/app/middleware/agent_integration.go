package middleware

import (
	"log"
	"net/http"
	"strings"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

var logger = log.New(log.Writer(), "kled.agent_integration: ", log.LstdFlags)

type AgentIntegrationMiddleware struct {
	next              http.Handler
	createKledRuntime func() interface{}
	createVeigarRuntime func() interface{}
	kledRuntime       interface{}
	veigarRuntime     interface{}
}

func NewAgentIntegrationMiddleware(next http.Handler) *AgentIntegrationMiddleware {
	middleware := &AgentIntegrationMiddleware{
		next: next,
	}

	var createKledRuntime func() interface{}
	if kledIntegration, err := core.ImportPythonModule("apps.python_agent.kled.django_integration.django_integration"); err == nil {
		if fn, err := kledIntegration.GetAttr("create_agent_runtime"); err == nil {
			createKledRuntime = func() interface{} {
				result, err := fn.Call()
				if err != nil {
					logger.Printf("Error creating Kled runtime: %v", err)
					return nil
				}
				return result
			}
		}
	} else {
		logger.Printf("Kled agent integration not available: %v", err)
	}
	middleware.createKledRuntime = createKledRuntime

	var createVeigarRuntime func() interface{}
	if veigarIntegration, err := core.ImportPythonModule("apps.python_agent.veigar.django_integration.django_integration"); err == nil {
		if fn, err := veigarIntegration.GetAttr("create_agent_runtime"); err == nil {
			createVeigarRuntime = func() interface{} {
				result, err := fn.Call()
				if err != nil {
					logger.Printf("Error creating Veigar runtime: %v", err)
					return nil
				}
				return result
			}
		}
	} else {
		logger.Printf("Veigar agent integration not available: %v", err)
	}
	middleware.createVeigarRuntime = createVeigarRuntime

	if autoInitialize, _ := core.GetSetting("AUTO_INITIALIZE_AGENT_RUNTIMES", false); autoInitialize.(bool) {
		middleware.initializeAgentRuntimes()
	}

	return middleware
}

func (m *AgentIntegrationMiddleware) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	ctx = core.SetContextValue(ctx, "KLED_RUNTIME", m.kledRuntime)
	ctx = core.SetContextValue(ctx, "VEIGAR_RUNTIME", m.veigarRuntime)
	r = r.WithContext(ctx)

	isAgentRequest := m.isAgentRequest(r)

	if isAgentRequest && (m.kledRuntime == nil || m.veigarRuntime == nil) {
		m.initializeAgentRuntimes()
	}

	m.next.ServeHTTP(w, r)

	if isAgentRequest {
		w.Header().Set("X-Agent-Enabled", "true")
	}
}

func (m *AgentIntegrationMiddleware) isAgentRequest(r *http.Request) bool {
	agentPaths := []string{
		"/api/sessions/",
		"/api/events/",
		"/api/agent/",
		"/api/kled/",
		"/api/veigar/",
	}

	for _, path := range agentPaths {
		if strings.HasPrefix(r.URL.Path, path) {
			return true
		}
	}

	if r.Header.Get("X-Agent-Request") == "true" {
		return true
	}

	return false
}

func (m *AgentIntegrationMiddleware) initializeAgentRuntimes() {
	if m.createKledRuntime != nil && m.kledRuntime == nil {
		defer func() {
			if r := recover(); r != nil {
				logger.Printf("Recovered from panic in Kled runtime initialization: %v", r)
			}
		}()

		m.kledRuntime = m.createKledRuntime()
		if m.kledRuntime != nil {
			logger.Println("Kled agent runtime initialized")
		}
	}

	if m.createVeigarRuntime != nil && m.veigarRuntime == nil {
		defer func() {
			if r := recover(); r != nil {
				logger.Printf("Recovered from panic in Veigar runtime initialization: %v", r)
			}
		}()

		m.veigarRuntime = m.createVeigarRuntime()
		if m.veigarRuntime != nil {
			logger.Println("Veigar agent runtime initialized")
		}
	}
}

func init() {
	core.RegisterMiddleware("AgentIntegrationMiddleware", func(next http.Handler) http.Handler {
		return NewAgentIntegrationMiddleware(next)
	})
}
