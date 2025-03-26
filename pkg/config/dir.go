package config

import (
	"os"
	"path/filepath"

	"github.com/loft-sh/devpod/pkg/util"
)

const KLED_HOME = "KLED_HOME"

// Override config path
const KLED_CONFIG = "KLED_CONFIG"

func GetConfigDir() (string, error) {
	homeDir := os.Getenv(KLED_HOME)
	if homeDir != "" {
		return homeDir, nil
	}

	homeDir, err := util.UserHomeDir()
	if err != nil {
		return "", err
	}

	configDir := filepath.Join(homeDir, ".kled")
	return configDir, nil
}

func GetConfigPath() (string, error) {
	configOrigin := os.Getenv(KLED_CONFIG)
	if configOrigin == "" {
		configDir, err := GetConfigDir()
		if err != nil {
			return "", err
		}

		return filepath.Join(configDir, ConfigFile), nil
	}

	return configOrigin, nil
}
