package cmd

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/spf13/cobra"
)

func NewKledSpaceCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	kledspaceCmd := &cobra.Command{
		Use:   "kledspace",
		Short: "Manage application spaces",
		Long: `
The kledspace commands can be used to create and manage application spaces.
These are development environments with predefined configurations and tools.
`,
	}

	kledspaceCmd.AddCommand(NewInitCmd(globalFlags))
	kledspaceCmd.AddCommand(NewDeployCmd(globalFlags))
	kledspaceCmd.AddCommand(NewListCmd(globalFlags))

	return kledspaceCmd
}
