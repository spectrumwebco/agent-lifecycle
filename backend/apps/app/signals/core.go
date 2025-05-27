package signals

import (
	"log"
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/backend/apps/app/models"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

func CreateUserProfile(user interface{}, created bool) {
	if !created {
		return
	}

	userObj, ok := user.(*models.User)
	if !ok {
		logger.Printf("Error: user object is not of type *models.User")
		return
	}

	org := &models.Organization{
		Name:      userObj.Username + "'s Organization",
		CreatedBy: userObj,
	}

	err := core.CreateModel("Organization", org)
	if err != nil {
		logger.Printf("Error creating organization: %v", err)
		return
	}

	workspace := &models.Workspace{
		Name:         "Default Workspace",
		Organization: org,
		CreatedBy:    userObj,
	}

	err = core.CreateModel("Workspace", workspace)
	if err != nil {
		logger.Printf("Error creating workspace: %v", err)
		return
	}

	logger.Printf("Created default organization and workspace for user %s", userObj.ID)
}

func LogApiKeyCreation(apiKey *models.ApiKey, created bool) {
	if created {
		logger.Printf("API key created for user %s in organization %s", apiKey.User.ID, apiKey.Organization.ID)
	} else {
		logger.Printf("API key updated for user %s in organization %s", apiKey.User.ID, apiKey.Organization.ID)
	}
}

func SetApiKeyExpiry(apiKey *models.ApiKey) {
	if apiKey.ExpiresAt == nil || apiKey.ExpiresAt.IsZero() {
		expiryDate := time.Now().AddDate(1, 0, 0)
		apiKey.ExpiresAt = &expiryDate
	}
}

func LogOrganizationDeletion(org *models.Organization) {
	var deletedByID string
	if org.DeletedBy != nil {
		deletedByID = org.DeletedBy.ID.String()
	} else {
		deletedByID = "unknown"
	}

	logger.Printf("WARNING: Organization %s (%s) deleted by user %s", org.ID, org.Name, deletedByID)
}

func init() {
	core.RegisterSignalHandler("post_save", "User", CreateUserProfile)
	core.RegisterSignalHandler("post_save", "ApiKey", LogApiKeyCreation)
	core.RegisterSignalHandler("pre_save", "ApiKey", SetApiKeyExpiry)
	core.RegisterSignalHandler("post_delete", "Organization", LogOrganizationDeletion)
}
