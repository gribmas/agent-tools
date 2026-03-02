#!/usr/bin/env python3
"""
Discovery Poster - Quick way to post discoveries to the feed

Commands:
  discover post "title" "content"     - Post a discovery
  discover list                       - Show recent discoveries
  discover win "description"          - Quick win post
  discover insight "description"      - Quick insight post
  discover question "description"     - Quick question post
"""

import sys
import os
from datetime import datetime
from pathlib import Path

WORKSPACE_DIR = Path.home() / ".openclaw" / "workspace-subagent"
DISCOVERIES_FILE = WORKSPACE_DIR / "memory" / "blackboard" / "discoveries-feed.md"

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def get_date():
    return datetime.now().strftime("%Y-%m-%d")

def post_discovery(title, content, post_type="discovery"):
    """Post a new discovery to the feed"""
    
    if not DISCOVERIES_FILE.exists():
        # Create the file if it doesn't exist
        DISCOVERIES_FILE.parent.mkdir(parents=True, exist_ok=True)
        DISCOVERIES_FILE.write_text("# Discoveries Feed 🎯\n\n_A collaborative space for wins, insights, and strategic discussion_\n\n---\n")
    
    content_text = DISCOVERIES_FILE.read_text()
    
    # Type emoji mapping
    type_emoji = {
        "discovery": "🔍",
        "win": "🎉",
        "insight": "💡",
        "question": "🤔",
        "story": "📖",
        "discussion": "💭"
    }
    
    emoji = type_emoji.get(post_type.lower(), "✨")
    
    new_post = f"""
## {emoji} [{get_timestamp()}] {title}

**Type:** {post_type}

{content}

---

"""
    
    # Insert before the last marker or at end
    if "---\n\n_" in content_text:
        # Insert before the last section
        parts = content_text.rsplit("---\n\n_", 1)
        updated = parts[0] + new_post + "---\n\n_" + parts[1]
    else:
        updated = content_text + new_post
    
    DISCOVERIES_FILE.write_text(updated)
    print(f"✅ Posted: {title}")
    print(f"   Type: {post_type}")
    print(f"   File: {DISCOVERIES_FILE}")

def list_discoveries(limit=10):
    """Show recent discoveries"""
    if not DISCOVERIES_FILE.exists():
        print("❌ No discoveries feed found")
        return
    
    content = DISCOVERIES_FILE.read_text()
    
    # Find all post headers
    import re
    posts = re.findall(r'## ([🔍🎉💡🤔📖💭✨]+) \[([^\]]+)\] (.+)', content)
    
    print("🔍 RECENT DISCOVERIES")
    print("=" * 50)
    
    for emoji, timestamp, title in posts[:limit]:
        print(f"\n{emoji} {title}")
        print(f"   Posted: {timestamp}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "post":
        if len(sys.argv) < 4:
            print("Usage: discover post \"title\" \"content\" [type]")
            return
        title = sys.argv[2]
        content = sys.argv[3]
        post_type = sys.argv[4] if len(sys.argv) > 4 else "discovery"
        post_discovery(title, content, post_type)
    elif cmd == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        list_discoveries(limit)
    elif cmd == "win":
        if len(sys.argv) < 3:
            print("Usage: discover win \"description\"")
            return
        post_discovery("Quick Win! 🎉", sys.argv[2], "win")
    elif cmd == "insight":
        if len(sys.argv) < 3:
            print("Usage: discover insight \"description\"")
            return
        post_discovery("Quick Insight", sys.argv[2], "insight")
    elif cmd == "question":
        if len(sys.argv) < 3:
            print("Usage: discover question \"description\"")
            return
        post_discovery("Quick Question", sys.argv[2], "question")
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
