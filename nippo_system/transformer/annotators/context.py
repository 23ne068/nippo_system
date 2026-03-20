def resolve_activity(window_title):
    """
    ウィンドウタイトルから「何をしているか」の意味付けを行う。
    """
    title_lower = window_title.lower()
    
    # 判定ルール（カスタマイズ可能）
    rules = {
        "visual studio code": "Programming/Development",
        "cursor": "Programming/Development (AI Assisted)",
        "nippo": "Nippo Project Development",
        "antigravity": "Nippo Project Development",
        "google chrome": "Research/Browsing",
        "microsoft edge": "Research/Browsing",
        "slack": "Communication",
        "discord": "Communication",
        "cmd.exe": "Terminal/Command",
        "powershell": "Terminal/Command",
        "bash": "Terminal/Command",
        "notepad": "Note-taking",
        "excel": "Data Analysis/Documentation",
        "explorer": "File Management",
        "settings": "System Settings",
        "通知": "System Notification",
        "少なくなっています": "System Notification"
    }
    
    for key, category in rules.items():
        if key in title_lower:
            return category
            
    return "Other Activity"
