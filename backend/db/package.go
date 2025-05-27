package db

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

func init() {
	db.RegisterIntegration("integrations", "DatabaseIntegrations")
}
