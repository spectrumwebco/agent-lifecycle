package cmd

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/spf13/cobra"
)

func NewSpaceCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	spaceCmd := &cobra.Command{
		Use:     "space",
		Aliases: []string{"s"},
		Short:   "Manage development spaces",
		Long:    `Commands for creating and managing development spaces`,
	}
	
	
	return spaceCmd
}
