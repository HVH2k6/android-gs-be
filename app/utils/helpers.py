"""
Utility functions
"""
import hashlib
from datetime import datetime
from typing import Optional


def generate_fingerprint(rule_id: str, scope: str, node: str) -> str:
    """
    Generate stable issue fingerprint based on AST information
    Does not use line numbers (which change when code is edited)
    """
    fingerprint_string = f"{rule_id}:{scope}:{node}"
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:16]


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def calculate_resolution_time(detected_at: datetime, resolved_at: Optional[datetime]) -> Optional[int]:
    """Calculate time to resolve an issue in seconds"""
    if not resolved_at:
        return None
    return int((resolved_at - detected_at).total_seconds())
