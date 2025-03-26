package workspace

import (
	"github.com/spectrumwebco/kled-beta/cmd/flags"
	"github.com/spf13/cobra"
)

// NewWorkspaceCmd returns a new command
func NewWorkspaceCmd(flags *flags.GlobalFlags) *cobra.Command {
	workspaceCmd := &cobra.Command{
		Use:   "workspace",
		Short: "Workspace commands",
	}

	workspaceCmd.AddCommand(NewUpCmd(flags))
	workspaceCmd.AddCommand(NewDeleteCmd(flags))
	workspaceCmd.AddCommand(NewStopCmd(flags))
	workspaceCmd.AddCommand(NewStatusCmd(flags))
	workspaceCmd.AddCommand(NewUpdateConfigCmd(flags))
	workspaceCmd.AddCommand(NewBuildCmd(flags))
	workspaceCmd.AddCommand(NewLogsDaemonCmd(flags))
	workspaceCmd.AddCommand(NewInstallDotfilesCmd(flags))
	workspaceCmd.AddCommand(NewSetupGPGCmd(flags))
	workspaceCmd.AddCommand(NewLogsCmd(flags))
	return workspaceCmd
}
