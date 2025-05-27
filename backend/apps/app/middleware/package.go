package middleware

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

func init() {
	core.RegisterPackage("middleware", "MiddlewarePackage")
}
