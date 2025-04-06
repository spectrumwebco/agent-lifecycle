package cmd

import (
	"github.com/loft-sh/devpod/cmd/flags"
	spacecmd "github.com/loft-sh/devpod/pkg/kledspace/cmd"
	"github.com/spf13/cobra"
)

func NewSpaceCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	spaceCmd := &cobra.Command{
		Use:     "space",
		Aliases: []string{"s"},
		Short:   "Manage application spaces",
		Long:    `Commands for creating and managing application spaces`,
	}
	
	spaceCmd.AddCommand(spacecmd.NewInitCmd(globalFlags))
	spaceCmd.AddCommand(spacecmd.NewDeployCmd(globalFlags))
	spaceCmd.AddCommand(spacecmd.NewListCmd(globalFlags))
	
	spaceCmd.AddCommand(spacecmd.NewKledSpaceCmd(globalFlags))
	
	return spaceCmd
}
