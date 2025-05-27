package config

import (
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/hashicorp/vault/api"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type VaultClient struct {
	URL          string
	Token        string
	RoleID       string
	SecretID     string
	Client       *api.Client
	Authenticated bool
}

func NewVaultClient(url, token, roleID, secretID string) *VaultClient {
	if url == "" {
		url = os.Getenv("VAULT_ADDR")
		if url == "" {
			url = "http://vault.default.svc.cluster.local:8200"
		}
	}

	if token == "" {
		token = os.Getenv("VAULT_TOKEN")
	}

	if roleID == "" {
		roleID = os.Getenv("VAULT_ROLE_ID")
	}

	if secretID == "" {
		secretID = os.Getenv("VAULT_SECRET_ID")
	}

	client := &VaultClient{
		URL:      url,
		Token:    token,
		RoleID:   roleID,
		SecretID: secretID,
	}

	client.Initialize()
	return client
}

func (c *VaultClient) Initialize() {
	isLocal := !isRunningInKubernetes()

	if isLocal && c.URL == "http://vault.default.svc.cluster.local:8200" {
		c.URL = "http://localhost:8200"
		log.Printf("Local development detected, using Vault URL: %s", c.URL)
	}

	config := api.DefaultConfig()
	config.Address = c.URL

	var err error
	client, err := api.NewClient(config)
	if err != nil {
		log.Printf("Error creating Vault client: %v", err)
		return
	}

	c.Client = client

	if c.Token != "" {
		c.Client.SetToken(c.Token)
		c.Authenticated = c.Client.Token() != ""
	} else if c.RoleID != "" && c.SecretID != "" {
		c.authenticateAppRole()
	} else {
		c.authenticateKubernetes()
	}

	if !c.Authenticated {
		if isLocal {
			log.Printf("Failed to authenticate with Vault in local development mode")
		} else {
			log.Printf("Failed to authenticate with Vault")
		}
	}
}

func (c *VaultClient) authenticateAppRole() {
	data := map[string]interface{}{
		"role_id":   c.RoleID,
		"secret_id": c.SecretID,
	}

	secret, err := c.Client.Logical().Write("auth/approle/login", data)
	if err != nil {
		log.Printf("Error authenticating with Vault using AppRole: %v", err)
		return
	}

	if secret == nil || secret.Auth == nil {
		log.Printf("No auth info returned from AppRole login")
		return
	}

	c.Client.SetToken(secret.Auth.ClientToken)
	c.Authenticated = c.Client.Token() != ""
}

func (c *VaultClient) authenticateKubernetes() {
	tokenPath := "/var/run/secrets/kubernetes.io/serviceaccount/token"
	if !fileExists(tokenPath) {
		log.Printf("Not running in Kubernetes, skipping Kubernetes authentication")
		return
	}

	jwt, err := ioutil.ReadFile(tokenPath)
	if err != nil {
		log.Printf("Error reading Kubernetes service account token: %v", err)
		return
	}

	data := map[string]interface{}{
		"role": "agent-api",
		"jwt":  string(jwt),
	}

	secret, err := c.Client.Logical().Write("auth/kubernetes/login", data)
	if err != nil {
		log.Printf("Error authenticating with Vault using Kubernetes: %v", err)
		return
	}

	if secret == nil || secret.Auth == nil {
		log.Printf("No auth info returned from Kubernetes login")
		return
	}

	c.Client.SetToken(secret.Auth.ClientToken)
	c.Authenticated = c.Client.Token() != ""
}

func (c *VaultClient) ReadSecret(path string) (map[string]interface{}, error) {
	isLocal := !isRunningInKubernetes()

	if !c.Authenticated {
		c.Initialize()

		if !c.Authenticated {
			if isLocal {
				log.Printf("Not authenticated with Vault in local development mode")
			} else {
				log.Printf("Not authenticated with Vault")
			}
			return nil, fmt.Errorf("not authenticated with Vault")
		}
	}

	secret, err := c.Client.Logical().Read(fmt.Sprintf("secret/data/%s", path))
	if err != nil {
		if isLocal {
			log.Printf("Error reading secret from Vault in local development mode: %v", err)
		} else {
			log.Printf("Error reading secret from Vault: %v", err)
		}
		return nil, err
	}

	if secret == nil || secret.Data == nil {
		return nil, fmt.Errorf("no secret found at %s", path)
	}

	data, ok := secret.Data["data"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid secret data format")
	}

	return data, nil
}

func (c *VaultClient) WriteSecret(path string, data map[string]interface{}) error {
	if !c.Authenticated {
		c.Initialize()

		if !c.Authenticated {
			log.Printf("Not authenticated with Vault")
			return fmt.Errorf("not authenticated with Vault")
		}
	}

	secretData := map[string]interface{}{
		"data": data,
	}

	_, err := c.Client.Logical().Write(fmt.Sprintf("secret/data/%s", path), secretData)
	if err != nil {
		log.Printf("Error writing secret to Vault: %v", err)
		return err
	}

	return nil
}

func (c *VaultClient) DeleteSecret(path string) error {
	if !c.Authenticated {
		c.Initialize()

		if !c.Authenticated {
			log.Printf("Not authenticated with Vault")
			return fmt.Errorf("not authenticated with Vault")
		}
	}

	_, err := c.Client.Logical().Delete(fmt.Sprintf("secret/metadata/%s", path))
	if err != nil {
		log.Printf("Error deleting secret from Vault: %v", err)
		return err
	}

	return nil
}

type DatabaseSecrets struct {
	VaultClient *VaultClient
}

func NewDatabaseSecrets(vaultClient *VaultClient) *DatabaseSecrets {
	if vaultClient == nil {
		vaultClient = NewVaultClient("", "", "", "")
	}

	return &DatabaseSecrets{
		VaultClient: vaultClient,
	}
}

func (s *DatabaseSecrets) GetDatabaseCredentials(database string) (map[string]interface{}, error) {
	path := fmt.Sprintf("database/%s", database)
	return s.VaultClient.ReadSecret(path)
}

func (s *DatabaseSecrets) StoreDatabaseCredentials(database string, credentials map[string]interface{}) error {
	path := fmt.Sprintf("database/%s", database)
	return s.VaultClient.WriteSecret(path, credentials)
}

func (s *DatabaseSecrets) ConfigureDjangoDatabases() map[string]map[string]interface{} {
	databases := make(map[string]map[string]interface{})

	defaultCredentials, err := s.GetDatabaseCredentials("default")
	if err == nil && defaultCredentials != nil {
		databases["default"] = map[string]interface{}{
			"ENGINE":   getStringWithDefault(defaultCredentials, "engine", "django.db.backends.postgresql"),
			"NAME":     getStringWithDefault(defaultCredentials, "name", "postgres"),
			"USER":     getStringWithDefault(defaultCredentials, "user", "postgres"),
			"PASSWORD": getStringWithDefault(defaultCredentials, "password", "postgres"),
			"HOST":     getStringWithDefault(defaultCredentials, "host", "supabase-db.default.svc.cluster.local"),
			"PORT":     getIntWithDefault(defaultCredentials, "port", 5432),
			"OPTIONS": map[string]interface{}{
				"sslmode": "require",
			},
		}
	}

	agentCredentials, err := s.GetDatabaseCredentials("agent")
	if err == nil && agentCredentials != nil {
		databases["agent"] = map[string]interface{}{
			"ENGINE":   getStringWithDefault(agentCredentials, "engine", "django.db.backends.postgresql"),
			"NAME":     getStringWithDefault(agentCredentials, "name", "agent_db"),
			"USER":     getStringWithDefault(agentCredentials, "user", "postgres"),
			"PASSWORD": getStringWithDefault(agentCredentials, "password", "postgres"),
			"HOST":     getStringWithDefault(agentCredentials, "host", "supabase-db.default.svc.cluster.local"),
			"PORT":     getIntWithDefault(agentCredentials, "port", 5432),
			"OPTIONS": map[string]interface{}{
				"sslmode": "require",
			},
		}
	}

	trajectoryCredentials, err := s.GetDatabaseCredentials("trajectory")
	if err == nil && trajectoryCredentials != nil {
		databases["trajectory"] = map[string]interface{}{
			"ENGINE":   getStringWithDefault(trajectoryCredentials, "engine", "django.db.backends.postgresql"),
			"NAME":     getStringWithDefault(trajectoryCredentials, "name", "trajectory_db"),
			"USER":     getStringWithDefault(trajectoryCredentials, "user", "postgres"),
			"PASSWORD": getStringWithDefault(trajectoryCredentials, "password", "postgres"),
			"HOST":     getStringWithDefault(trajectoryCredentials, "host", "supabase-db.default.svc.cluster.local"),
			"PORT":     getIntWithDefault(trajectoryCredentials, "port", 5432),
			"OPTIONS": map[string]interface{}{
				"sslmode": "require",
			},
		}
	}

	mlCredentials, err := s.GetDatabaseCredentials("ml")
	if err == nil && mlCredentials != nil {
		databases["ml"] = map[string]interface{}{
			"ENGINE":   getStringWithDefault(mlCredentials, "engine", "django.db.backends.postgresql"),
			"NAME":     getStringWithDefault(mlCredentials, "name", "ml_db"),
			"USER":     getStringWithDefault(mlCredentials, "user", "postgres"),
			"PASSWORD": getStringWithDefault(mlCredentials, "password", "postgres"),
			"HOST":     getStringWithDefault(mlCredentials, "host", "supabase-db.default.svc.cluster.local"),
			"PORT":     getIntWithDefault(mlCredentials, "port", 5432),
			"OPTIONS": map[string]interface{}{
				"sslmode": "require",
			},
		}
	}

	return databases
}


func fileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func getStringWithDefault(data map[string]interface{}, key, defaultValue string) string {
	if value, ok := data[key].(string); ok {
		return value
	}
	return defaultValue
}

func getIntWithDefault(data map[string]interface{}, key string, defaultValue int) int {
	if value, ok := data[key].(int); ok {
		return value
	}
	if value, ok := data[key].(float64); ok {
		return int(value)
	}
	return defaultValue
}

var (
	DefaultVaultClient    = NewVaultClient("", "", "", "")
	DefaultDatabaseSecrets = NewDatabaseSecrets(DefaultVaultClient)
)

func init() {
	core.RegisterConfig("vault", map[string]interface{}{
		"vault_client":     DefaultVaultClient,
		"database_secrets": DefaultDatabaseSecrets,
	})
}
