package integration

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

func init() {
	core.RegisterTestPackage("integration", "IntegrationTests")
}
