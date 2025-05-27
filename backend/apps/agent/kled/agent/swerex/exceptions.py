"""
Mock swerex exceptions module for local development.
"""

class SwerexException(Exception):
    """Base exception for all swerex exceptions."""
    pass

class BashIncorrectSyntaxError(SwerexException):
    """Raised when bash syntax is incorrect."""
    pass

class CommandTimeoutError(SwerexException):
    """Raised when a command times out."""
    pass
