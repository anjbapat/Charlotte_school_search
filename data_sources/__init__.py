"""Official North Carolina school-data clients and canonical data management."""

from .data_manager import DataManager
from .models import DatasetResult, SourceMetadata

__all__ = ["DataManager", "DatasetResult", "SourceMetadata"]
