package platform

import (
	"encoding/json"
	"fmt"
	"io"
	"strings"

	"github.com/loft-sh/devpod/pkg/http"
	"github.com/loft-sh/devpod/pkg/provider"
)

type VersionObject struct {
	// Version is the server version
	Version string `json:"version,omitempty"`

	KledVersion string `json:"kledVersion,omitempty"`
}

func GetProInstanceKledVersion(proInstance *provider.ProInstance) (string, error) {
	url := "https://" + proInstance.Host
	return GetKledVersion(url)
}

func GetPlatformVersion(url string) (*VersionObject, error) {
	resp, err := http.GetHTTPClient().Get(url + "/version")
	if err != nil {
		return nil, fmt.Errorf("get %s: %w", url, err)
	} else if resp.StatusCode != 200 {
		out, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("get %s: %s (Status: %d)", url, string(out), resp.StatusCode)
	}

	versionRaw, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read %s: %w", url, err)
	}

	version := &VersionObject{}
	err = json.Unmarshal(versionRaw, version)
	if err != nil {
		return nil, fmt.Errorf("parse %s: %w", url, err)
	}

	return version, nil
}

func GetKledVersion(url string) (string, error) {
	version, err := GetPlatformVersion(url)
	if err != nil {
		return "", err
	}
	if version.KledVersion == "" {
		return "", fmt.Errorf("unexpected version '%s', please use --version to define a provider version", version.KledVersion)
	}

	// make sure it starts with a v
	if !strings.HasPrefix(version.KledVersion, "v") {
		version.KledVersion = "v" + version.KledVersion
	}

	return version.KledVersion, nil
}

func GetDevPodVersion(url string) (string, error) {
	return GetKledVersion(url)
}
