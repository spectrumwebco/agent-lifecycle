package machine

import (
	"context"

	"github.com/spectrumwebco/kled-beta/cmd/flags"
	"github.com/spectrumwebco/kled-beta/pkg/client"
	"github.com/spectrumwebco/kled-beta/pkg/config"
	"github.com/spectrumwebco/kled-beta/pkg/workspace"
	"github.com/loft-sh/log"
	"github.com/spf13/cobra"
)

// StopCmd holds the configuration
type StopCmd struct {
	*flags.GlobalFlags
}

// NewStopCmd creates a new destroy command
func NewStopCmd(flags *flags.GlobalFlags) *cobra.Command {
	cmd := &StopCmd{
		GlobalFlags: flags,
	}
	stopCmd := &cobra.Command{
		Use:   "stop [name]",
		Short: "Stops an existing machine",
		RunE: func(_ *cobra.Command, args []string) error {
			return cmd.Run(context.Background(), args)
		},
	}

	return stopCmd
}

// Run runs the command logic
func (cmd *StopCmd) Run(ctx context.Context, args []string) error {
	devPodConfig, err := config.LoadConfig(cmd.Context, cmd.Provider)
	if err != nil {
		return err
	}

	machineClient, err := workspace.GetMachine(devPodConfig, args, log.Default)
	if err != nil {
		return err
	}

	err = machineClient.Stop(ctx, client.StopOptions{})
	if err != nil {
		return err
	}

	return nil
}
