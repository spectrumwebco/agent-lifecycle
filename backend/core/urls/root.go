package urls

import (
	"github.com/gorilla/mux"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

func SetupRootURLPatterns() *mux.Router {
	router := mux.NewRouter()

	router.PathPrefix("/admin/").Handler(core.DjangoView("django.contrib.admin.site.urls"))
	router.PathPrefix("/api/").Handler(core.DjangoInclude("apps.app.urls"))
	router.PathPrefix("/agent/").Handler(core.DjangoInclude("apps.agent.urls"))
	router.PathPrefix("/ml/").Handler(core.DjangoInclude("apps.ml.urls"))

	return router
}

var RootURLPatterns = SetupRootURLPatterns()

func init() {
	core.RegisterConfig("root_urls", map[string]interface{}{
		"urlpatterns": RootURLPatterns,
	})
}
