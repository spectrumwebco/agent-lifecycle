package cmd

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/spf13/cobra"
)

func NewPolicyCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	policyCmd := &cobra.Command{
		Use:     "policy",
		Aliases: []string{"p"},
		Short:   "Manage policies",
		Long:    `Commands for creating and managing policies`,
	}
	
	
	return policyCmd
}
