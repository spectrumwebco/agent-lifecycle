package middleware

import (
	"crypto/md5"
	"encoding/hex"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

var logger = log.New(log.Writer(), "kled.security: ", log.LstdFlags)

type SecurityMiddleware struct {
	next                http.Handler
	enableRateLimiting  bool
	rateLimitRequests   int
	rateLimitWindow     int // seconds
	enableCSP           bool
	cspReportOnly       bool
}

func NewSecurityMiddleware(next http.Handler) *SecurityMiddleware {
	enableRateLimiting, _ := core.GetSetting("ENABLE_RATE_LIMITING", true)
	rateLimitRequests, _ := core.GetSetting("RATE_LIMIT_REQUESTS", 100)
	rateLimitWindow, _ := core.GetSetting("RATE_LIMIT_WINDOW", 60)
	enableCSP, _ := core.GetSetting("ENABLE_CONTENT_SECURITY_POLICY", true)
	cspReportOnly, _ := core.GetSetting("CSP_REPORT_ONLY", false)

	return &SecurityMiddleware{
		next:                next,
		enableRateLimiting:  enableRateLimiting.(bool),
		rateLimitRequests:   rateLimitRequests.(int),
		rateLimitWindow:     rateLimitWindow.(int),
		enableCSP:           enableCSP.(bool),
		cspReportOnly:       cspReportOnly.(bool),
	}
}

func (m *SecurityMiddleware) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if m.shouldSkipSecurity(r) {
		m.next.ServeHTTP(w, r)
		return
	}

	if m.enableRateLimiting {
		if exceeded, status, message := m.checkRateLimit(r); exceeded {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(status)
			w.Write([]byte(`{"error": "` + message + `"}`))
			return
		}
	}

	rw := &responseWriter{ResponseWriter: w}
	m.next.ServeHTTP(rw, r)
	m.addSecurityHeaders(rw)
}

func (m *SecurityMiddleware) shouldSkipSecurity(r *http.Request) bool {
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

func (m *SecurityMiddleware) checkRateLimit(r *http.Request) (bool, int, string) {
	user := core.GetUserFromRequest(r)
	if user != nil && user.IsAuthenticated() && user.IsStaff() {
		return false, 0, ""
	}

	clientID := m.getClientIdentifier(r)
	cacheKey := "rate_limit:" + clientID

	requestCount, err := core.GetCache(cacheKey, 0)
	if err != nil {
		logger.Printf("Error getting rate limit from cache: %v", err)
		return false, 0, ""
	}

	count, ok := requestCount.(int)
	if !ok {
		count = 0
	}

	if count >= m.rateLimitRequests {
		logger.Printf("Rate limit exceeded for %s", clientID)
		return true, 429, "Rate limit exceeded. Please try again later."
	}

	if count == 0 {
		core.SetCache(cacheKey, 1, time.Duration(m.rateLimitWindow)*time.Second)
	} else {
		core.IncrCache(cacheKey, 1)
	}

	return false, 0, ""
}

func (m *SecurityMiddleware) getClientIdentifier(r *http.Request) string {
	user := core.GetUserFromRequest(r)
	if user != nil && user.IsAuthenticated() {
		return "user:" + user.GetID()
	}

	ip := r.Header.Get("X-Forwarded-For")
	if ip != "" {
		parts := strings.Split(ip, ",")
		ip = strings.TrimSpace(parts[0])
	} else {
		ip = r.RemoteAddr
	}

	userAgent := r.UserAgent()
	identifier := ip + ":" + userAgent

	hasher := md5.New()
	hasher.Write([]byte(identifier))
	hashed := hex.EncodeToString(hasher.Sum(nil))

	return "ip:" + hashed
}

func (m *SecurityMiddleware) addSecurityHeaders(w http.ResponseWriter) {
	if m.enableCSP {
		headerName := "Content-Security-Policy"
		if m.cspReportOnly {
			headerName = "Content-Security-Policy-Report-Only"
		}

		cspDirectives := []string{
			"default-src 'self'",
			"script-src 'self' 'unsafe-inline' 'unsafe-eval'",
			"style-src 'self' 'unsafe-inline'",
			"img-src 'self' data: blob:",
			"font-src 'self'",
			"connect-src 'self' wss: ws:",
			"frame-src 'self'",
			"object-src 'none'",
			"base-uri 'self'",
			"form-action 'self'",
		}

		w.Header().Set(headerName, strings.Join(cspDirectives, "; "))
	}

	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("X-Frame-Options", "DENY")
	w.Header().Set("X-XSS-Protection", "1; mode=block")
	w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
	w.Header().Set("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
}

type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

func (rw *responseWriter) Status() int {
	if rw.statusCode == 0 {
		return http.StatusOK
	}
	return rw.statusCode
}

func init() {
	core.RegisterMiddleware("SecurityMiddleware", func(next http.Handler) http.Handler {
		return NewSecurityMiddleware(next)
	})
}
