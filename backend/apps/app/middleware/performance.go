package middleware

import (
	"fmt"
	"log"
	"net/http"
	"runtime"
	"strings"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

var perfLogger = log.New(log.Writer(), "kled.performance: ", log.LstdFlags)

type PerformanceMiddleware struct {
	next                 http.Handler
	slowRequestThreshold int
	enableMemoryTracking bool
	enableQueryTracking  bool
	logAllRequests       bool
}

func NewPerformanceMiddleware(next http.Handler) *PerformanceMiddleware {
	slowRequestThreshold, _ := core.GetSetting("SLOW_REQUEST_THRESHOLD_MS", 500)
	enableMemoryTracking, _ := core.GetSetting("ENABLE_MEMORY_TRACKING", false)
	enableQueryTracking, _ := core.GetSetting("ENABLE_QUERY_TRACKING", true)
	logAllPerformance, _ := core.GetSetting("LOG_ALL_PERFORMANCE", false)

	return &PerformanceMiddleware{
		next:                 next,
		slowRequestThreshold: slowRequestThreshold.(int),
		enableMemoryTracking: enableMemoryTracking.(bool),
		enableQueryTracking:  enableQueryTracking.(bool),
		logAllRequests:       logAllPerformance.(bool),
	}
}

func (m *PerformanceMiddleware) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if m.shouldSkipMonitoring(r) {
		m.next.ServeHTTP(w, r)
		return
	}

	startTime := time.Now()
	
	var startQueries int
	if m.enableQueryTracking {
		startQueries = core.GetQueryCount()
	}

	var startMemory runtime.MemStats
	if m.enableMemoryTracking {
		runtime.ReadMemStats(&startMemory)
	}

	rw := &responseCapture{ResponseWriter: w}
	m.next.ServeHTTP(rw, r)

	durationMs := float64(time.Since(startTime).Milliseconds())

	perfData := map[string]interface{}{
		"timestamp":   time.Now().Format(time.RFC3339),
		"method":      r.Method,
		"path":        r.URL.Path,
		"status_code": rw.statusCode,
		"duration_ms": durationMs,
		"is_slow":     durationMs > float64(m.slowRequestThreshold),
	}

	if m.enableQueryTracking {
		endQueries := core.GetQueryCount()
		queryCount := endQueries - startQueries
		queryTimeMs := core.GetQueryTime(startQueries, endQueries)
		
		var avgQueryTimeMs float64
		if queryCount > 0 {
			avgQueryTimeMs = queryTimeMs / float64(queryCount)
		}

		perfData["query_count"] = queryCount
		perfData["query_time_ms"] = queryTimeMs
		perfData["avg_query_time_ms"] = avgQueryTimeMs
	}

	if m.enableMemoryTracking {
		var endMemory runtime.MemStats
		runtime.ReadMemStats(&endMemory)

		memoryCurrent := endMemory.Alloc - startMemory.Alloc
		memoryPeak := endMemory.TotalAlloc - startMemory.TotalAlloc

		perfData["memory_current"] = memoryCurrent
		perfData["memory_peak"] = memoryPeak
	}

	m.logPerformance(perfData)

	if includeHeaders, _ := core.GetSetting("INCLUDE_PERFORMANCE_HEADERS", false); includeHeaders.(bool) {
		w.Header().Set("X-Response-Time-Ms", fmt.Sprintf("%.2f", durationMs))
		
		if m.enableQueryTracking {
			w.Header().Set("X-Query-Count", fmt.Sprintf("%d", perfData["query_count"].(int)))
			w.Header().Set("X-Query-Time-Ms", fmt.Sprintf("%.2f", perfData["query_time_ms"].(float64)))
		}
	}
}

func (m *PerformanceMiddleware) shouldSkipMonitoring(r *http.Request) bool {
	skipPaths := []string{
		"/static/",
		"/media/",
		"/favicon.ico",
		"/health/",
		"/metrics/",
	}

	for _, path := range skipPaths {
		if strings.HasPrefix(r.URL.Path, path) {
			return true
		}
	}

	return false
}

func (m *PerformanceMiddleware) logPerformance(perfData map[string]interface{}) {
	isSlow := perfData["is_slow"].(bool)
	
	if isSlow || m.logAllRequests {
		logMessage := fmt.Sprintf("%v", perfData)
		
		if isSlow {
			perfLogger.Printf("WARNING: Slow request: %s", logMessage)
		} else {
			perfLogger.Printf("INFO: Request performance: %s", logMessage)
		}
	}
}

func init() {
	core.RegisterMiddleware("PerformanceMiddleware", func(next http.Handler) http.Handler {
		return NewPerformanceMiddleware(next)
	})
}
