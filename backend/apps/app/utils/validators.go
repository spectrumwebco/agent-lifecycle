package utils

import (
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type ValidationError struct {
	Message string
	Params  map[string]interface{}
}

func (e ValidationError) Error() string {
	if len(e.Params) == 0 {
		return e.Message
	}

	msg := e.Message
	for key, value := range e.Params {
		placeholder := fmt.Sprintf("%%(%s)s", key)
		msg = strings.Replace(msg, placeholder, fmt.Sprintf("%v", value), -1)
	}
	return msg
}

func ValidateJSON(value string) error {
	var js interface{}
	if err := json.Unmarshal([]byte(value), &js); err != nil {
		return &ValidationError{Message: "Invalid JSON format."}
	}
	return nil
}

func ValidateJSONSchema(value string, schema map[string]interface{}) error {
	var data interface{}
	if err := json.Unmarshal([]byte(value), &data); err != nil {
		return &ValidationError{Message: "Invalid JSON format."}
	}

	if core.PythonModuleExists("jsonschema") {
		err := core.CallPythonFunction("jsonschema", "validate", []interface{}{data, schema})
		if err != nil {
			return &ValidationError{
				Message: "JSON does not conform to schema: %(error)s",
				Params:  map[string]interface{}{"error": err.Error()},
			}
		}
	}

	return nil
}

func ValidateHostname(value string) error {
	hostnamePattern := `^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$`
	matched, _ := regexp.MatchString(hostnamePattern, value)
	if !matched {
		return &ValidationError{Message: "Invalid hostname format."}
	}
	return nil
}

func ValidateURL(value string) error {
	parsedURL, err := url.Parse(value)
	if err != nil || parsedURL.Scheme == "" || parsedURL.Host == "" {
		return &ValidationError{Message: "Invalid URL format."}
	}
	return nil
}

func ValidateAPIKey(value string) error {
	if len(value) < 32 {
		return &ValidationError{Message: "API key is too short. It should be at least 32 characters."}
	}

	matched, _ := regexp.MatchString(`^[a-zA-Z0-9_\-]+$`, value)
	if !matched {
		return &ValidationError{Message: "API key contains invalid characters."}
	}
	return nil
}

func ValidateEmailList(value string) error {
	if value == "" {
		return nil
	}

	emailPattern := `^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$`
	emails := strings.Split(value, ",")

	for _, email := range emails {
		email = strings.TrimSpace(email)
		matched, _ := regexp.MatchString(emailPattern, email)
		if !matched {
			return &ValidationError{
				Message: "Invalid email address: %(email)s",
				Params:  map[string]interface{}{"email": email},
			}
		}
	}
	return nil
}

func ValidateCronExpression(value string) error {
	parts := strings.Fields(value)

	if len(parts) != 5 {
		return &ValidationError{Message: "Cron expression must have 5 parts."}
	}

	if parts[0] != "*" {
		for _, x := range strings.Split(parts[0], ",") {
			num, err := strconv.Atoi(x)
			if err != nil || num < 0 || num > 59 {
				return &ValidationError{Message: "Invalid minutes in cron expression."}
			}
		}
	}

	if parts[1] != "*" {
		for _, x := range strings.Split(parts[1], ",") {
			num, err := strconv.Atoi(x)
			if err != nil || num < 0 || num > 23 {
				return &ValidationError{Message: "Invalid hours in cron expression."}
			}
		}
	}

	if parts[2] != "*" {
		for _, x := range strings.Split(parts[2], ",") {
			num, err := strconv.Atoi(x)
			if err != nil || num < 1 || num > 31 {
				return &ValidationError{Message: "Invalid day of month in cron expression."}
			}
		}
	}

	if parts[3] != "*" {
		for _, x := range strings.Split(parts[3], ",") {
			num, err := strconv.Atoi(x)
			if err != nil || num < 1 || num > 12 {
				return &ValidationError{Message: "Invalid month in cron expression."}
			}
		}
	}

	if parts[4] != "*" {
		for _, x := range strings.Split(parts[4], ",") {
			num, err := strconv.Atoi(x)
			if err != nil || num < 0 || num > 6 {
				return &ValidationError{Message: "Invalid day of week in cron expression."}
			}
		}
	}

	return nil
}

func ValidateHexColor(value string) error {
	matched, _ := regexp.MatchString(`^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$`, value)
	if !matched {
		return &ValidationError{Message: "Invalid hex color code. Use format #RRGGBB or #RGB."}
	}
	return nil
}

func ValidateSemanticVersion(value string) error {
	semverPattern := `^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$`
	matched, _ := regexp.MatchString(semverPattern, value)
	if !matched {
		return &ValidationError{Message: "Invalid semantic version. Use format X.Y.Z."}
	}
	return nil
}

func ValidateFileExtension(value interface{}, allowedExtensions []string) error {
	var filename string

	switch v := value.(type) {
	case string:
		filename = v
	case core.File:
		filename = v.Name()
	default:
		filename = fmt.Sprintf("%v", value)
	}

	ext := strings.ToLower(filepath.Ext(filename))
	
	for _, allowed := range allowedExtensions {
		if ext == allowed {
			return nil
		}
	}

	return &ValidationError{
		Message: "Unsupported file extension. Allowed extensions: %(extensions)s",
		Params:  map[string]interface{}{"extensions": strings.Join(allowedExtensions, ", ")},
	}
}

func ValidateFileSize(value interface{}, maxSizeMB int) error {
	maxSizeBytes := int64(maxSizeMB) * 1024 * 1024
	
	var size int64
	
	switch v := value.(type) {
	case core.File:
		size = v.Size()
	case string:
		info, err := os.Stat(v)
		if err != nil {
			return err
		}
		size = info.Size()
	default:
		return fmt.Errorf("unsupported value type for file size validation")
	}
	
	if size > maxSizeBytes {
		return &ValidationError{
			Message: "File too large. Maximum size is %(max_size)s MB.",
			Params:  map[string]interface{}{"max_size": maxSizeMB},
		}
	}
	
	return nil
}
