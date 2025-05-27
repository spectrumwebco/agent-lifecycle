package middleware

import (
	"encoding/json"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

var requestLogger = log.New(log.Writer(), "kled.request: ", log.LstdFlags)

type RequestLoggingMiddleware struct {
	next             http.Handler
	logRequestBody   bool
	logResponseBody  bool
	maxBodyLength    int
}

func NewRequestLoggingMiddleware(next http.Handler) *RequestLoggingMiddleware {
	logRequestBody, _ := core.GetSetting("LOG_REQUEST_BODY", false)
	logResponseBody, _ := core.GetSetting("LOG_RESPONSE_BODY", false)
	maxBodyLength, _ := core.GetSetting("MAX_LOGGED_BODY_LENGTH", 1000)

	return &RequestLoggingMiddleware{
		next:             next,
		logRequestBody:   logRequestBody.(bool),
		logResponseBody:  logResponseBody.(bool),
		maxBodyLength:    maxBodyLength.(int),
	}
}

func (m *RequestLoggingMiddleware) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if m.shouldSkipLogging(r) {
		m.next.ServeHTTP(w, r)
		return
	}

	startTime := time.Now()
	requestTime := startTime

	requestData := m.getRequestData(r)

	rw := &responseCapture{ResponseWriter: w}
	m.next.ServeHTTP(rw, r)

	durationMs := float64(time.Since(startTime).Milliseconds())

	responseData := m.getResponseData(rw)

	var userID string
	user := core.GetUserFromRequest(r)
	if user != nil && user.IsAuthenticated() {
		userID = user.GetID()
	}

	logData := map[string]interface{}{
		"timestamp":       requestTime.Format(time.RFC3339),
		"method":          r.Method,
		"path":            r.URL.Path,
		"query_params":    r.URL.Query(),
		"status_code":     rw.statusCode,
		"duration_ms":     durationMs,
		"user_id":         userID,
		"ip_address":      m.getClientIP(r),
		"user_agent":      r.UserAgent(),
		"request_id":      r.Header.Get("X-Request-ID"),
		"content_length":  r.ContentLength,
		"response_length": rw.size,
	}

	if m.logRequestBody && requestData != nil {
		logData["request_body"] = m.truncateData(requestData)
	}

	if m.logResponseBody && responseData != nil {
		logData["response_body"] = m.truncateData(responseData)
	}

	m.logRequest(logData, rw.statusCode)
}

func (m *RequestLoggingMiddleware) shouldSkipLogging(r *http.Request) bool {
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

func (m *RequestLoggingMiddleware) getRequestData(r *http.Request) map[string]interface{} {
	if !m.logRequestBody {
		return nil
	}

	contentType := r.Header.Get("Content-Type")
	if !strings.Contains(contentType, "application/json") {
		return nil
	}

	var data map[string]interface{}
	decoder := json.NewDecoder(r.Body)
	if err := decoder.Decode(&data); err != nil {
		return map[string]interface{}{"error": "Could not decode JSON body"}
	}

	r.Body = core.ResetRequestBody(r)

	return data
}

func (m *RequestLoggingMiddleware) getResponseData(rw *responseCapture) map[string]interface{} {
	if !m.logResponseBody {
		return nil
	}

	contentType := rw.Header().Get("Content-Type")
	if !strings.Contains(contentType, "application/json") {
		return nil
	}

	var data map[string]interface{}
	if err := json.Unmarshal(rw.body, &data); err != nil {
		return map[string]interface{}{"error": "Could not decode JSON response"}
	}

	return data
}

func (m *RequestLoggingMiddleware) getClientIP(r *http.Request) string {
	xForwardedFor := r.Header.Get("X-Forwarded-For")
	if xForwardedFor != "" {
		parts := strings.Split(xForwardedFor, ",")
		return strings.TrimSpace(parts[0])
	}
	return r.RemoteAddr
}

func (m *RequestLoggingMiddleware) truncateData(data map[string]interface{}) map[string]interface{} {
	dataBytes, err := json.Marshal(data)
	if err != nil {
		return map[string]interface{}{"error": "Could not marshal data"}
	}

	if len(dataBytes) > m.maxBodyLength {
		return map[string]interface{}{
			"truncated": string(dataBytes[:m.maxBodyLength]) + "...",
		}
	}

	return data
}

func (m *RequestLoggingMiddleware) logRequest(logData map[string]interface{}, statusCode int) {
	logBytes, err := json.Marshal(logData)
	if err != nil {
		requestLogger.Printf("Error marshaling log data: %v", err)
		return
	}

	logMessage := string(logBytes)

	if statusCode >= 500 {
		requestLogger.Printf("ERROR: %s", logMessage)
	} else if statusCode >= 400 {
		requestLogger.Printf("WARNING: %s", logMessage)
	} else {
		requestLogger.Printf("INFO: %s", logMessage)
	}
}

type responseCapture struct {
	http.ResponseWriter
	statusCode int
	size       int
	body       []byte
}

func (rw *responseCapture) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

func (rw *responseCapture) Write(b []byte) (int, error) {
	if rw.statusCode == 0 {
		rw.statusCode = http.StatusOK
	}
	
	size, err := rw.ResponseWriter.Write(b)
	rw.size += size
	rw.body = append(rw.body, b...)
	return size, err
}

func init() {
	core.RegisterMiddleware("RequestLoggingMiddleware", func(next http.Handler) http.Handler {
		return NewRequestLoggingMiddleware(next)
	})
}
