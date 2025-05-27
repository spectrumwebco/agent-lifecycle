"""
Abstract deployment module for SWE-ReX.
"""

class AbstractDeployment:
    """Abstract deployment class for SWE-ReX."""
    
    def __init__(self, config=None):
        """Initialize the deployment."""
        self.config = config or {}
    
    def deploy(self):
        """Deploy the application."""
        raise NotImplementedError("Subclasses must implement deploy()")
    
    def undeploy(self):
        """Undeploy the application."""
        raise NotImplementedError("Subclasses must implement undeploy()")
