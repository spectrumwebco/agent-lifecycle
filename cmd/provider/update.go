package provider

import (
	"context"
	"fmt"

	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/loft-sh/devpod/pkg/config"
	"github.com/loft-sh/devpod/pkg/workspace"
	"github.com/loft-sh/log"
	"github.com/pkg/errors"
	"github.com/spf13/cobra"
)

// UpdateCmd holds the cmd flags
type UpdateCmd struct {
	*flags.GlobalFlags

	Use     bool
	Options []string
}

// NewUpdateCmd creates a new command
func NewUpdateCmd(flags *flags.GlobalFlags) *cobra.Command {
	cmd := &UpdateCmd{
		GlobalFlags: flags,
	}
	updateCmd := &cobra.Command{
		Use:   "update [name] [URL or path]",
		Short: "Updates a provider in Kled",
		RunE: func(_ *cobra.Command, args []string) error {
			ctx := context.Background()
			kledConfig, err := config.LoadConfig(cmd.Context, cmd.Provider) // TODO: Update variable name to reflect Kled branding
			if err != nil {
				return err
			}

			return cmd.Run(ctx, kledConfig, args)
		},
	}

	updateCmd.Flags().BoolVar(&cmd.Use, "use", true, "If enabled will automatically activate the provider")
	updateCmd.Flags().StringArrayVarP(&cmd.Options, "option", "o", []string{}, "Provider option in the form KEY=VALUE")
	return updateCmd
}

func (cmd *UpdateCmd) Run(ctx context.Context, kledConfig *config.Config, args []string) error {
	if len(args) != 1 && len(args) != 2 {
		return fmt.Errorf("please specify either a local file, url or git repository. E.g. kled provider update my-provider loft-sh/devpod-provider-gcloud") // TODO: Update to kled-provider-gcloud when repositories are renamed
	}

	providerSource := ""
	if len(args) == 2 {
		providerSource = args[1]
	}

	providerConfig, err := workspace.UpdateProvider(kledConfig, args[0], providerSource, log.Default)
	if err != nil {
		return err
	}

	log.Default.Donef("Successfully updated provider %s", providerConfig.Name)
	if cmd.Use {
		err = ConfigureProvider(ctx, providerConfig, kledConfig.DefaultContext, cmd.Options, false, false, false, nil, log.Default)
		if err != nil {
			log.Default.Errorf("Error configuring provider, please retry with 'kled provider use %s --reconfigure'", providerConfig.Name)
			return errors.Wrap(err, "configure provider")
		}

		return nil
	}

	log.Default.Infof("To use the provider, please run the following command:")
	log.Default.Infof("devpod provider use %s", providerConfig.Name)
	return nil
}
