package scripts

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

func init() {
	db.RegisterScript("run_database_tests", "RunDatabaseTests")
}
