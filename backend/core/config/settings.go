package config

import (
	"os"
	"path/filepath"
	"strings"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type ApiSettings struct {
	ApiKey              string   `json:"api_key"`
	Debug               bool     `json:"debug"`
	AllowedHosts        []string `json:"allowed_hosts"`
	DorisHost           string   `json:"doris_host"`
	DorisPort           int      `json:"doris_port"`
	DorisUser           string   `json:"doris_user"`
	DorisPassword       string   `json:"doris_password"`
	DorisDB             string   `json:"doris_db"`
	PostgresHost        string   `json:"postgres_host"`
	PostgresPort        int      `json:"postgres_port"`
	PostgresUser        string   `json:"postgres_user"`
	PostgresPassword    string   `json:"postgres_password"`
	PostgresDB          string   `json:"postgres_db"`
	KafkaBootstrapServers string `json:"kafka_bootstrap_servers"`
	KafkaTopicPrefix    string   `json:"kafka_topic_prefix"`
	SupabaseURL         string   `json:"supabase_url"`
	SupabaseKey         string   `json:"supabase_key"`
	DragonflyHost       string   `json:"dragonfly_host"`
	DragonflyPort       int      `json:"dragonfly_port"`
	DragonflyPassword   string   `json:"dragonfly_password"`
	DragonflySSL        bool     `json:"dragonfly_ssl"`
	DragonflyDB         int      `json:"dragonfly_db"`
	RagflowURL          string   `json:"ragflow_url"`
	RagflowAPIKey       string   `json:"ragflow_api_key"`
	RocketMQNameServer  string   `json:"rocketmq_name_server"`
	RocketMQProducerGroup string `json:"rocketmq_producer_group"`
	RocketMQConsumerGroup string `json:"rocketmq_consumer_group"`
	GRPCHost            string   `json:"grpc_host"`
	GRPCPort            int      `json:"grpc_port"`
	MLApiURL            string   `json:"ml_api_url"`
	MLApiKey            string   `json:"ml_api_key"`
}

func NewApiSettings() *ApiSettings {
	return &ApiSettings{
		ApiKey:              getEnv("AGENT_API_KEY", "dev-api-key"),
		Debug:               getEnvBool("AGENT_DEBUG", true),
		AllowedHosts:        strings.Split(getEnv("AGENT_ALLOWED_HOSTS", "*"), ","),
		DorisHost:           getEnv("AGENT_DORIS_HOST", "doris-fe.default.svc.cluster.local"),
		DorisPort:           getEnvInt("AGENT_DORIS_PORT", 9030),
		DorisUser:           getEnv("AGENT_DORIS_USER", "root"),
		DorisPassword:       getEnv("AGENT_DORIS_PASSWORD", ""),
		DorisDB:             getEnv("AGENT_DORIS_DB", "agent_runtime"),
		PostgresHost:        getEnv("AGENT_POSTGRES_HOST", "agent-postgres-cluster-primary.default.svc.cluster.local"),
		PostgresPort:        getEnvInt("AGENT_POSTGRES_PORT", 5432),
		PostgresUser:        getEnv("AGENT_POSTGRES_USER", "agent_user"),
		PostgresPassword:    getEnv("AGENT_POSTGRES_PASSWORD", ""),
		PostgresDB:          getEnv("AGENT_POSTGRES_DB", "agent_runtime"),
		KafkaBootstrapServers: getEnv("AGENT_KAFKA_BOOTSTRAP_SERVERS", "kafka.default.svc.cluster.local:9092"),
		KafkaTopicPrefix:    getEnv("AGENT_KAFKA_TOPIC_PREFIX", "agent_runtime"),
		SupabaseURL:         getEnv("AGENT_SUPABASE_URL", "http://supabase-db.default.svc.cluster.local:8000"),
		SupabaseKey:         getEnv("AGENT_SUPABASE_KEY", ""),
		DragonflyHost:       getEnv("AGENT_DRAGONFLY_HOST", "dragonfly.default.svc.cluster.local"),
		DragonflyPort:       getEnvInt("AGENT_DRAGONFLY_PORT", 6379),
		DragonflyPassword:   getEnv("AGENT_DRAGONFLY_PASSWORD", ""),
		DragonflySSL:        getEnvBool("AGENT_DRAGONFLY_SSL", false),
		DragonflyDB:         getEnvInt("AGENT_DRAGONFLY_DB", 0),
		RagflowURL:          getEnv("AGENT_RAGFLOW_URL", "http://ragflow.default.svc.cluster.local:8000"),
		RagflowAPIKey:       getEnv("AGENT_RAGFLOW_API_KEY", ""),
		RocketMQNameServer:  getEnv("AGENT_ROCKETMQ_NAME_SERVER", "rocketmq-namesrv.default.svc.cluster.local:9876"),
		RocketMQProducerGroup: getEnv("AGENT_ROCKETMQ_PRODUCER_GROUP", "agent_runtime_producer"),
		RocketMQConsumerGroup: getEnv("AGENT_ROCKETMQ_CONSUMER_GROUP", "agent_runtime_consumer"),
		GRPCHost:            getEnv("AGENT_GRPC_HOST", "0.0.0.0"),
		GRPCPort:            getEnvInt("AGENT_GRPC_PORT", 50051),
		MLApiURL:            getEnv("AGENT_ML_API_URL", "http://localhost:8000"),
		MLApiKey:            getEnv("AGENT_ML_API_KEY", ""),
	}
}

func GetBaseDir() string {
	execPath, err := os.Executable()
	if err != nil {
		execPath = os.Args[0]
	}
	
	return filepath.Dir(filepath.Dir(filepath.Dir(execPath)))
}

func GetSecretKey() string {
	return getEnv("AGENT_SECRET_KEY", "django-insecure-darztxot86at54=)1oisit@34zow4b$@&&kv4ka$(j%mlis6u3")
}

func GetInstalledApps() []string {
	return []string{
		"django.contrib.admin",
		"django.contrib.auth",
		"django.contrib.contenttypes",
		"django.contrib.sessions",
		"django.contrib.messages",
		"django.contrib.staticfiles",
		"rest_framework",
		"corsheaders",
		"channels",
		"apps.app.apps.ApplicationConfig",
		"apps.agent.apps.AgentConfig",
		"apps.ml.apps.MLConfig",
	}
}

func GetMiddleware() []string {
	return []string{
		"django.middleware.security.SecurityMiddleware",
		"django.contrib.sessions.middleware.SessionMiddleware",
		"corsheaders.middleware.CorsMiddleware",
		"django.middleware.common.CommonMiddleware",
		"django.middleware.csrf.CsrfViewMiddleware",
		"django.contrib.auth.middleware.AuthenticationMiddleware",
		"django.contrib.messages.middleware.MessageMiddleware",
		"django.middleware.clickjacking.XFrameOptionsMiddleware",
		"apps.agent.agent_framework.django_views.middleware.AgentFrameworkExceptionMiddleware",
	}
}

func GetTemplates() []map[string]interface{} {
	return []map[string]interface{}{
		{
			"BACKEND": "django.template.backends.django.DjangoTemplates",
			"DIRS":    []string{filepath.Join(GetBaseDir(), "templates")},
			"APP_DIRS": true,
			"OPTIONS": map[string]interface{}{
				"context_processors": []string{
					"django.template.context_processors.request",
					"django.contrib.auth.context_processors.auth",
					"django.contrib.messages.context_processors.messages",
				},
			},
		},
	}
}

func GetAuthPasswordValidators() []map[string]string {
	return []map[string]string{
		{
			"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
		},
		{
			"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
		},
		{
			"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
		},
		{
			"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
		},
	}
}

func GetRestFramework() map[string]interface{} {
	return map[string]interface{}{
		"DEFAULT_PERMISSION_CLASSES": []string{
			"rest_framework.permissions.IsAuthenticated",
		},
		"DEFAULT_AUTHENTICATION_CLASSES": []string{
			"rest_framework.authentication.SessionAuthentication",
			"rest_framework.authentication.BasicAuthentication",
		},
		"DEFAULT_RENDERER_CLASSES": []string{
			"rest_framework.renderers.JSONRenderer",
			"rest_framework.renderers.BrowsableAPIRenderer",
		},
		"DEFAULT_PARSER_CLASSES": []string{
			"rest_framework.parsers.JSONParser",
			"rest_framework.parsers.FormParser",
			"rest_framework.parsers.MultiPartParser",
		},
	}
}

func GetDragonflyConfig() map[string]interface{} {
	apiSettings := NewApiSettings()
	return map[string]interface{}{
		"host":     apiSettings.DragonflyHost,
		"port":     apiSettings.DragonflyPort,
		"password": apiSettings.DragonflyPassword,
		"ssl":      apiSettings.DragonflySSL,
		"db":       apiSettings.DragonflyDB,
	}
}

func GetChannelLayers() map[string]interface{} {
	dragonflyConfig := GetDragonflyConfig()
	password := dragonflyConfig["password"].(string)
	passwordConfig := interface{}(nil)
	if password != "" {
		passwordConfig = password
	}
	
	return map[string]interface{}{
		"default": map[string]interface{}{
			"BACKEND": "channels_redis.core.RedisChannelLayer",
			"CONFIG": map[string]interface{}{
				"hosts":    []interface{}{[]interface{}{dragonflyConfig["host"], dragonflyConfig["port"]}},
				"prefix":   "agent_api:",
				"capacity": 1500,
				"expiry":   60,
				"password": passwordConfig,
				"ssl":      dragonflyConfig["ssl"],
			},
		},
	}
}

func GetCaches() map[string]interface{} {
	redisConfig := GetDorisRedisConfig()
	password := redisConfig["password"].(string)
	passwordConfig := interface{}(nil)
	if password != "" {
		passwordConfig = password
	}
	
	return map[string]interface{}{
		"default": map[string]interface{}{
			"BACKEND":  "django_redis.cache.RedisCache",
			"LOCATION": "redis://" + redisConfig["host"].(string) + ":" + 
				        redisConfig["port"].(string) + "/" + 
				        redisConfig["db"].(string),
			"OPTIONS": map[string]interface{}{
				"CLIENT_CLASS": "django_redis.client.DefaultClient",
				"PASSWORD":     passwordConfig,
				"SSL":          redisConfig["ssl"],
			},
		},
	}
}

func GetDjangoSettings() map[string]interface{} {
	apiSettings := NewApiSettings()
	baseDir := GetBaseDir()
	
	databases := map[string]interface{}{
		"default": map[string]interface{}{
			"ENGINE": "django.db.backends.sqlite3",
			"NAME":   filepath.Join(baseDir, "db.sqlite3"),
		},
	}
	
	postgresDBs := GetPostgresOperatorDatabases()
	for dbName, dbConfig := range postgresDBs {
		databases[dbName] = dbConfig
	}
	
	dorisDBs := GetDorisDatabases()
	for dbName, dbConfig := range dorisDBs {
		if dbName != "default" { // Don't override default
			databases[dbName] = dbConfig
		}
	}
	
	vaultDatabases := DefaultDatabaseSecrets.ConfigureDjangoDatabases()
	for dbName, dbConfig := range vaultDatabases {
		if existingDB, ok := databases[dbName]; ok {
			existingDBMap := existingDB.(map[string]interface{})
			dbConfigMap := dbConfig.(map[string]interface{})
			
			if user, ok := dbConfigMap["USER"]; ok {
				existingDBMap["USER"] = user
			}
			if password, ok := dbConfigMap["PASSWORD"]; ok {
				existingDBMap["PASSWORD"] = password
			}
			if host, ok := dbConfigMap["HOST"]; ok {
				existingDBMap["HOST"] = host
			}
			if port, ok := dbConfigMap["PORT"]; ok {
				existingDBMap["PORT"] = port
			}
		} else {
			databases[dbName] = dbConfig
		}
	}
	
	return map[string]interface{}{
		"BASE_DIR":                baseDir,
		"SECRET_KEY":              GetSecretKey(),
		"DEBUG":                   apiSettings.Debug,
		"ALLOWED_HOSTS":           apiSettings.AllowedHosts,
		"API_KEY":                 apiSettings.ApiKey,
		"INSTALLED_APPS":          GetInstalledApps(),
		"ASGI_APPLICATION":        "agent_api.routing.application",
		"DATABASE_ROUTERS":        []string{"core.config.database_routers.AgentRuntimeRouter"},
		"DATABASES":               databases,
		"DRAGONFLY_CONFIG":        GetDragonflyConfig(),
		"CHANNEL_LAYERS":          GetChannelLayers(),
		"MIDDLEWARE":              GetMiddleware(),
		"CORS_ALLOW_ALL_ORIGINS":  true,
		"CORS_ALLOW_CREDENTIALS": true,
		"ROOT_URLCONF":            "core.urls.root",
		"TEMPLATES":               GetTemplates(),
		"WSGI_APPLICATION":        "core.config.wsgi.application",
		"CACHES":                  GetCaches(),
		"SESSION_ENGINE":          "django.contrib.sessions.backends.cache",
		"SESSION_CACHE_ALIAS":     "default",
		"AUTH_PASSWORD_VALIDATORS": GetAuthPasswordValidators(),
		"LANGUAGE_CODE":           "en-us",
		"TIME_ZONE":               "UTC",
		"USE_I18N":                true,
		"USE_TZ":                  true,
		"STATIC_URL":              "static/",
		"DEFAULT_AUTO_FIELD":      "django.db.models.BigAutoField",
		"REST_FRAMEWORK":          GetRestFramework(),
		"GRPC_SERVER_HOST":        apiSettings.GRPCHost,
		"GRPC_SERVER_PORT":        apiSettings.GRPCPort,
		"SRC_DIR":                 filepath.Join(baseDir, "apps", "ml"),
		"AGENT_DIR":               filepath.Join(baseDir, "apps", "agent"),
		"TOOLS_DIR":               filepath.Join(baseDir, "apps", "agent", "tools"),
	}
}

func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

func getEnvBool(key string, defaultValue bool) bool {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value == "true" || value == "True" || value == "1" || value == "yes" || value == "Yes"
}

func getEnvInt(key string, defaultValue int) int {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	var result int
	_, err := fmt.Sscanf(value, "%d", &result)
	if err != nil {
		return defaultValue
	}
	return result
}

func init() {
	pythonPath := filepath.Join(GetBaseDir(), "apps")
	os.Setenv("PYTHONPATH", pythonPath+":"+os.Getenv("PYTHONPATH"))
	
	core.RegisterConfig("settings", GetDjangoSettings())
}
