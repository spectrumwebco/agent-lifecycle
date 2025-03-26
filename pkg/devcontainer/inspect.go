package devcontainer

import (
	"context"

	"github.com/spectrumwebco/kled-beta/pkg/devcontainer/config"
	"github.com/spectrumwebco/kled-beta/pkg/driver"
	"github.com/spectrumwebco/kled-beta/pkg/image"
)

func (r *runner) inspectImage(ctx context.Context, imageName string) (*config.ImageDetails, error) {
	dockerDriver, ok := r.Driver.(driver.DockerDriver)
	if ok {
		return dockerDriver.InspectImage(ctx, imageName)
	}

	// fallback to just looking into the remote registry
	imageConfig, _, err := image.GetImageConfig(ctx, imageName, r.Log)
	if err != nil {
		return nil, err
	}

	return &config.ImageDetails{
		ID: imageName,
		Config: config.ImageDetailsConfig{
			User:       imageConfig.Config.User,
			Env:        imageConfig.Config.Env,
			Labels:     imageConfig.Config.Labels,
			Entrypoint: imageConfig.Config.Entrypoint,
			Cmd:        imageConfig.Config.Cmd,
		},
	}, nil
}

func (r *runner) getImageTag(ctx context.Context, imageID string) (string, error) {
	dockerDriver, ok := r.Driver.(driver.DockerDriver)
	if ok {
		return dockerDriver.GetImageTag(ctx, imageID)
	}

	return "", nil
}
