"""
Nodetree related exceptions.
"""


class ExternalToolError(StandardError):
    """Errors with external command-line tools etc."""


class AbortedAction(StandardError):
    """Exception to raise when execution is aborted."""


class ImproperlyConfigured(StandardError):
    """Something is configured wrong"""

