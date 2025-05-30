package clientimplementation

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/gofrs/flock"
	"github.com/loft-sh/api/v4/pkg/devpod"
	"github.com/loft-sh/devpod/pkg/client"
	"github.com/loft-sh/devpod/pkg/config"
	kledlog "github.com/loft-sh/devpod/pkg/log"
	"github.com/loft-sh/devpod/pkg/options"
	"github.com/loft-sh/devpod/pkg/provider"
	"github.com/loft-sh/log"
	perrors "github.com/pkg/errors"
)

var (
	KledDebug = "KLED_DEBUG"

	KledPlatformOptions = "KLED_PLATFORM_OPTIONS"

	KledFlagsUp     = "KLED_FLAGS_UP"
	KledFlagsSsh    = "KLED_FLAGS_SSH"
	KledFlagsDelete = "KLED_FLAGS_DELETE"
	KledFlagsStatus = "KLED_FLAGS_STATUS"
)

func NewProxyClient(kledConfig *config.Config, prov *provider.ProviderConfig, workspace *provider.Workspace, log log.Logger) (client.ProxyClient, error) {
	return &proxyClient{
		kledConfig: kledConfig,
		config:       prov,
		workspace:    workspace,
		log:          log,
	}, nil
}

type proxyClient struct {
	m sync.Mutex

	workspaceLockOnce sync.Once
	workspaceLock     *flock.Flock

	kledConfig *config.Config
	config       *provider.ProviderConfig
	workspace    *provider.Workspace
	log          log.Logger
}

func (s *proxyClient) Lock(ctx context.Context) error {
	s.initLock()

	// try to lock workspace
	s.log.Debugf("Acquire workspace lock...")
	err := tryLock(ctx, s.workspaceLock, "workspace", s.log)
	if err != nil {
		return fmt.Errorf("error locking workspace: %w", err)
	}
	s.log.Debugf("Acquired workspace lock...")

	return nil
}

func (s *proxyClient) Unlock() {
	s.initLock()

	// try to unlock workspace
	err := s.workspaceLock.Unlock()
	if err != nil {
		s.log.Warnf("Error unlocking workspace: %v", err)
	}
}

func tryLock(ctx context.Context, lock *flock.Flock, name string, log log.Logger) error {
	done := printLogMessagePeriodically(fmt.Sprintf("Trying to lock %s, seems like another process is running that blocks this %s", name, name), log)
	defer close(done)

	now := time.Now()
	for time.Since(now) < time.Minute*5 {
		locked, err := lock.TryLock()
		if err != nil {
			return err
		} else if locked {
			return nil
		}

		select {
		case <-time.After(time.Second):
			continue
		case <-ctx.Done():
			return ctx.Err()
		}
	}

	return fmt.Errorf("timed out waiting to lock %s, seems like there is another process running on this machine that blocks it", name)
}

func (s *proxyClient) initLock() {
	s.workspaceLockOnce.Do(func() {
		s.m.Lock()
		defer s.m.Unlock()

		// get locks dir
		workspaceLocksDir, err := provider.GetLocksDir(s.workspace.Context)
		if err != nil {
			panic(fmt.Errorf("get workspaces dir: %w", err))
		}
		_ = os.MkdirAll(workspaceLocksDir, 0777)

		// create workspace lock
		s.workspaceLock = flock.New(filepath.Join(workspaceLocksDir, s.workspace.ID+".workspace.lock"))
	})
}

func (s *proxyClient) Provider() string {
	return s.config.Name
}

func (s *proxyClient) Workspace() string {
	s.m.Lock()
	defer s.m.Unlock()

	return s.workspace.ID
}

func (s *proxyClient) WorkspaceConfig() *provider.Workspace {
	s.m.Lock()
	defer s.m.Unlock()

	return provider.CloneWorkspace(s.workspace)
}

func (s *proxyClient) Context() string {
	return s.workspace.Context
}

func (s *proxyClient) RefreshOptions(ctx context.Context, userOptionsRaw []string, reconfigure bool) error {
	s.m.Lock()
	defer s.m.Unlock()

	userOptions, err := provider.ParseOptions(userOptionsRaw)
	if err != nil {
		return perrors.Wrap(err, "parse options")
	}

	workspace, err := options.ResolveAndSaveOptionsProxy(ctx, s.kledConfig, s.config, s.workspace, userOptions, s.log)
	if err != nil {
		return err
	}

	if reconfigure {
		err := s.updateInstance(ctx)
		if err != nil {
			return err
		}
	}

	s.workspace = workspace
	return nil
}

func (s *proxyClient) Create(ctx context.Context, stdin io.Reader, stdout io.Writer, stderr io.Writer) error {
	err := RunCommandWithBinaries(
		ctx,
		"createWorkspace",
		s.config.Exec.Proxy.Create.Workspace,
		s.workspace.Context,
		s.workspace,
		nil,
		s.kledConfig.ProviderOptions(s.config.Name),
		s.config,
		nil,
		stdin,
		stdout,
		stderr,
		s.log)
	if err != nil {
		return fmt.Errorf("create remote workspace : %w", err)
	}

	return nil
}

func (s *proxyClient) Up(ctx context.Context, opt client.UpOptions) error {
	writer, _ := kledlog.PipeJSONStream(s.log.ErrorStreamOnly())
	defer writer.Close()

	opts := EncodeOptions(opt.CLIOptions, KledFlagsUp)
	if opt.Debug {
		opts["DEBUG"] = "true"
	}

	err := RunCommandWithBinaries(
		ctx,
		"up",
		s.config.Exec.Proxy.Up,
		s.workspace.Context,
		s.workspace,
		nil,
		s.kledConfig.ProviderOptions(s.config.Name),
		s.config,
		opts,
		opt.Stdin,
		opt.Stdout,
		writer,
		s.log.ErrorStreamOnly(),
	)
	if err != nil {
		return fmt.Errorf("error running kled up: %w", err)
	}

	return nil
}

func (s *proxyClient) Ssh(ctx context.Context, opt client.SshOptions) error {
	writer, _ := kledlog.PipeJSONStream(s.log.ErrorStreamOnly())
	defer writer.Close()

	err := RunCommandWithBinaries(
		ctx,
		"ssh",
		s.config.Exec.Proxy.Ssh,
		s.workspace.Context,
		s.workspace,
		nil,
		s.kledConfig.ProviderOptions(s.config.Name),
		s.config,
		EncodeOptions(opt, KledFlagsSsh),
		opt.Stdin,
		opt.Stdout,
		writer,
		s.log.ErrorStreamOnly(),
	)
	if err != nil {
		return err
	}

	return nil
}

func (s *proxyClient) Delete(ctx context.Context, opt client.DeleteOptions) error {
	s.m.Lock()
	defer s.m.Unlock()

	writer, _ := kledlog.PipeJSONStream(s.log.ErrorStreamOnly())
	defer writer.Close()

	var gracePeriod *time.Duration
	if opt.GracePeriod != "" {
		duration, err := time.ParseDuration(opt.GracePeriod)
		if err == nil {
			gracePeriod = &duration
		}
	}

	// kill the command after the grace period
	if gracePeriod != nil {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, *gracePeriod)
		defer cancel()
	}

	err := RunCommandWithBinaries(
		ctx,
		"delete",
		s.config.Exec.Proxy.Delete,
		s.workspace.Context,
		s.workspace,
		nil,
		s.kledConfig.ProviderOptions(s.config.Name),
		s.config,
		EncodeOptions(opt, KledFlagsDelete),
		nil,
		writer,
		writer,
		s.log,
	)
	if err != nil {
		if !opt.Force {
			return fmt.Errorf("error deleting workspace: %w", err)
		}

		s.log.Errorf("Error deleting workspace: %v", err)
	}

	return DeleteWorkspaceFolder(s.workspace.Context, s.workspace.ID, s.workspace.SSHConfigPath, s.log)
}

func (s *proxyClient) Stop(ctx context.Context, opt client.StopOptions) error {
	s.m.Lock()
	defer s.m.Unlock()

	writer, _ := kledlog.PipeJSONStream(s.log.ErrorStreamOnly())
	defer writer.Close()

	err := RunCommandWithBinaries(
		ctx,
		"stop",
		s.config.Exec.Proxy.Stop,
		s.workspace.Context,
		s.workspace,
		nil,
		s.kledConfig.ProviderOptions(s.config.Name),
		s.config,
		nil,
		nil,
		writer,
		writer,
		s.log,
	)
	if err != nil {
		return fmt.Errorf("error stopping container: %w", err)
	}

	return nil
}

func (s *proxyClient) Status(ctx context.Context, options client.StatusOptions) (client.Status, error) {
	s.m.Lock()
	defer s.m.Unlock()

	stdout := &bytes.Buffer{}
	buf := &bytes.Buffer{}
	err := RunCommandWithBinaries(
		ctx,
		"status",
		s.config.Exec.Proxy.Status,
		s.workspace.Context,
		s.workspace,
		nil,
		s.kledConfig.ProviderOptions(s.config.Name),
		s.config,
		EncodeOptions(options, KledFlagsStatus),
		nil,
		io.MultiWriter(stdout, buf),
		buf,
		s.log.ErrorStreamOnly(),
	)
	if err != nil {
		return client.StatusNotFound, fmt.Errorf("error retrieving container status: %s%w", buf.String(), err)
	}

	kledlog.ReadJSONStream(bytes.NewReader(buf.Bytes()), s.log.ErrorStreamOnly())
	status := &client.WorkspaceStatus{}
	err = json.Unmarshal(stdout.Bytes(), status)
	if err != nil {
		return client.StatusNotFound, fmt.Errorf("error parsing proxy command response: %s%w", stdout.String(), err)
	}

	// parse status
	return client.ParseStatus(status.State)
}

func (s *proxyClient) updateInstance(ctx context.Context) error {
	err := RunCommandWithBinaries(
		ctx,
		"updateWorkspace",
		s.config.Exec.Proxy.Update.Workspace,
		s.workspace.Context,
		s.workspace,
		nil,
		s.kledConfig.ProviderOptions(s.config.Name),
		s.config,
		nil,
		os.Stdin,
		os.Stdout,
		os.Stderr,
		s.log.ErrorStreamOnly(),
	)
	if err != nil {
		return err
	}

	return nil
}

func EncodeOptions(options any, name string) map[string]string {
	raw, _ := json.Marshal(options)
	return map[string]string{
		name: string(raw),
	}
}

func DecodeOptionsFromEnv(name string, into any) (bool, error) {
	raw := os.Getenv(name)
	if raw == "" {
		return false, nil
	}

	return true, json.Unmarshal([]byte(raw), into)
}

func DecodePlatformOptionsFromEnv(into *devpod.PlatformOptions) error {
	raw := os.Getenv(KledPlatformOptions)
	if raw == "" {
		return nil
	}

	return json.Unmarshal([]byte(raw), into)
}
