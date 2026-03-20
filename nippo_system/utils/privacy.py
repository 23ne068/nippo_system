from ..config import SENSITIVE_APP_NAMES

def is_sensitive_window(title):
    """
    Check if the window title contains any sensitive keywords.
    """
    if not title:
        return False
    
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in SENSITIVE_APP_NAMES)
