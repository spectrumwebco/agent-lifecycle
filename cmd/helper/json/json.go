package json

import (
	"github.com/spectrumwebco/kled-beta/cmd/flags"
	"github.com/spf13/cobra"
)

// NewJSONCmd returns a new command
func NewJSONCmd(flags *flags.GlobalFlags) *cobra.Command {
	jsonCmd := &cobra.Command{
		Use:    "json",
		Short:  "DevPod JSON Utility Commands",
		Hidden: true,
	}

	jsonCmd.AddCommand(NewGetCmd())
	return jsonCmd
}
