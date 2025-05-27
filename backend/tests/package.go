package tests

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

func init() {
	core.RegisterTestPackage("tests", "Tests")
}
