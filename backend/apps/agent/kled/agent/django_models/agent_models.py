"""
Django models for the agent components.

This module provides Django models for the agent components, converting
the Pydantic models from the original implementation to Django models.
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
import json
import uuid
import os
from pathlib import Path

from apps.agent.kled.agent.types import Trajectory, TrajectoryStep


class AgentModel(models.Model):
    """Django model for agent model configuration."""
    
    name = models.CharField(max_length=255)
    temperature = models.FloatField(default=0.0)
    top_p = models.FloatField(default=1.0)
    api_base = models.CharField(max_length=255, null=True, blank=True)
    api_version = models.CharField(max_length=50, null=True, blank=True)
    api_key_env_var = models.CharField(max_length=100, null=True, blank=True, 
                                      help_text="Environment variable name for API key")
    stop_sequences = models.JSONField(default=list)
    completion_kwargs = models.JSONField(default=dict)
    convert_system_to_user = models.BooleanField(default=False)
    delay = models.FloatField(default=0.0)
    fallbacks = models.JSONField(default=list)
    choose_api_key_by_thread = models.BooleanField(default=True)
    max_input_tokens = models.IntegerField(null=True, blank=True)
    max_output_tokens = models.IntegerField(null=True, blank=True)
    
    per_instance_cost_limit = models.FloatField(default=3.0)
    total_cost_limit = models.FloatField(default=0.0)
    per_instance_call_limit = models.IntegerField(default=0)
    
    retry_count = models.IntegerField(default=20)
    retry_min_wait = models.FloatField(default=10.0)
    retry_max_wait = models.FloatField(default=120.0)
    
    model_type = models.CharField(
        max_length=50,
        choices=[
            ('generic', 'Generic API Model'),
            ('replay', 'Replay Model'),
            ('instant_empty_submit', 'Instant Empty Submit Model'),
            ('human', 'Human Model'),
            ('human_thought', 'Human Thought Model'),
        ],
        default='generic'
    )
    
    replay_path = models.CharField(max_length=255, null=True, blank=True)
    cost_per_call = models.FloatField(default=0.0, null=True, blank=True)
    
    class Meta:
        verbose_name = "Agent Model"
        verbose_name_plural = "Agent Models"
    
    def __str__(self):
        return f"{self.name} (t={self.temperature:.2f}, p={self.top_p:.2f})"
    
    @property
    def id_string(self):
        """Generate a unique ID for this model configuration."""
        return f"{self.name}__t-{self.temperature:.2f}__p-{self.top_p:.2f}__c-{self.per_instance_cost_limit:.2f}"
    
    def get_api_keys(self):
        """Returns a list of API keys from environment variables."""
        if not self.api_key_env_var:
            return []
        
        api_key = os.getenv(self.api_key_env_var, "")
        if not api_key:
            return []
        
        return api_key.split(":::")


class AgentStats(models.Model):
    """Django model for tracking agent statistics."""
    
    total_cost = models.FloatField(default=0.0)
    last_query_timestamp = models.FloatField(default=0.0)
    
    instance_cost = models.FloatField(default=0.0)
    tokens_sent = models.IntegerField(default=0)
    tokens_received = models.IntegerField(default=0)
    api_calls = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Agent Statistics"
        verbose_name_plural = "Agent Statistics"
    
    def __str__(self):
        return f"Stats: {self.instance_cost:.4f} USD, {self.api_calls} calls"


class AgentRun(models.Model):
    """Django model for tracking agent runs."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_model = models.ForeignKey(AgentModel, on_delete=models.CASCADE)
    stats = models.OneToOneField(AgentStats, on_delete=models.CASCADE)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    exit_status = models.CharField(max_length=100, null=True, blank=True)
    submission = models.TextField(null=True, blank=True)
    
    review_data = models.JSONField(null=True, blank=True)
    edited_files30 = models.TextField(null=True, blank=True)
    edited_files50 = models.TextField(null=True, blank=True)
    edited_files70 = models.TextField(null=True, blank=True)
    
    agent_version = models.CharField(max_length=100, null=True, blank=True)
    agent_hash = models.CharField(max_length=100, null=True, blank=True)
    framework_version = models.CharField(max_length=100, null=True, blank=True)
    framework_hash = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        verbose_name = "Agent Run"
        verbose_name_plural = "Agent Runs"
    
    def __str__(self):
        return f"Run {self.id} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"
    
    def mark_complete(self, exit_status=None, submission=None):
        """Mark the run as complete."""
        self.completed_at = timezone.now()
        self.exit_status = exit_status
        self.submission = submission
        self.save()
    
    def save_trajectory(self, trajectory: Trajectory, trajectory_id=None):
        """Save the trajectory for this run."""
        from apps.agent.trajectory_utils import trajectory_manager
        
        if trajectory_id is None:
            trajectory_id = f"run_{self.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        saved_id = trajectory_manager.save_trajectory(trajectory, trajectory_id)
        
        AgentTrajectory.objects.create(
            agent_run=self,
            trajectory_id=saved_id
        )
        
        return saved_id


class AgentTrajectory(models.Model):
    """Django model for tracking agent trajectories."""
    
    agent_run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name='trajectories')
    trajectory_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Agent Trajectory"
        verbose_name_plural = "Agent Trajectories"
    
    def __str__(self):
        return f"Trajectory {self.trajectory_id}"
    
    def load_trajectory(self) -> Trajectory:
        """Load the trajectory from the file system."""
        from apps.agent.trajectory_utils import trajectory_manager
        return trajectory_manager.load_trajectory(self.trajectory_id)


class AgentSession(models.Model):
    """Django model for tracking agent sessions."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    user_identifier = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        verbose_name = "Agent Session"
        verbose_name_plural = "Agent Sessions"
    
    def __str__(self):
        return f"Session {self.id}"


class AgentThread(models.Model):
    """Django model for tracking agent threads."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AgentSession, on_delete=models.CASCADE, related_name='threads')
    agent_run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Agent Thread"
        verbose_name_plural = "Agent Threads"
    
    def __str__(self):
        return f"Thread {self.id}"
    
    def stop(self):
        """Stop the thread."""
        self.is_active = False
        self.save()
