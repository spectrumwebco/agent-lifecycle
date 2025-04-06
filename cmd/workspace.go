package cmd

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/spf13/cobra"
)

func NewWorkspaceCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	workspaceCmd := &cobra.Command{
		Use:     "workspace",
		Aliases: []string{"env", "w"},
		Short:   "Manage development workspaces",
		Long:    `Commands for creating and managing development workspaces`,
	}

	workspaceCmd.AddCommand(NewUpCmd(globalFlags))
	workspaceCmd.AddCommand(NewSSHCmd(globalFlags))
	workspaceCmd.AddCommand(NewStatusCmd(globalFlags))
	workspaceCmd.AddCommand(NewDeleteCmd(globalFlags))
	workspaceCmd.AddCommand(NewListCmd(globalFlags))
	workspaceCmd.AddCommand(NewStopCmd(globalFlags))
	workspaceCmd.AddCommand(NewBuildCmd(globalFlags))
	workspaceCmd.AddCommand(NewExportCmd(globalFlags))
	workspaceCmd.AddCommand(NewImportCmd(globalFlags))
	workspaceCmd.AddCommand(NewLogsCmd(globalFlags))
	
	return workspaceCmd
}
