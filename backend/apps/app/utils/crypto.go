package utils

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"fmt"
	"os"
	"strings"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"golang.org/x/crypto/pbkdf2"
)

func GenerateKey() []byte {
	key := make([]byte, 32)
	_, err := rand.Read(key)
	if err != nil {
		panic(fmt.Sprintf("Failed to generate key: %v", err))
	}
	return key
}

func GetEncryptionKey() []byte {
	settings, err := core.GetSettings()
	if err != nil {
		return GenerateKey()
	}

	key, ok := settings.Get("ENCRYPTION_KEY")
	if !ok {
		return GenerateKey()
	}

	switch k := key.(type) {
	case string:
		return []byte(k)
	case []byte:
		return k
	default:
		return GenerateKey()
	}
}

func EncryptValue(value string) string {
	if value == "" {
		return ""
	}

	key := GetEncryptionKey()
	
	result, err := core.CallPythonFunction("cryptography.fernet", "Fernet", []interface{}{key})
	if err != nil {
		panic(fmt.Sprintf("Failed to create Fernet: %v", err))
	}
	
	encrypted, err := core.CallMethod(result, "encrypt", []interface{}{[]byte(value)})
	if err != nil {
		panic(fmt.Sprintf("Failed to encrypt: %v", err))
	}
	
	return base64.StdEncoding.EncodeToString(encrypted.([]byte))
}

func DecryptValue(encryptedValue string) string {
	if encryptedValue == "" {
		return ""
	}

	key := GetEncryptionKey()
	
	result, err := core.CallPythonFunction("cryptography.fernet", "Fernet", []interface{}{key})
	if err != nil {
		panic(fmt.Sprintf("Failed to create Fernet: %v", err))
	}
	
	decoded, err := base64.StdEncoding.DecodeString(encryptedValue)
	if err != nil {
		panic(fmt.Sprintf("Failed to decode base64: %v", err))
	}
	
	decrypted, err := core.CallMethod(result, "decrypt", []interface{}{decoded})
	if err != nil {
		panic(fmt.Sprintf("Failed to decrypt: %v", err))
	}
	
	return string(decrypted.([]byte))
}

func GenerateAPIKey() string {
	randomBytes := make([]byte, 32)
	_, err := rand.Read(randomBytes)
	if err != nil {
		panic(fmt.Sprintf("Failed to generate random bytes: %v", err))
	}
	
	apiKey := base64.URLEncoding.EncodeToString(randomBytes)
	apiKey = strings.TrimRight(apiKey, "=")
	
	return fmt.Sprintf("kled_%s", apiKey)
}

func HashPassword(password string, salt []byte) (string, []byte) {
	if salt == nil {
		salt = make([]byte, 16)
		_, err := rand.Read(salt)
		if err != nil {
			panic(fmt.Sprintf("Failed to generate salt: %v", err))
		}
	}
	
	hashed := pbkdf2.Key([]byte(password), salt, 100000, 32, sha256.New)
	
	return base64.StdEncoding.EncodeToString(hashed), salt
}

func VerifyPassword(password string, hashedPassword string, salt []byte) bool {
	newHash, _ := HashPassword(password, salt)
	return newHash == hashedPassword
}

func GenerateRandomToken(length int) string {
	if length <= 0 {
		length = 32
	}
	
	const alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	
	bytes := make([]byte, length)
	_, err := rand.Read(bytes)
	if err != nil {
		panic(fmt.Sprintf("Failed to generate random bytes: %v", err))
	}
	
	for i, b := range bytes {
		bytes[i] = alphabet[b%byte(len(alphabet))]
	}
	
	return string(bytes)
}

func init() {
	core.RegisterFunction("generate_key", GenerateKey)
	core.RegisterFunction("get_encryption_key", GetEncryptionKey)
	core.RegisterFunction("encrypt_value", EncryptValue)
	core.RegisterFunction("decrypt_value", DecryptValue)
	core.RegisterFunction("generate_api_key", GenerateAPIKey)
	core.RegisterFunction("hash_password", HashPassword)
	core.RegisterFunction("verify_password", VerifyPassword)
	core.RegisterFunction("generate_random_token", GenerateRandomToken)
}
