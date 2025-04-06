package kata

import (
	"bufio"
	"bytes"
	"context"
	"fmt"
	"io"
	"os"
	"os/exec"
	"os/user"
	"regexp"
	"runtime"
	"slices"
	"strconv"
	"strings"

	"github.com/loft-sh/devpod/pkg/compose"
	config2 "github.com/loft-sh/devpod/pkg/config"
	"github.com/loft-sh/devpod/pkg/devcontainer/config"
	"github.com/loft-sh/devpod/pkg/driver"
	"github.com/loft-sh/devpod/pkg/ide/jetbrains"
	provider2 "github.com/loft-sh/devpod/pkg/provider"
	"github.com/loft-sh/log"
	"github.com/pkg/errors"
	"github.com/sirupsen/logrus"
)

func makeEnvironment(env map[string]string, log log.Logger) []string {
	if env == nil {
		return nil
	}

	ret := config.ObjectToList(env)
	if len(env) > 0 {
		log.Debugf("Use kata environment variables: %v", ret)
	}

	return ret
}

func NewKataDriver(workspaceInfo *provider2.AgentWorkspaceInfo, log log.Logger) (driver.Driver, error) {
	kataCommand := "kata-runtime"
	if workspaceInfo.Agent.Kata.Path != "" {
		kataCommand = workspaceInfo.Agent.Kata.Path
	}

	containerdCommand := "containerd"
	if workspaceInfo.Agent.Kata.ContainerdPath != "" {
		containerdCommand = workspaceInfo.Agent.Kata.ContainerdPath
	}

	log.Debugf("Using kata command '%s' and containerd command '%s'", kataCommand, containerdCommand)
	return &kataDriver{
		KataCommand:      kataCommand,
		ContainerdCommand: containerdCommand,
		ContainerID:      workspaceInfo.Workspace.Source.Container,
		Log:              log,
	}, nil
}

type kataDriver struct {
	KataCommand      string
	ContainerdCommand string
	ContainerID      string
	Compose          *compose.ComposeHelper

	Log log.Logger
}

func (d *kataDriver) TargetArchitecture(ctx context.Context, workspaceId string) (string, error) {
	return runtime.GOARCH, nil
}

func (d *kataDriver) CommandDevContainer(ctx context.Context, workspaceId, user, command string, stdin io.Reader, stdout io.Writer, stderr io.Writer) error {
	container, err := d.FindDevContainer(ctx, workspaceId)
	if err != nil {
		return err
	} else if container == nil {
		return fmt.Errorf("container not found")
	}

	args := []string{"exec"}
	if stdin != nil {
		args = append(args, "-i")
	}
	args = append(args, "-u", user, container.ID, "sh", "-c", command)
	return d.runContainerdCommand(ctx, args, stdin, stdout, stderr)
}

func (d *kataDriver) PushDevContainer(ctx context.Context, image string) error {
	writer := d.Log.Writer(logrus.InfoLevel, false)
	defer writer.Close()

	args := []string{
		"push",
		image,
	}

	d.Log.Debugf("Running containerd command: %s %s", d.ContainerdCommand, strings.Join(args, " "))
	err := d.runContainerdCommand(ctx, args, nil, writer, writer)
	if err != nil {
		return errors.Wrap(err, "push image")
	}

	return nil
}

func (d *kataDriver) TagDevContainer(ctx context.Context, image, tag string) error {
	writer := d.Log.Writer(logrus.InfoLevel, false)
	defer writer.Close()

	args := []string{
		"tag",
		image,
		tag,
	}

	d.Log.Debugf("Running containerd command: %s %s", d.ContainerdCommand, strings.Join(args, " "))
	err := d.runContainerdCommand(ctx, args, nil, writer, writer)
	if err != nil {
		return errors.Wrap(err, "tag image")
	}

	return nil
}

func (d *kataDriver) DeleteDevContainer(ctx context.Context, workspaceId string) error {
	container, err := d.FindDevContainer(ctx, workspaceId)
	if err != nil {
		return err
	} else if container == nil {
		return nil
	}

	args := []string{"rm", "-f", container.ID}
	return d.runContainerdCommand(ctx, args, nil, nil, nil)
}

func (d *kataDriver) StartDevContainer(ctx context.Context, workspaceId string) error {
	container, err := d.FindDevContainer(ctx, workspaceId)
	if err != nil {
		return err
	} else if container == nil {
		return fmt.Errorf("container not found")
	}

	args := []string{"start", container.ID}
	return d.runContainerdCommand(ctx, args, nil, nil, nil)
}

func (d *kataDriver) StopDevContainer(ctx context.Context, workspaceId string) error {
	container, err := d.FindDevContainer(ctx, workspaceId)
	if err != nil {
		return err
	} else if container == nil {
		return fmt.Errorf("container not found")
	}

	args := []string{"stop", container.ID}
	return d.runContainerdCommand(ctx, args, nil, nil, nil)
}

func (d *kataDriver) InspectImage(ctx context.Context, imageName string) (*config.ImageDetails, error) {
	args := []string{"inspect", imageName}
	var stdout bytes.Buffer
	var stderr bytes.Buffer
	err := d.runContainerdCommand(ctx, args, nil, &stdout, &stderr)
	if err != nil {
		return nil, err
	}

	imageDetails := &config.ImageDetails{}
	return imageDetails, nil
}

func (d *kataDriver) GetImageTag(ctx context.Context, imageID string) (string, error) {
	args := []string{"images", "--format", "{{.Repository}}:{{.Tag}}", imageID}
	var stdout bytes.Buffer
	err := d.runContainerdCommand(ctx, args, nil, &stdout, nil)
	if err != nil {
		return "", err
	}

	return strings.TrimSpace(stdout.String()), nil
}

func (d *kataDriver) ComposeHelper() (*compose.ComposeHelper, error) {
	if d.Compose != nil {
		return d.Compose, nil
	}

	var err error
	d.Compose, err = compose.NewComposeHelper("docker-compose", nil)
	return d.Compose, err
}

func (d *kataDriver) FindDevContainer(ctx context.Context, workspaceId string) (*config.ContainerDetails, error) {
	var containerDetails *config.ContainerDetails
	var err error
	
	if d.ContainerID != "" {
		args := []string{"inspect", d.ContainerID}
		var stdout bytes.Buffer
		err = d.runContainerdCommand(ctx, args, nil, &stdout, nil)
		if err != nil {
			return nil, err
		}
		
		containerDetails = &config.ContainerDetails{
			ID: d.ContainerID,
			Config: &config.ContainerConfig{},
		}
	} else {
		args := []string{"ps", "-a", "--filter", "label=" + config.DockerIDLabel + "=" + workspaceId, "--format", "{{.ID}}"}
		var stdout bytes.Buffer
		err = d.runContainerdCommand(ctx, args, nil, &stdout, nil)
		if err != nil {
			return nil, err
		}
		
		containerID := strings.TrimSpace(stdout.String())
		if containerID == "" {
			return nil, nil
		}
		
		args = []string{"inspect", containerID}
		stdout.Reset()
		err = d.runContainerdCommand(ctx, args, nil, &stdout, nil)
		if err != nil {
			return nil, err
		}
		
		containerDetails = &config.ContainerDetails{
			ID: containerID,
			Config: &config.ContainerConfig{},
		}
	}

	return containerDetails, nil
}

func (d *kataDriver) RunDevContainer(
	ctx context.Context,
	workspaceId string,
	options *driver.RunOptions,
) error {
	return fmt.Errorf("unsupported")
}

func (d *kataDriver) RunKataDevContainer(
	ctx context.Context,
	workspaceId string,
	options *driver.RunOptions,
	parsedConfig *config.DevContainerConfig,
	init *bool,
	ide string,
	ideOptions map[string]config2.OptionValue,
) error {
	err := d.EnsureImage(ctx, options)
	if err != nil {
		return err
	}

	args := []string{"run"}
	args = append(args, "--runtime=kata-runtime")

	for _, appPort := range parsedConfig.AppPort {
		intPort, err := strconv.Atoi(appPort)
		if err != nil {
			args = append(args, "-p", appPort)
		} else {
			args = append(args, "-p", fmt.Sprintf("127.0.0.1:%d:%d", intPort, intPort))
		}
	}

	if options.WorkspaceMount != nil {
		workspacePath := d.EnsurePath(options.WorkspaceMount)
		mountPath := workspacePath.String()
		args = append(args, "--mount", mountPath)
	}

	if options.User != "" {
		args = append(args, "-u", options.User)
	}

	for k, v := range options.Env {
		args = append(args, "-e", k+"="+v)
	}

	if options.Privileged != nil && *options.Privileged {
		args = append(args, "--privileged")
	}

	for _, capAdd := range options.CapAdd {
		args = append(args, "--cap-add", capAdd)
	}
	for _, securityOpt := range options.SecurityOpt {
		args = append(args, "--security-opt", securityOpt)
	}

	for _, mount := range options.Mounts {
		args = append(args, "--mount", mount.String())
	}

	switch ide {
	case string(config2.IDEGoland):
		args = append(args, "--mount", jetbrains.NewGolandServer("", ideOptions, d.Log).GetVolume())
	case string(config2.IDERustRover):
		args = append(args, "--mount", jetbrains.NewRustRoverServer("", ideOptions, d.Log).GetVolume())
	case string(config2.IDEPyCharm):
		args = append(args, "--mount", jetbrains.NewPyCharmServer("", ideOptions, d.Log).GetVolume())
	case string(config2.IDEPhpStorm):
		args = append(args, "--mount", jetbrains.NewPhpStorm("", ideOptions, d.Log).GetVolume())
	case string(config2.IDEIntellij):
		args = append(args, "--mount", jetbrains.NewIntellij("", ideOptions, d.Log).GetVolume())
	case string(config2.IDECLion):
		args = append(args, "--mount", jetbrains.NewCLionServer("", ideOptions, d.Log).GetVolume())
	case string(config2.IDERider):
		args = append(args, "--mount", jetbrains.NewRiderServer("", ideOptions, d.Log).GetVolume())
	case string(config2.IDERubyMine):
		args = append(args, "--mount", jetbrains.NewRubyMineServer("", ideOptions, d.Log).GetVolume())
	case string(config2.IDEWebStorm):
		args = append(args, "--mount", jetbrains.NewWebStormServer("", ideOptions, d.Log).GetVolume())
	case string(config2.IDEDataSpell):
		args = append(args, "--mount", jetbrains.NewDataSpellServer("", ideOptions, d.Log).GetVolume())
	}

	labels := append(config.GetDockerLabelForID(workspaceId), options.Labels...)
	for _, label := range labels {
		args = append(args, "-l", label)
	}

	if parsedConfig.HostRequirements != nil && parsedConfig.HostRequirements.GPU == "true" {
		args = append(args, "--gpus", "all")
	}

	args = append(args, parsedConfig.RunArgs...)

	args = append(args, "-d")

	if options.Entrypoint != "" {
		args = append(args, "--entrypoint", options.Entrypoint)
	}

	args = append(args, options.Image)

	args = append(args, options.Cmd...)

	d.Log.Debugf("Running containerd command: %s %s", d.ContainerdCommand, strings.Join(args, " "))
	writer := d.Log.Writer(logrus.InfoLevel, false)
	defer writer.Close()

	err = d.runContainerdCommand(ctx, args, nil, writer, writer)
	if err != nil {
		return err
	}

	return nil
}

func (d *kataDriver) EnsureImage(ctx context.Context, options *driver.RunOptions) error {
	if options.Image == "" {
		return fmt.Errorf("image is empty")
	}

	args := []string{"images", "--format", "{{.Repository}}:{{.Tag}}", options.Image}
	var stdout bytes.Buffer
	err := d.runContainerdCommand(ctx, args, nil, &stdout, nil)
	if err != nil {
		return err
	}

	if strings.TrimSpace(stdout.String()) == "" {
		args = []string{"pull", options.Image}
		writer := d.Log.Writer(logrus.InfoLevel, false)
		defer writer.Close()
		
		d.Log.Infof("Pulling image %s...", options.Image)
		err = d.runContainerdCommand(ctx, args, nil, writer, writer)
		if err != nil {
			return errors.Wrap(err, "pull image")
		}
	}

	return nil
}

func (d *kataDriver) EnsurePath(mount *driver.Mount) *driver.Mount {
	if mount == nil {
		return nil
	}

	return mount
}

func (d *kataDriver) GetDevContainerLogs(ctx context.Context, workspaceId string, stdout io.Writer, stderr io.Writer) error {
	container, err := d.FindDevContainer(ctx, workspaceId)
	if err != nil {
		return err
	} else if container == nil {
		return fmt.Errorf("container not found")
	}

	args := []string{"logs", container.ID}
	return d.runContainerdCommand(ctx, args, nil, stdout, stderr)
}

func (d *kataDriver) runContainerdCommand(ctx context.Context, args []string, stdin io.Reader, stdout io.Writer, stderr io.Writer) error {
	cmd := exec.CommandContext(ctx, d.ContainerdCommand, args...)
	cmd.Stdin = stdin
	cmd.Stdout = stdout
	cmd.Stderr = stderr
	return cmd.Run()
}
