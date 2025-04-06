package cmd

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/loft-sh/log"
	"github.com/spf13/cobra"
)

func NewListCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List application spaces",
		Long: `
Lists all application spaces in the current context.
`,
		RunE: func(cobraCmd *cobra.Command, args []string) error {
			log.GetInstance().Infof("Listing application spaces...")
			return nil
		},
	}

	return cmd
}
