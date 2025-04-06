package provider

type ProviderKataDriverConfig struct {
	Path string `json:"path,omitempty"`

	ContainerdPath string `json:"containerdPath,omitempty"`

	Install types.StrBool `json:"install,omitempty"`

	Env map[string]string `json:"env,omitempty"`
}
