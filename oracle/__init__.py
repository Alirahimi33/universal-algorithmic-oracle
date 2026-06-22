"""Universal Algorithmic Oracle."""
import logging

logger = logging.getLogger("oracle")

from .logging_config import setup_logging
setup_logging()


def __getattr__(name: str):
    """Lazy-load OraclePipeline to avoid circular imports."""
    if name == "OraclePipeline":
        from .runtime.executor import OraclePipeline
        return OraclePipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["OraclePipeline", "list_systems", "compute_system"]


def list_systems():
    """List all available symbolic systems.
    
    Returns:
        List of system IDs that are registered and available.
    """
    from .symbolic.registry import list_systems
    return list_systems()


def compute_system(*args, **kwargs):
    """Compute output for a symbolic system.
    
    Args:
        *args: Arguments to pass to the system's compute method.
        **kwargs: Keyword arguments to pass to the system's compute method.
        
    Returns:
        SymbolicOutput with the computation results.
    """
    from .symbolic.registry import compute_system
    return compute_system(*args, **kwargs)
