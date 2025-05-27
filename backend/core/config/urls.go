package config

import (
	"net/http"

	"github.com/gorilla/mux"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

func SetupURLPatterns() *mux.Router {
	router := mux.NewRouter()

	router.PathPrefix("/admin/").Handler(core.DjangoView("django.contrib.admin.site.urls"))
	router.PathPrefix("/api/").Handler(core.DjangoInclude("api.urls"))
	router.PathPrefix("/ml-api/").Handler(core.DjangoInclude("ml_api.urls"))
	router.PathPrefix("/ninja-api/").Handler(core.DjangoView("api.ninja_api.api.urls"))
	router.PathPrefix("/docs/").Handler(core.DjangoInclude("api.swagger.urlpatterns"))
	router.PathPrefix("/agent/").Handler(core.DjangoInclude("apps.python_agent.urls"))
	router.PathPrefix("/ml/").Handler(core.DjangoInclude("apps.python_ml.urls"))
	router.PathPrefix("/tools/").Handler(core.DjangoInclude("apps.python_agent.tools.urls"))
	router.PathPrefix("/app/").Handler(core.DjangoInclude("apps.app.urls"))
	
	router.PathPrefix("/").Handler(http.RedirectHandler("/api/", http.StatusTemporaryRedirect))

	core.AddRouter("api.ninja_api.api", "/grpc", "api.grpc_service.router")

	return router
}

var URLPatterns = SetupURLPatterns()

func init() {
	core.RegisterConfig("urls", map[string]interface{}{
		"urlpatterns": URLPatterns,
	})
}
