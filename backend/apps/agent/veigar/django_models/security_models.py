"""
Django models for the Veigar cybersecurity agent.

This module provides Django models for storing security vulnerabilities,
compliance issues, and security review results.
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.agent.kled.agent.django_models.agent_models import AgentRun

User = get_user_model()


class SecurityFramework(models.Model):
    """Security framework model."""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=50, blank=True)
    url = models.URLField(blank=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class SecurityTool(models.Model):
    """Security tool model."""
    
    TOOL_TYPES = (
        ('static', 'Static Analysis'),
        ('dynamic', 'Dynamic Analysis'),
        ('dependency', 'Dependency Scanning'),
        ('container', 'Container Scanning'),
        ('network', 'Network Scanning'),
        ('compliance', 'Compliance Checking'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    tool_type = models.CharField(max_length=20, choices=TOOL_TYPES)
    source_repo = models.CharField(max_length=255, blank=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class SecurityVulnerability(models.Model):
    """Security vulnerability model."""
    
    SEVERITY_LEVELS = (
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('info', 'Info'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    cve = models.CharField(max_length=50, blank=True, null=True)
    cwe = models.CharField(max_length=50, blank=True, null=True)
    file_path = models.CharField(max_length=255, blank=True)
    line_number = models.CharField(max_length=10, blank=True)
    evidence = models.TextField(blank=True)
    remediation = models.TextField(blank=True)
    tool = models.ForeignKey(SecurityTool, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.severity})"


class ComplianceIssue(models.Model):
    """Compliance issue model."""
    
    SEVERITY_LEVELS = (
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('info', 'Info'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    category = models.CharField(max_length=100)
    issue_id = models.CharField(max_length=50)
    remediation = models.TextField(blank=True)
    framework = models.ForeignKey(SecurityFramework, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.framework.name} - {self.title} ({self.severity})"


class SecurityReview(models.Model):
    """Security review model."""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    SEVERITY_LEVELS = (
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('none', 'None'),
    )
    
    repository = models.CharField(max_length=255)
    branch = models.CharField(max_length=255)
    pr_id = models.CharField(max_length=50)
    pr_title = models.CharField(max_length=255, blank=True)
    pr_author = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    severity_level = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='none')
    summary = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    agent_run = models.ForeignKey(AgentRun, on_delete=models.SET_NULL, null=True, blank=True)
    vulnerabilities = models.ManyToManyField(SecurityVulnerability, blank=True)
    compliance_issues = models.ManyToManyField(ComplianceIssue, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Security Review for {self.repository}:{self.branch} (PR #{self.pr_id})"
    
    def mark_completed(self, severity_level='none', summary=''):
        """Mark the security review as completed."""
        self.status = 'completed'
        self.severity_level = severity_level
        self.summary = summary
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message=''):
        """Mark the security review as failed."""
        self.status = 'failed'
        self.summary = f"Review failed: {error_message}"
        self.completed_at = timezone.now()
        self.save()
    
    @property
    def total_vulnerabilities(self):
        """Get the total number of vulnerabilities."""
        return self.vulnerabilities.count()
    
    @property
    def total_compliance_issues(self):
        """Get the total number of compliance issues."""
        return self.compliance_issues.count()
    
    @property
    def is_compliant(self):
        """Check if the review is compliant."""
        return self.severity_level in ['none', 'low']
