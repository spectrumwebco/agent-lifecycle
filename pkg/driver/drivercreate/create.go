package drivercreate

import (
	"fmt"

	"github.com/spectrumwebco/kled-beta/pkg/driver"
	"github.com/spectrumwebco/kled-beta/pkg/driver/custom"
	"github.com/spectrumwebco/kled-beta/pkg/driver/docker"
	"github.com/spectrumwebco/kled-beta/pkg/driver/kubernetes"
	provider2 "github.com/spectrumwebco/kled-beta/pkg/provider"
	"github.com/loft-sh/log"
)

func NewDriver(workspaceInfo *provider2.AgentWorkspaceInfo, log log.Logger) (driver.Driver, error) {
	driver := workspaceInfo.Agent.Driver
	if driver == "" || driver == provider2.DockerDriver {
		return docker.NewDockerDriver(workspaceInfo, log)
	} else if driver == provider2.CustomDriver {
		return custom.NewCustomDriver(workspaceInfo, log), nil
	} else if driver == provider2.KubernetesDriver {
		return kubernetes.NewKubernetesDriver(workspaceInfo, log)
	}

	return nil, fmt.Errorf("unrecognized driver '%s', possible values are %s, %s or %s",
		driver, provider2.DockerDriver, provider2.CustomDriver, provider2.KubernetesDriver)
}
