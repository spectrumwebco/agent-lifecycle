"""
Agent-related models for the python_agent app.

This module provides Django models for agent-related data,
which are stored in the agent database.
"""

from django.db import models
import uuid


class AgentModel(models.Model):
    """
    Model for an agent model configuration.
    
    This model represents a language model configuration for an agent.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    temperature = models.FloatField(default=0.0)
    top_p = models.FloatField(default=1.0)
    per_instance_cost_limit = models.FloatField(default=3.0)
    total_cost_limit = models.FloatField(default=0.0)
    per_instance_call_limit = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        agent_model = True
        db_table = 'agent_models'
        verbose_name = 'Agent Model'
        verbose_name_plural = 'Agent Models'
    
    def __str__(self):
        return f"{self.name} (T={self.temperature}, P={self.top_p})"


class AgentStats(models.Model):
    """
    Model for agent statistics.
    
    This model represents statistics for an agent run.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tokens_used = models.IntegerField(default=0)
    tokens_prompt = models.IntegerField(default=0)
    tokens_completion = models.IntegerField(default=0)
    cost = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        agent_model = True
        db_table = 'agent_stats'
        verbose_name = 'Agent Stats'
        verbose_name_plural = 'Agent Stats'
    
    def __str__(self):
        return f"Stats {self.id} (Tokens: {self.tokens_used}, Cost: ${self.cost:.2f})"


class AgentSession(models.Model):
    """
    Model for an agent session.
    
    This model represents a session for an agent.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        agent_model = True
        db_table = 'agent_sessions'
        verbose_name = 'Agent Session'
        verbose_name_plural = 'Agent Sessions'
    
    def __str__(self):
        return f"Session {self.id}"


class AgentThread(models.Model):
    """
    Model for an agent thread.
    
    This model represents a thread for an agent session.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AgentSession, on_delete=models.CASCADE, related_name='threads')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        agent_model = True
        db_table = 'agent_threads'
        verbose_name = 'Agent Thread'
        verbose_name_plural = 'Agent Threads'
    
    def __str__(self):
        return f"Thread {self.id}"


class AgentRun(models.Model):
    """
    Model for an agent run.
    
    This model represents a run of an agent.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_model = models.ForeignKey(AgentModel, on_delete=models.CASCADE, related_name='runs')
    stats = models.OneToOneField(AgentStats, on_delete=models.CASCADE, related_name='run')
    thread = models.ForeignKey(AgentThread, on_delete=models.SET_NULL, null=True, blank=True, related_name='runs')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    exit_status = models.CharField(max_length=255, null=True, blank=True)
    submission = models.TextField(null=True, blank=True)
    
    class Meta:
        agent_model = True
        db_table = 'agent_runs'
        verbose_name = 'Agent Run'
        verbose_name_plural = 'Agent Runs'
    
    def __str__(self):
        return f"Run {self.id}"
    
    def mark_complete(self, exit_status=None, submission=None):
        """
        Mark the run as complete.
        
        Args:
            exit_status: The exit status of the run
            submission: The submission of the run
        """
        from django.utils import timezone
        
        self.completed_at = timezone.now()
        self.exit_status = exit_status
        self.submission = submission
        self.save()
    
    def save_trajectory(self, trajectory):
        """
        Save the trajectory for the run.
        
        Args:
            trajectory: The trajectory to save
            
        Returns:
            str: The ID of the saved trajectory
        """
        from apps.agent.models.trajectory_models import Trajectory
        import json
        
        trajectory_obj = Trajectory.objects.create(
            agent_run=self,
            data=json.dumps(trajectory)
        )
        
        return str(trajectory_obj.id)
