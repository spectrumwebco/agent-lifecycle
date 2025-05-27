"""
Trajectory-related models for the python_agent app.

This module provides Django models for trajectory-related data,
which are stored in the trajectory database.
"""

from django.db import models
import uuid
import json


class Trajectory(models.Model):
    """
    Model for a trajectory.
    
    This model represents a trajectory for an agent run.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_run_id = models.UUIDField(null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    data = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        trajectory_model = True
        db_table = 'trajectories'
        verbose_name = 'Trajectory'
        verbose_name_plural = 'Trajectories'
    
    def __str__(self):
        return f"Trajectory {self.id}"
    
    @property
    def agent_run(self):
        """
        Get the agent run for the trajectory.
        
        Returns:
            AgentRun: The agent run for the trajectory
        """
        from apps.agent.models.agent_models import AgentRun
        
        if not self.agent_run_id:
            return None
        
        try:
            return AgentRun.objects.get(id=self.agent_run_id)
        except AgentRun.DoesNotExist:
            return None
    
    @property
    def data_json(self):
        """
        Get the trajectory data as JSON.
        
        Returns:
            dict: The trajectory data as JSON
        """
        try:
            return json.loads(self.data)
        except json.JSONDecodeError:
            return {}
    
    def save_to_file(self, file_path):
        """
        Save the trajectory data to a file.
        
        Args:
            file_path: The path to save the trajectory data to
            
        Returns:
            bool: True if the trajectory data was saved successfully, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(self.data_json, f, indent=2)
            return True
        except Exception:
            return False


class TrajectoryMetadata(models.Model):
    """
    Model for trajectory metadata.
    
    This model represents metadata for a trajectory.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trajectory = models.OneToOneField(Trajectory, on_delete=models.CASCADE, related_name='metadata')
    problem_statement = models.TextField(null=True, blank=True)
    repository = models.CharField(max_length=255, null=True, blank=True)
    model_name = models.CharField(max_length=255, null=True, blank=True)
    exit_status = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        trajectory_model = True
        db_table = 'trajectory_metadata'
        verbose_name = 'Trajectory Metadata'
        verbose_name_plural = 'Trajectory Metadata'
    
    def __str__(self):
        return f"Metadata for {self.trajectory}"


class TrajectoryTag(models.Model):
    """
    Model for a trajectory tag.
    
    This model represents a tag for a trajectory.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        trajectory_model = True
        db_table = 'trajectory_tags'
        verbose_name = 'Trajectory Tag'
        verbose_name_plural = 'Trajectory Tags'
    
    def __str__(self):
        return self.name


class TrajectoryTagAssociation(models.Model):
    """
    Model for a trajectory tag association.
    
    This model represents an association between a trajectory and a tag.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trajectory = models.ForeignKey(Trajectory, on_delete=models.CASCADE, related_name='tag_associations')
    tag = models.ForeignKey(TrajectoryTag, on_delete=models.CASCADE, related_name='trajectory_associations')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        trajectory_model = True
        db_table = 'trajectory_tag_associations'
        verbose_name = 'Trajectory Tag Association'
        verbose_name_plural = 'Trajectory Tag Associations'
        unique_together = ('trajectory', 'tag')
    
    def __str__(self):
        return f"{self.trajectory} - {self.tag}"
