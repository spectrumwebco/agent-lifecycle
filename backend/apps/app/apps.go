package app

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type ApplicationConfig struct {
	DefaultAutoField string
	Name             string
	VerboseName      string
}

func NewApplicationConfig() *ApplicationConfig {
	return &ApplicationConfig{
		DefaultAutoField: "django.db.models.BigAutoField",
		Name:             "apps.app",
		VerboseName:      "Application",
	}
}

func init() {
	appConfig := NewApplicationConfig()
	core.RegisterApp(appConfig.Name, appConfig)
}
