package tests

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

func init() {
	db.RegisterTestPackage("database_tests", "DatabaseTests")
}
