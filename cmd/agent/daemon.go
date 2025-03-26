package agent

import (
	"bytes"
	"context"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/loft-sh/devpod/pkg/agent"
	"github.com/loft-sh/devpod/pkg/client/clientimplementation"
	"github.com/loft-sh/devpod/pkg/driver/custom"
	provider2 "github.com/loft-sh/devpod/pkg/provider"
	"github.com/loft-sh/log"
	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

// DaemonCmd holds the cmd flags
type DaemonCmd struct {
	*flags.GlobalFlags

	Interval string
}

// NewDaemonCmd creates a new command
func NewDaemonCmd(flags *flags.GlobalFlags) *cobra.Command {
	cmd := &DaemonCmd{
		GlobalFlags: flags,
	}
	daemonCmd := &cobra.Command{
		Use:   "daemon",
		Short: "Watches for activity and stops the server due to inactivity",
		Args:  cobra.NoArgs,
		RunE: func(_ *cobra.Command, _ []string) error {
			return cmd.Run(context.Background())
		},
	}
	daemonCmd.Flags().StringVar(&cmd.Interval, "interval", "", "The interval how to poll workspaces")
	return daemonCmd
}

func (cmd *DaemonCmd) Run(ctx context.Context) error {
	logFolder, err := agent.GetAgentDaemonLogFolder(cmd.AgentDir)
	if err != nil {
		return err
	}

	logger := log.NewFileLogger(filepath.Join(logFolder, "agent-daemon.log"), logrus.InfoLevel)
	logger.Infof("Starting Kled Daemon patrol at %s...", logFolder)

	// start patrolling
	cmd.patrol(logger)

	// should never reach this
	return nil
}

func (cmd *DaemonCmd) patrol(log log.Logger) {
	// make sure we don't immediately resleep on startup
	cmd.initialTouch(log)

	// parse the daemon interval
	interval := time.Second * 60
	if cmd.Interval != "" {
		parsed, err := time.ParseDuration(cmd.Interval)
		if err == nil {
			interval = parsed
		}
	}

	// loop over workspace configs and check their last ModTime
	for {
		time.Sleep(interval)
		cmd.doOnce(log)
	}
}

func (cmd *DaemonCmd) doOnce(log log.Logger) {
	var latestActivity *time.Time
	var workspace *provider2.AgentWorkspaceInfo

	// get base folder
	baseFolder, err := agent.FindAgentHomeFolder(cmd.AgentDir)
	if err != nil {
		return
	}

	// get all workspace configs
	pattern := baseFolder + "/contexts/*/workspaces/*/" + provider2.WorkspaceConfigFile
	matches, err := filepath.Glob(pattern)
	if err != nil {
		log.Errorf("Error globing pattern %s: %v", pattern, err)
		return
	}

	// check when the last touch was
	for _, match := range matches {
		activity, activityWorkspace, err := getActivity(match, log)
		if err != nil {
			log.Errorf("Error checking for inactivity: %v", err)
			continue
		} else if activity == nil {
			continue
		}

		if latestActivity == nil || activity.After(*latestActivity) {
			latestActivity = activity
			workspace = activityWorkspace
		}
	}

	// should we run shutdown command?
	if latestActivity == nil {
		if len(matches) == 0 {
			log.Infof("No workspaces found in path '%s'", baseFolder)
		} else {
			log.Infof("%d workspaces found in path '%s', but none of them had any auto-stop configured or were still running / never completed successfully", len(matches), baseFolder)
		}
		return
	}

	// check timeout
	timeout := agent.DefaultInactivityTimeout
	if workspace.Agent.Timeout != "" {
		var err error
		timeout, err = time.ParseDuration(workspace.Agent.Timeout)
		if err != nil {
			log.Errorf("Error parsing inactivity timeout: %v", err)
			timeout = agent.DefaultInactivityTimeout
		}
	}
	if latestActivity.Add(timeout).After(time.Now()) {
		log.Infof("Workspace '%s' has latest activity at '%s', will auto-stop machine in %s", workspace.Workspace.ID, latestActivity.String(), time.Until(latestActivity.Add(timeout)).String())
		return
	}

	// run shutdown command
	cmd.runShutdownCommand(workspace, log)
}

func (cmd *DaemonCmd) runShutdownCommand(workspace *provider2.AgentWorkspaceInfo, log log.Logger) {
	// get environ
	environ, err := custom.ToEnvironWithBinaries(workspace, log)
	if err != nil {
		log.Errorf("%v", err)
		return
	}

	// we run the timeout command now
	buf := &bytes.Buffer{}
	log.Infof("Run shutdown command for workspace %s: %s", workspace.Workspace.ID, strings.Join(workspace.Agent.Exec.Shutdown, " "))
	err = clientimplementation.RunCommand(
		context.Background(),
		workspace.Agent.Exec.Shutdown,
		environ,
		nil,
		buf,
		buf,
	)
	if err != nil {
		log.Errorf("Error running %s: %s%w", strings.Join(workspace.Agent.Exec.Shutdown, " "), buf.String(), err)
		return
	}

	log.Infof("Successful ran command: %s", buf.String())
}

func (cmd *DaemonCmd) initialTouch(log log.Logger) {
	// get base folder
	baseFolder, err := agent.FindAgentHomeFolder(cmd.AgentDir)
	if err != nil {
		return
	}

	// get workspace configs
	pattern := baseFolder + "/contexts/*/workspaces/*/" + provider2.WorkspaceConfigFile
	matches, err := filepath.Glob(pattern)
	if err != nil {
		log.Errorf("Error globing pattern %s: %v", pattern, err)
		return
	}

	// check when the last touch was
	now := time.Now()
	for _, match := range matches {
		err := os.Chtimes(match, now, now)
		if err != nil {
			log.Errorf("Error touching workspace config %s: %v", pattern, err)
			return
		}
	}
}

func getActivity(workspaceConfig string, log log.Logger) (*time.Time, *provider2.AgentWorkspaceInfo, error) {
	workspace, err := agent.ParseAgentWorkspaceInfo(workspaceConfig)
	if err != nil {
		log.Errorf("Error reading %s: %v", workspaceConfig, err)
		return nil, nil, nil
	}

	// check if shutdown is configured
	if len(workspace.Agent.Exec.Shutdown) == 0 {
		return nil, nil, nil
	}

	// check last access time
	stat, err := os.Stat(workspaceConfig)
	if err != nil {
		return nil, nil, err
	}

	// check if workspace is locked
	t := stat.ModTime()
	if agent.HasWorkspaceBusyFile(filepath.Dir(workspaceConfig)) {
		t = t.Add(time.Minute * 20)
	}

	// check if timeout
	return &t, workspace, nil
}
