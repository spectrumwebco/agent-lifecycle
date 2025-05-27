package config

import (
	"os"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/wsgi"
)

func init() {
	if os.Getenv("DJANGO_SETTINGS_MODULE") == "" {
		os.Setenv("DJANGO_SETTINGS_MODULE", "core.config.settings")
	}

	application := wsgi.GetWSGIApplication()

	core.RegisterConfig("wsgi", map[string]interface{}{
		"application": application,
	})
}

var Application = wsgi.GetWSGIApplication()
