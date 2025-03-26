package provider

import (
	"os"

	"github.com/spectrumwebco/kled-beta/cmd/agent"
	"github.com/spectrumwebco/kled-beta/cmd/pro/flags"
	"github.com/spectrumwebco/kled-beta/cmd/pro/provider/create"
	"github.com/spectrumwebco/kled-beta/cmd/pro/provider/get"
	"github.com/spectrumwebco/kled-beta/cmd/pro/provider/list"
	"github.com/spectrumwebco/kled-beta/cmd/pro/provider/update"
	"github.com/spectrumwebco/kled-beta/cmd/pro/provider/watch"
	"github.com/spectrumwebco/kled-beta/pkg/client/clientimplementation"
	"github.com/spectrumwebco/kled-beta/pkg/platform"
	"github.com/spectrumwebco/kled-beta/pkg/platform/client"
	"github.com/spectrumwebco/kled-beta/pkg/telemetry"
	"github.com/loft-sh/log"

	"github.com/spf13/cobra"
)

// NewProProviderCmd creates a new cobra command
func NewProProviderCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	c := &cobra.Command{
		Use:    "provider",
		Short:  "DevPod Pro provider commands",
		Args:   cobra.NoArgs,
		Hidden: true,
		PersistentPreRun: func(cmd *cobra.Command, args []string) {
			if (globalFlags.Config == "" || globalFlags.Config == client.DefaultCacheConfig) && os.Getenv("LOFT_CONFIG") != "" {
				globalFlags.Config = os.Getenv(platform.ConfigEnv)
			}

			log.Default.SetFormat(log.JSONFormat)

			if os.Getenv(clientimplementation.DevPodDebug) == "true" {
				globalFlags.Debug = true
			}

			// Disable debug hints if we execute pro commands from DevPod Desktop
			// We're reusing the agent.AgentExecutedAnnotation for simplicity, could rename in the future
			if os.Getenv(telemetry.UIEnvVar) == "true" {
				cmd.VisitParents(func(c *cobra.Command) {
					// find the root command
					if c.Name() == "devpod" {
						if c.Annotations == nil {
							c.Annotations = map[string]string{}
						}
						c.Annotations[agent.AgentExecutedAnnotation] = "true"
					}
				})
			}
		},
	}

	c.AddCommand(list.NewCmd(globalFlags))
	c.AddCommand(watch.NewCmd(globalFlags))
	c.AddCommand(create.NewCmd(globalFlags))
	c.AddCommand(get.NewCmd(globalFlags))
	c.AddCommand(update.NewCmd(globalFlags))
	c.AddCommand(NewHealthCmd(globalFlags))

	c.AddCommand(NewUpCmd(globalFlags))
	c.AddCommand(NewStopCmd(globalFlags))
	c.AddCommand(NewSshCmd(globalFlags))
	c.AddCommand(NewStatusCmd(globalFlags))
	c.AddCommand(NewDeleteCmd(globalFlags))
	c.AddCommand(NewRebuildCmd(globalFlags))
	return c
}
