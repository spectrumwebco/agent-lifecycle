package agent

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strconv"
	"strings"

	"github.com/spectrumwebco/kled-beta/cmd/flags"
	"github.com/spectrumwebco/kled-beta/pkg/dockercredentials"
	devpodhttp "github.com/spectrumwebco/kled-beta/pkg/http"
	"github.com/loft-sh/log"
	"github.com/spf13/cobra"
)

// DockerCredentialsCmd holds the cmd flags
type DockerCredentialsCmd struct {
	*flags.GlobalFlags

	Port int
}

// NewDockerCredentialsCmd creates a new command
func NewDockerCredentialsCmd(flags *flags.GlobalFlags) *cobra.Command {
	cmd := &DockerCredentialsCmd{
		GlobalFlags: flags,
	}
	dockerCredentialsCmd := &cobra.Command{
		Use:   "docker-credentials",
		Short: "Retrieves docker-credentials from the local machine",
		RunE: func(_ *cobra.Command, args []string) error {
			return cmd.Run(context.Background(), args, log.Default.ErrorStreamOnly())
		},
	}
	dockerCredentialsCmd.Flags().IntVar(&cmd.Port, "port", 0, "If specified, will use the given port")
	_ = dockerCredentialsCmd.MarkFlagRequired("port")
	return dockerCredentialsCmd
}

func (cmd *DockerCredentialsCmd) Run(ctx context.Context, args []string, log log.Logger) error {
	if len(args) == 0 {
		return nil
	}

	// we only handle get and list
	if args[0] == "get" {
		return cmd.handleGet(log)
	} else if args[0] == "list" {
		return cmd.handleList(log)
	}

	return nil
}

func (cmd *DockerCredentialsCmd) handleList(log log.Logger) error {
	rawJSON, err := json.Marshal(&dockercredentials.Request{})
	if err != nil {
		return err
	}

	response, err := devpodhttp.GetHTTPClient().Post("http://localhost:"+strconv.Itoa(cmd.Port)+"/docker-credentials", "application/json", bytes.NewReader(rawJSON))
	if err != nil {
		log.Errorf("Error retrieving list credentials: %v", err)
		return nil
	}
	defer response.Body.Close()

	raw, err := io.ReadAll(response.Body)
	if err != nil {
		log.Errorf("Error reading list credentials: %v", err)
		return nil
	}

	// has the request succeeded?
	if response.StatusCode != http.StatusOK {
		log.Errorf("Error reading list credentials (%d): %v", response.StatusCode, string(raw))
		return nil
	}

	listResponse := &dockercredentials.ListResponse{}
	err = json.Unmarshal(raw, listResponse)
	if err != nil {
		log.Errorf("Error decoding list credentials: %s%v", string(raw), err)
		return nil
	}

	if listResponse.Registries == nil {
		listResponse.Registries = map[string]string{}
	}
	raw, err = json.Marshal(listResponse.Registries)
	if err != nil {
		log.Errorf("Error encoding list credentials: %v", err)
		return nil
	}

	// print response to stdout
	fmt.Print(string(raw))
	return nil
}

func (cmd *DockerCredentialsCmd) handleGet(log log.Logger) error {
	url, err := io.ReadAll(os.Stdin)
	if err != nil {
		return err
	} else if len(strings.TrimSpace(string(url))) == 0 {
		return fmt.Errorf("no credentials server URL")
	}

	rawJSON, err := json.Marshal(&dockercredentials.Request{ServerURL: strings.TrimSpace(string(url))})
	if err != nil {
		return err
	}

	response, err := devpodhttp.GetHTTPClient().Post("http://localhost:"+strconv.Itoa(cmd.Port)+"/docker-credentials", "application/json", bytes.NewReader(rawJSON))
	if err != nil {
		log.Errorf("Error retrieving credentials: %v", err)
		return nil
	}
	defer response.Body.Close()

	raw, err := io.ReadAll(response.Body)
	if err != nil {
		log.Errorf("Error reading credentials: %v", err)
		return nil
	}

	// has the request succeeded?
	if response.StatusCode != http.StatusOK {
		log.Errorf("Error reading credentials (%d): %v", response.StatusCode, string(raw))
		return nil
	}

	// try to unmarshal
	err = json.Unmarshal(raw, &dockercredentials.Credentials{})
	if err != nil {
		log.Errorf("Error parsing credentials: %v", err)
		return nil
	}

	// print response to stdout
	fmt.Print(string(raw))
	return nil
}
