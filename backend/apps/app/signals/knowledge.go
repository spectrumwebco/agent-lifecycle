package signals

import (
	"log"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/backend/apps/app/models"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

func HandleKnowledgeItemCreation(item *models.KnowledgeItem, created bool) {
	if created {
		logger.Printf("New knowledge item created: %s in knowledge base %s", item.ID, item.KnowledgeBase.ID)
		
		generateEmbedding(item)
	} else {
		if contentChanged, ok := core.GetObjectAttribute(item, "_content_changed").(bool); ok && contentChanged {
			logger.Printf("Knowledge item %s content updated, regenerating embedding", item.ID)
			
			generateEmbedding(item)
		}
	}
}

func TrackKnowledgeItemChanges(item *models.KnowledgeItem) {
	if item.ID != uuid.Nil {
		var previous models.KnowledgeItem
		err := core.GetModelByID("KnowledgeItem", item.ID, &previous)
		if err != nil {
			logger.Printf("Error getting previous knowledge item: %v", err)
			core.SetObjectAttribute(item, "_content_changed", false)
			return
		}

		if previous.Content != item.Content {
			core.SetObjectAttribute(item, "_content_changed", true)
		} else {
			core.SetObjectAttribute(item, "_content_changed", false)
		}
	} else {
		core.SetObjectAttribute(item, "_content_changed", false)
	}
}

func HandleKnowledgeBaseCreation(kb *models.KnowledgeBase, created bool) {
	if created {
		logger.Printf("New knowledge base created: %s", kb.ID)
		
		defaultCategories := []string{"General", "Documentation", "Code", "Tutorials"}
		for _, categoryName := range defaultCategories {
			category := &models.KnowledgeCategory{
				Name:         categoryName,
				Organization: kb.Organization,
				CreatedBy:    kb.CreatedBy,
			}
			
			err := core.CreateModel("KnowledgeCategory", category)
			if err != nil {
				logger.Printf("Error creating knowledge category: %v", err)
			}
		}
	}
}

func HandleKnowledgeItemDeletion(item *models.KnowledgeItem) {
	logger.Printf("Knowledge item %s deleted from knowledge base %s", item.ID, item.KnowledgeBase.ID)
	
	deleteEmbedding(item)
}

func generateEmbedding(item *models.KnowledgeItem) {
	defer func() {
		if r := recover(); r != nil {
			logger.Printf("Recovered from panic in generateEmbedding: %v", r)
		}
	}()

	knowledgeModule, err := core.ImportPythonModule("apps.python_agent.kled.agent.knowledge")
	if err != nil {
		logger.Printf("Could not import knowledge module for knowledge item %s: %v", item.ID, err)
		return
	}

	generateEmbeddingFunc, err := knowledgeModule.GetAttr("generate_embedding")
	if err != nil {
		logger.Printf("Could not get generate_embedding function for knowledge item %s: %v", item.ID, err)
		return
	}

	_, err = generateEmbeddingFunc.Call(item)
	if err != nil {
		logger.Printf("Error generating embedding for knowledge item %s: %v", item.ID, err)
	}
}

func deleteEmbedding(item *models.KnowledgeItem) {
	defer func() {
		if r := recover(); r != nil {
			logger.Printf("Recovered from panic in deleteEmbedding: %v", r)
		}
	}()

	knowledgeModule, err := core.ImportPythonModule("apps.python_agent.kled.agent.knowledge")
	if err != nil {
		logger.Printf("Could not import knowledge module for knowledge item %s: %v", item.ID, err)
		return
	}

	deleteEmbeddingFunc, err := knowledgeModule.GetAttr("delete_embedding")
	if err != nil {
		logger.Printf("Could not get delete_embedding function for knowledge item %s: %v", item.ID, err)
		return
	}

	_, err = deleteEmbeddingFunc.Call(item)
	if err != nil {
		logger.Printf("Error deleting embedding for knowledge item %s: %v", item.ID, err)
	}
}

func init() {
	core.RegisterSignalHandler("post_save", "KnowledgeItem", HandleKnowledgeItemCreation)
	core.RegisterSignalHandler("pre_save", "KnowledgeItem", TrackKnowledgeItemChanges)
	core.RegisterSignalHandler("post_save", "KnowledgeBase", HandleKnowledgeBaseCreation)
	core.RegisterSignalHandler("post_delete", "KnowledgeItem", HandleKnowledgeItemDeletion)
}
