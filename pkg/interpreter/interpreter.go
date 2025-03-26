package interpreter

import (
	"fmt"
	"os"
	"runtime"
	"sync"
	"time"

	"github.com/spectrumwebco/kled/pkg/interpreter/api"
)

const (
	// DefaultAPIKey is the default API key for the Code Interpreter API
	DefaultAPIKey = "sk-lc-code01_6dU4jC9R8W0iuYEe6FE_efd3ebf0"
)

// InterpreterOptions holds configuration options for the interpreter
type InterpreterOptions struct {
	APIKey            string
	LocalExecution    bool
	GPUAcceleration   bool
	MemoryLimit       int64
	CPULimit          int
	WorkspaceID       string
	SpacetimeDBClient interface{} // Will be replaced with an actual client type
}

// Interpreter is the main interpreter service
type Interpreter struct {
	options    InterpreterOptions
	apiClient  *api.Client
	cache      map[string]*api.ExecutionResponse
	cacheMutex sync.RWMutex
}

// New creates a new interpreter with the given options
func New(options InterpreterOptions) *Interpreter {
	// Set default API key if not provided
	if options.APIKey == "" {
		options.APIKey = DefaultAPIKey
	}

	return &Interpreter{
		options:    options,
		apiClient:  api.NewClient(options.APIKey),
		cache:      make(map[string]*api.ExecutionResponse),
		cacheMutex: sync.RWMutex{},
	}
}

// ExecutionResult represents the result of a code execution
type ExecutionResult struct {
	ID          string
	Output      string
	Error       string
	Duration    time.Duration
	MemoryUsage int64
	CPUUsage    float64
}

// Execute executes the given code in the specified language
func (i *Interpreter) Execute(language, code string) (*ExecutionResult, error) {
	// Check cache first
	cacheKey := fmt.Sprintf("%s:%s", language, code)
	i.cacheMutex.RLock()
	cached, ok := i.cache[cacheKey]
	i.cacheMutex.RUnlock()

	if ok {
		return &ExecutionResult{
			ID:          cached.ID,
			Output:      cached.Result,
			Error:       cached.Error,
			Duration:    time.Duration(cached.Duration) * time.Millisecond,
			MemoryUsage: cached.MemoryUsage,
			CPUUsage:    cached.CPUUsage,
		}, nil
	}

	// Determine if we can execute locally
	if i.options.LocalExecution && canExecuteLocally(language) {
		return i.executeLocally(language, code)
	}

	// Fall back to API execution
	return i.executeAPI(language, code)
}

// canExecuteLocally checks if the given language can be executed locally
func canExecuteLocally(language string) bool {
	// For now, we'll just support a few languages locally
	// This can be expanded in the future
	switch language {
	case "go", "python", "javascript", "typescript":
		return true
	default:
		return false
	}
}

// executeLocally executes code locally (stub implementation)
func (i *Interpreter) executeLocally(language, code string) (*ExecutionResult, error) {
	// This is a placeholder for local execution
	// In a real implementation, we would use language-specific interpreters
	// or containers to execute the code

	// For now, we'll just return an error
	return nil, fmt.Errorf("local execution not yet implemented for %s", language)
}

// executeAPI executes code using the Code Interpreter API
func (i *Interpreter) executeAPI(language, code string) (*ExecutionResult, error) {
	startTime := time.Now()

	// Execute the code via the API
	resp, err := i.apiClient.Execute(language, code)
	if err != nil {
		return nil, fmt.Errorf("API execution failed: %w", err)
	}

	// Calculate execution duration if not provided by API
	if resp.Duration == 0 {
		resp.Duration = int64(time.Since(startTime) / time.Millisecond)
	}

	// Cache the result
	cacheKey := fmt.Sprintf("%s:%s", language, code)
	i.cacheMutex.Lock()
	i.cache[cacheKey] = resp
	i.cacheMutex.Unlock()

	// Record execution in SpacetimeDB if a workspace ID is provided
	if i.options.WorkspaceID != "" && i.options.SpacetimeDBClient != nil {
		go i.recordExecution(language, code, resp)
	}

	// Return the result
	return &ExecutionResult{
		ID:          resp.ID,
		Output:      resp.Result,
		Error:       resp.Error,
		Duration:    time.Duration(resp.Duration) * time.Millisecond,
		MemoryUsage: resp.MemoryUsage,
		CPUUsage:    resp.CPUUsage,
	}, nil
}

// recordExecution records an execution in SpacetimeDB (stub implementation)
func (i *Interpreter) recordExecution(language, code string, resp *api.ExecutionResponse) {
	// This is a placeholder for SpacetimeDB integration
	// In a real implementation, we would call into the SpacetimeDB client
	// to record the execution
	fmt.Fprintf(
		os.Stderr,
		"Recording execution to SpacetimeDB: workspace=%s, language=%s, code_length=%d\n",
		i.options.WorkspaceID,
		language,
		len(code),
	)
}

// GetSystemResources returns the system resources available to the interpreter
func GetSystemResources() map[string]interface{} {
	return map[string]interface{}{
		"cpuCount":        runtime.NumCPU(),
		"goVersion":       runtime.Version(),
		"operatingSystem": runtime.GOOS,
		"architecture":    runtime.GOARCH,
		"hasGPU":          hasGPU(),
	}
}

// hasGPU returns whether the system has a GPU available
func hasGPU() bool {
	// Check for Apple Silicon M2 GPU
	if runtime.GOOS == "darwin" && runtime.GOARCH == "arm64" {
		// On Apple Silicon, we can detect Metal support
		// For M2 specifically, we need to check the model identifier
		// This is a simplified implementation
		return true
	}

	// Check for CUDA libraries on other platforms
	// We look for NVIDIA drivers and CUDA toolkit
	// For macOS, check both Rosetta and native libraries
	if _, err := os.Stat("/usr/local/cuda/lib64/libcudart.so"); err == nil {
		return true
	}
	if _, err := os.Stat("/usr/local/cuda/lib/libcudart.dylib"); err == nil {
		return true
	}

	// For Windows
	if _, err := os.Stat("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA"); err == nil {
		return true
	}

	return false
}

// GetGPUInfo returns information about available GPUs
func GetGPUInfo() map[string]interface{} {
	gpuInfo := make(map[string]interface{})

	// Set default values
	gpuInfo["available"] = hasGPU()
	gpuInfo["count"] = 0
	gpuInfo["type"] = "none"

	// If GPU is available, try to get more info
	if hasGPU() {
		// On Apple Silicon M2
		if runtime.GOOS == "darwin" && runtime.GOARCH == "arm64" {
			gpuInfo["count"] = 1
			gpuInfo["type"] = "apple_silicon_m2"
			gpuInfo["memory"] = "16GB" // Simplified for now
			gpuInfo["cores"] = 4       // As requested
		} else {
			// For NVIDIA GPUs, we'd implement more detection
			// This is a placeholder for proper detection
			gpuInfo["count"] = 1
			gpuInfo["type"] = "cuda"
		}
	}

	return gpuInfo
}
