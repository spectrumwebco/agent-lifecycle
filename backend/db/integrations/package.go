//
package integrations

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

func init() {
	db.RegisterIntegration("kafka", "KafkaClient")
	db.RegisterIntegration("doris", "DorisClient")
}
