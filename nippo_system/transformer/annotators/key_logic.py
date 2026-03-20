import re

def reconstruct_typing(key_events):
    """
    生のキー情報（文字入力, Backspaceなど）から、
    最終的に入力された文字列と、「修正の激しさ」を推定する。
    """
    buffer = []
    backspace_count = 0
    total_keys = 0
    
    for ev in key_events:
        total_keys += 1
        # ev が辞書（{"key": "..."}）の場合と、単なる文字列の場合の両方に対応
        if isinstance(ev, dict):
            key = str(ev.get("key", ""))
        else:
            key = str(ev)
        
        # 特殊キーの判定
        if "Key.backspace" in key:
            backspace_count += 1
            if buffer:
                buffer.pop()
        elif "Key.space" in key:
            buffer.append(" ")
        elif "Key.enter" in key:
            buffer.append("\n")
        elif key == "\x16" or "\\x16" in key or "'\\x16'" in key: # Ctrl+V
            buffer.append(" [PASTE] ")
        elif key == "\x03" or "\\x03" in key or "'\\x03'" in key: # Ctrl+C
            buffer.append(" [COPY] ")
        elif key == "\x1a" or "\\x1a" in key or "'\\x1a'" in key: # Ctrl+Z
            buffer.append(" [UNDO] ")
        elif "Key." in key:
            continue
        else:
            char_match = re.search(r"'(.*?)'", key)
            if char_match:
                buffer.append(char_match.group(1))
            else:
                # 制御文字を除外
                if len(key) == 1 and ord(key) < 32 and key not in ["\n", "\r", "\t"]:
                    continue
                buffer.append(key)
                
    result_text = "".join(buffer)
    return {
        "text": result_text,
        "stats": {
            "total_keys": total_keys,
            "backspaces": backspace_count,
            "edit_intensity": round(backspace_count / (total_keys or 1), 2)
        }
    }

def identify_language(text):
    """
    入力されたテキストが日本語（マルチバイト）を含むか判定
    """
    if any(ord(c) > 127 for c in text):
        return "Japanese"
    return "English"
