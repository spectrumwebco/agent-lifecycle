package serializers

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type IssueLabelSerializer struct {
	core.Serializer
}

func NewIssueLabelSerializer() *IssueLabelSerializer {
	serializer := &IssueLabelSerializer{
		Serializer: core.NewSerializer("IssueLabel"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "color", "organization",
		"organization_name", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")

	return serializer
}

type IssueAttachmentSerializer struct {
	core.Serializer
}

func NewIssueAttachmentSerializer() *IssueAttachmentSerializer {
	serializer := &IssueAttachmentSerializer{
		Serializer: core.NewSerializer("IssueAttachment"),
	}

	serializer.SetFields([]string{
		"id", "issue", "issue_title", "filename", "file", "file_size",
		"content_type", "uploaded_by", "uploaded_by_username", "created_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "issue_title", "uploaded_by_username", "file_size",
	})
	
	serializer.AddReadOnlyField("issue_title", "issue.title")
	serializer.AddReadOnlyField("uploaded_by_username", "uploaded_by.username")

	return serializer
}

type IssueCommentSerializer struct {
	core.Serializer
}

func NewIssueCommentSerializer() *IssueCommentSerializer {
	serializer := &IssueCommentSerializer{
		Serializer: core.NewSerializer("IssueComment"),
	}

	serializer.SetFields([]string{
		"id", "issue", "issue_title", "content", "author",
		"author_username", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "issue_title", "author_username",
	})
	
	serializer.AddReadOnlyField("issue_title", "issue.title")
	serializer.AddReadOnlyField("author_username", "author.username")

	return serializer
}

type IssueRelationshipSerializer struct {
	core.Serializer
}

func NewIssueRelationshipSerializer() *IssueRelationshipSerializer {
	serializer := &IssueRelationshipSerializer{
		Serializer: core.NewSerializer("IssueRelationship"),
	}

	serializer.SetFields([]string{
		"id", "source_issue", "source_issue_title", "relationship_type",
		"target_issue", "target_issue_title", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "source_issue_title", "target_issue_title",
	})
	
	serializer.AddReadOnlyField("source_issue_title", "source_issue.title")
	serializer.AddReadOnlyField("target_issue_title", "target_issue.title")

	return serializer
}

type IssueSerializer struct {
	core.Serializer
}

func NewIssueSerializer() *IssueSerializer {
	serializer := &IssueSerializer{
		Serializer: core.NewSerializer("Issue"),
	}

	serializer.SetFields([]string{
		"id", "title", "description", "issue_type", "status", "priority",
		"organization", "organization_name", "reporter", "reporter_username",
		"assignee", "assignee_username", "labels", "due_date", "estimated_time",
		"actual_time", "comments_count", "attachments_count", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name",
		"reporter_username", "assignee_username", "comments_count", "attachments_count",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("reporter_username", "reporter.username")
	serializer.AddReadOnlyField("assignee_username", "assignee.username")
	serializer.AddNestedSerializer("labels", NewIssueLabelSerializer(), true)
	serializer.AddMethodField("comments_count", "GetCommentsCount")
	serializer.AddMethodField("attachments_count", "GetAttachmentsCount")

	return serializer
}

func (s *IssueSerializer) GetCommentsCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "comments.count")
}

func (s *IssueSerializer) GetAttachmentsCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "attachments.count")
}

func init() {
	core.RegisterSerializer("IssueLabelSerializer", NewIssueLabelSerializer())
	core.RegisterSerializer("IssueAttachmentSerializer", NewIssueAttachmentSerializer())
	core.RegisterSerializer("IssueCommentSerializer", NewIssueCommentSerializer())
	core.RegisterSerializer("IssueRelationshipSerializer", NewIssueRelationshipSerializer())
	core.RegisterSerializer("IssueSerializer", NewIssueSerializer())
}
