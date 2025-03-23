package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

const (
	// DefaultAPIURL is the base URL for the Code Interpreter API
	DefaultAPIURL = "https://api.librechat.ai/v1"

	// DefaultTimeout is the default timeout for API requests
	DefaultTimeout = 30 * time.Second
)

// ClientConfig holds the configuration for the API client
type ClientConfig struct {
	APIKey     string
	BaseURL    string
	Timeout    time.Duration
	MaxRetries int
}

// Client is the API client for the Code Interpreter API
type Client struct {
	config     ClientConfig
	httpClient *http.Client
}

// NewClient creates a new API client with the given API key
func NewClient(apiKey string) *Client {
	return &Client{
		config: ClientConfig{
			APIKey:     apiKey,
			BaseURL:    DefaultAPIURL,
			Timeout:    DefaultTimeout,
			MaxRetries: 3,
		},
		httpClient: &http.Client{
			Timeout: DefaultTimeout,
		},
	}
}

// WithConfig creates a new API client with the given configuration
func WithConfig(config ClientConfig) *Client {
	if config.BaseURL == "" {
		config.BaseURL = DefaultAPIURL
	}
	if config.Timeout == 0 {
		config.Timeout = DefaultTimeout
	}
	if config.MaxRetries == 0 {
		config.MaxRetries = 3
	}

	return &Client{
		config: config,
		httpClient: &http.Client{
			Timeout: config.Timeout,
		},
	}
}

// Request represents an API request
type Request struct {
	Method  string
	Path    string
	Body    interface{}
	Headers map[string]string
}

// ExecutionRequest represents a code execution request
type ExecutionRequest struct {
	Language string `json:"language"`
	Code     string `json:"code"`
}

// ExecutionResponse represents a code execution response
type ExecutionResponse struct {
	ID          string  `json:"id"`
	Language    string  `json:"language"`
	Code        string  `json:"code"`
	Status      string  `json:"status"`
	Result      string  `json:"result,omitempty"`
	Error       string  `json:"error,omitempty"`
	StartTime   string  `json:"startTime"`
	EndTime     string  `json:"endTime"`
	Duration    int     `json:"duration"`
	MemoryUsage int64   `json:"memoryUsage,omitempty"`
	CPUUsage    float64 `json:"cpuUsage,omitempty"`
}

// ErrorResponse represents an API error response
type ErrorResponse struct {
	Error struct {
		Type    string `json:"type"`
		Message string `json:"message"`
		Code    string `json:"code,omitempty"`
	} `json:"error"`
}

// Execute executes a code snippet with the Code Interpreter API
func (c *Client) Execute(language, code string) (*ExecutionResponse, error) {
	req := ExecutionRequest{
		Language: language,
		Code:     code,
	}

	var resp ExecutionResponse
	err := c.sendRequest(Request{
		Method: http.MethodPost,
		Path:   "/execute",
		Body:   req,
	}, &resp)

	return &resp, err
}

// sendRequest sends an API request and decodes the response
func (c *Client) sendRequest(req Request, v interface{}) error {
	var err error
	var resp *http.Response

	// Prepare the request
	var reqBody io.Reader
	if req.Body != nil {
		reqBodyBytes, err := json.Marshal(req.Body)
		if err != nil {
			return fmt.Errorf("failed to marshal request body: %w", err)
		}
		reqBody = bytes.NewBuffer(reqBodyBytes)
	}

	// Build the URL
	url := fmt.Sprintf("%s%s", c.config.BaseURL, req.Path)

	// Create the HTTP request
	httpReq, err := http.NewRequest(req.Method, url, reqBody)
	if err != nil {
		return fmt.Errorf("failed to create HTTP request: %w", err)
	}

	// Set headers
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.config.APIKey))
	for k, v := range req.Headers {
		httpReq.Header.Set(k, v)
	}

	// Make the request with retries
	retries := 0
	for {
		resp, err = c.httpClient.Do(httpReq)
		if err == nil {
			break
		}

		retries++
		if retries >= c.config.MaxRetries {
			return fmt.Errorf("failed to send request after %d retries: %w", c.config.MaxRetries, err)
		}

		// Exponential backoff
		time.Sleep(time.Duration(retries*retries) * 100 * time.Millisecond)
	}
	defer resp.Body.Close()

	// Read the response body
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read response body: %w", err)
	}

	// Check for API errors
	if resp.StatusCode != http.StatusOK {
		var errResp ErrorResponse
		if err := json.Unmarshal(respBody, &errResp); err == nil {
			return fmt.Errorf("API error: %s - %s", errResp.Error.Type, errResp.Error.Message)
		}
		return fmt.Errorf("API error: status code %d", resp.StatusCode)
	}

	// Decode the response
	if v != nil {
		if err := json.Unmarshal(respBody, v); err != nil {
			return fmt.Errorf("failed to unmarshal response: %w", err)
		}
	}

	return nil
}
