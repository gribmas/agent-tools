#!/usr/bin/env python3
"""
Blackboard CLI - Fast agent coordination tool

Commands:
  bb status          - Show ecosystem health
  bb now             - THE ONE thing to do right now
  bb signals         - List active signals (with priority)
  bb post "message"  - Post a signal to the blackboard
  bb mailbox <agent> - Read your mailbox
  bb nudge <agent>   - Send a nudge to another agent
  bb actions         - Extract all actionable items from signals
  bb recent          - Show recent activity summary
  bb summary         - Quick 5-line ecosystem overview
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path
import re

BLACKBOARD_DIR = Path.home() / ".openclaw" / "workspace-subagent" / "memory" / "blackboard"
WORKSPACE_DIR = Path.home() / ".openclaw" / "workspace-subagent"

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def parse_frontmatter(content):
    """Extract signal metadata from content"""
    lines = content.split('\n')
    meta = {}
    for line in lines[:20]:  # Check first 20 lines
        if line.startswith('- **From:**'):
            meta['from'] = line.split('**From:**')[1].strip()
        elif line.startswith('- **Posted:**'):
            meta['posted'] = line.split('**Posted:**')[1].strip()
        elif line.startswith('- **Priority:**'):
            meta['priority'] = line.split('**Priority:**')[1].strip()
        elif line.startswith('- **Summary:**'):
            meta['summary'] = line.split('**Summary:**')[1].strip()[:100]
        elif line.startswith('- **Needed from:**'):
            meta['needed'] = line.split('**Needed from:**')[1].strip()
    return meta

def cmd_status():
    """Show ecosystem status"""
    status_file = BLACKBOARD_DIR / "ecosystem-status.md"
    if not status_file.exists():
        print("❌ No ecosystem status found")
        return
    
    content = status_file.read_text()
    
    # Extract key info
    health_match = re.search(r'\*\*Health Check:\*\* (.+)', content)
    last_check = re.search(r'\*\*Last Check:\*\* (.+)', content)
    one_thing = re.search(r'\*\*The ONE Thing:\*\* (.+)', content)
    two_things = re.search(r'\*\*The TWO Things.*?\*\* (.+)', content)
    
    print("📊 ECOSYSTEM STATUS")
    print("=" * 50)
    
    if health_match:
        health = health_match.group(1)
        # Add color based on status
        if '🟢' in health or 'HEALTHY' in health.upper():
            print(f"Health: {health}")
        elif '🟡' in health:
            print(f"Health: {health}")
        else:
            print(f"Health: {health}")
    
    if last_check:
        print(f"Last Check: {last_check.group(1)}")
    
    print()
    
    if two_things:
        print("🎯 PRIORITY ACTIONS:")
        # Find both things
        things_section = re.search(r'\*\*The TWO Things.*?\n(.+?)\n\d\.\s+\*\*IMMEDIATE:\*\*\s+(.+?)\n\d\.\s+\*\*PRIMARY:\*\*\s+(.+?)(?:\n|$)', content, re.DOTALL)
        if things_section:
            print(f"  1. IMMEDIATE: {things_section.group(2)}")
            print(f"  2. PRIMARY: {things_section.group(3)}")
    elif one_thing:
        print(f"🎯 THE ONE THING: {one_thing.group(1)}")
    
    # Count signals
    signals_file = BLACKBOARD_DIR / "action-signals.md"
    if signals_file.exists():
        sig_content = signals_file.read_text()
        high_count = sig_content.count('**Priority:** HIGH')
        medium_count = sig_content.count('**Priority:** MEDIUM')
        print(f"\n📋 Signals: {high_count} HIGH / {medium_count} MEDIUM priority")

def cmd_signals(priority_filter=None):
    """List active signals"""
    signals_file = BLACKBOARD_DIR / "action-signals.md"
    if not signals_file.exists():
        print("❌ No signals file found")
        return
    
    content = signals_file.read_text()
    
    # Split into signal blocks
    signals = re.split(r'### SIGNAL:', content)[1:]  # Skip header
    
    print("📡 ACTIVE SIGNALS")
    print("=" * 50)
    
    count = 0
    for sig in signals[:10]:  # Show top 10
        lines = sig.strip().split('\n')
        title = lines[0].strip() if lines else "Unknown"
        
        meta = parse_frontmatter("### SIGNAL:" + sig)
        
        priority = meta.get('priority', 'UNKNOWN')
        
        # Filter by priority if specified
        if priority_filter and priority_filter.upper() not in priority.upper():
            continue
        
        # Priority emoji
        p_emoji = {'HIGH': '🔴', 'MEDIUM-HIGH': '🟠', 'MEDIUM': '🟡'}.get(priority.upper(), '⚪')
        
        print(f"\n{p_emoji} {title}")
        print(f"   From: {meta.get('from', 'unknown')}")
        print(f"   Priority: {priority}")
        if 'summary' in meta:
            print(f"   Summary: {meta['summary']}...")
        
        count += 1
        if count >= 10:
            print(f"\n   ... and {len(signals) - 10} more signals")
            break

def cmd_post(message, signal_type="GENERAL", priority="MEDIUM", from_agent="unknown"):
    """Post a new signal"""
    signals_file = BLACKBOARD_DIR / "action-signals.md"
    
    if not signals_file.exists():
        print("❌ No signals file found")
        return
    
    content = signals_file.read_text()
    
    # Create new signal entry
    new_signal = f"""
### SIGNAL: {signal_type} (NEW)
- **From:** {from_agent}
- **Posted:** {get_timestamp()}
- **Priority:** {priority}
- **Summary:** {message}
- **Needed from:** Action or response requested
- **Expires:** When addressed

"""
    
    # Insert after "## Active Signals"
    if "## Active Signals" in content:
        parts = content.split("## Active Signals", 1)
        updated = parts[0] + "## Active Signals" + new_signal + parts[1]
    else:
        updated = content + new_signal
    
    signals_file.write_text(updated)
    print(f"✅ Signal posted: {signal_type}")
    print(f"   Priority: {priority}")
    print(f"   Message: {message[:100]}...")

def cmd_mailbox(agent_name):
    """Read an agent's mailbox"""
    mailbox_file = BLACKBOARD_DIR / "mailboxes" / f"{agent_name}.md"
    
    if not mailbox_file.exists():
        # Try legacy location
        mailbox_file = BLACKBOARD_DIR / f"mailbox-{agent_name}.md"
    
    if not mailbox_file.exists():
        print(f"❌ No mailbox found for {agent_name}")
        print(f"   Create one at: blackboard/mailboxes/{agent_name}.md")
        return
    
    content = mailbox_file.read_text()
    print(f"📬 MAILBOX: {agent_name}")
    print("=" * 50)
    
    # Extract messages
    messages = re.split(r'### ', content)[1:]
    
    for msg in messages[:5]:
        lines = msg.strip().split('\n')
        title = lines[0] if lines else "Unknown"
        print(f"\n📥 {title}")
        
        # Get first few lines of content
        for line in lines[1:6]:
            if line.strip() and not line.startswith('**'):
                print(f"   {line[:80]}")

def cmd_nudge(to_agent, message):
    """Send a nudge to another agent's mailbox"""
    mailbox_dir = BLACKBOARD_DIR / "mailboxes"
    mailbox_dir.mkdir(exist_ok=True)
    
    mailbox_file = mailbox_dir / f"{to_agent}.md"
    
    # Create if doesn't exist
    if not mailbox_file.exists():
        mailbox_file.write_text(f"# Mailbox: {to_agent}\n\n## Messages\n\n")
    
    content = mailbox_file.read_text()
    
    nudge = f"""
### Nudge - {get_timestamp()}
**From:** CLI User
**Type:** nudge

{message}

---

"""
    
    # Insert before last section or at end
    if "## Messages" in content:
        parts = content.split("## Messages", 1)
        updated = parts[0] + "## Messages" + nudge + parts[1]
    else:
        updated = content + nudge
    
    mailbox_file.write_text(updated)
    print(f"✅ Nudge sent to {to_agent}")
    print(f"   Message: {message[:100]}...")

def cmd_actions():
    """Extract actionable items from all signals"""
    signals_file = BLACKBOARD_DIR / "action-signals.md"
    if not signals_file.exists():
        print("❌ No signals file found")
        return
    
    content = signals_file.read_text()
    
    # Find all "Needed from:" lines
    needed = re.findall(r'\*\*Needed from:\*\* (.+)', content)
    
    print("🎯 ACTIONABLE ITEMS")
    print("=" * 50)
    
    # Also get priorities
    priorities = re.findall(r'\*\*Priority:\*\* (.+)', content)
    summaries = re.findall(r'\*\*Summary:\*\* (.+)', content)
    
    # Combine into prioritized list
    actions = list(zip(priorities, summaries, needed))
    
    # Sort by priority
    def priority_sort(a):
        p = a[0].upper()
        if 'HIGH' in p and 'MEDIUM' not in p:
            return 0
        elif 'MEDIUM-HIGH' in p:
            return 1
        elif 'MEDIUM' in p:
            return 2
        return 3
    
    actions.sort(key=priority_sort)
    
    for i, (priority, summary, action) in enumerate(actions[:15], 1):
        p_emoji = {'HIGH': '🔴', 'MEDIUM-HIGH': '🟠', 'MEDIUM': '🟡'}.get(priority.upper(), '⚪')
        print(f"\n{i}. {p_emoji} [{priority}]")
        print(f"   Action: {action[:120]}")

def cmd_recent():
    """Show recent activity"""
    status_file = BLACKBOARD_DIR / "ecosystem-status.md"
    if not status_file.exists():
        print("❌ No ecosystem status found")
        return
    
    content = status_file.read_text()
    
    print("📜 RECENT ACTIVITY")
    print("=" * 50)
    
    # Extract recent subagent activity table
    if "## Recent Subagent Activity" in content:
        section = content.split("## Recent Subagent Activity")[1].split("##")[0]
        
        # Parse table rows
        rows = re.findall(r'\| (.+?) \| (.+?) \| (.+?) \| (.+?) \|', section)
        
        for session, task, duration, outcome in rows[:10]:
            if session.strip() and not session.startswith('-'):
                print(f"\n🤖 {session}")
                print(f"   Task: {task}")
                print(f"   Duration: {duration}")
                print(f"   Outcome: {outcome[:60]}...")

def cmd_now():
    """Show THE ONE thing to do right now"""
    status_file = BLACKBOARD_DIR / "ecosystem-status.md"
    if not status_file.exists():
        print("❌ No ecosystem status found")
        return
    
    content = status_file.read_text()
    
    # Find the ONE thing or TWO things
    one_thing = re.search(r'\*\*The ONE Thing:\*\* (.+)', content)
    two_things = re.search(r'\*\*The TWO Things.*?\*\* (.+?)\n\d\.\s+\*\*IMMEDIATE:\*\*\s+(.+?)\n\d\.\s+\*\*PRIMARY:\*\*\s+(.+?)(?:\n|$)', content, re.DOTALL)
    
    print("🎯 DO THIS NOW")
    print("=" * 50)
    
    if two_things:
        print(f"\n🔴 IMMEDIATE: {two_things.group(2)}")
        print(f"\n🟡 PRIMARY: {two_things.group(3)}")
    elif one_thing:
        print(f"\n🎯 {one_thing.group(1)}")
    else:
        # Fall back to top action
        signals_file = BLACKBOARD_DIR / "action-signals.md"
        if signals_file.exists():
            sig_content = signals_file.read_text()
            first_high = re.search(r'### SIGNAL: (.+?)\n.*?\*\*Priority:\*\* HIGH.*?\*\*Needed from:\*\* (.+)', sig_content, re.DOTALL)
            if first_high:
                print(f"\n🔴 {first_high.group(1)}")
                print(f"   {first_high.group(2)[:100]}")

def cmd_summary():
    """Quick 5-line ecosystem overview"""
    status_file = BLACKBOARD_DIR / "ecosystem-status.md"
    signals_file = BLACKBOARD_DIR / "action-signals.md"
    
    if not status_file.exists():
        print("❌ No ecosystem status found")
        return
    
    content = status_file.read_text()
    
    # Extract key metrics
    health = re.search(r'\*\*Health Check:\*\* (.+?)—', content)
    if not health:
        health = re.search(r'\*\*Health Check:\*\* (.+)', content)
    
    signals_count = 0
    high_count = 0
    if signals_file.exists():
        sig_content = signals_file.read_text()
        signals_count = sig_content.count('### SIGNAL:')
        high_count = sig_content.count('**Priority:** HIGH')
    
    last_check = re.search(r'\*\*Last Check:\*\* ([^—\n]+)', content)
    
    # Print compact summary
    print("📊 ECOSYSTEM SUMMARY")
    print("=" * 50)
    if health:
        health_text = health.group(1).strip()
        print(f"Health: {health_text[:60]}...")
    print(f"Signals: {signals_count} total, {high_count} HIGH priority")
    if last_check:
        print(f"Last update: {last_check.group(1).strip()}")
    
    # ONE thing
    one_thing = re.search(r'\*\*The ONE Thing:\*\* (.+)', content)
    if one_thing:
        print(f"\n🎯 {one_thing.group(1)[:80]}...")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "status":
        cmd_status()
    elif cmd == "now":
        cmd_now()
    elif cmd == "summary":
        cmd_summary()
    elif cmd == "signals":
        priority = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_signals(priority)
    elif cmd == "post":
        if len(sys.argv) < 3:
            print("Usage: bb post \"message\" [priority] [from_agent]")
            return
        message = sys.argv[2]
        priority = sys.argv[3] if len(sys.argv) > 3 else "MEDIUM"
        from_agent = sys.argv[4] if len(sys.argv) > 4 else "cli-user"
        cmd_post(message, "CLI Signal", priority, from_agent)
    elif cmd == "mailbox":
        if len(sys.argv) < 3:
            print("Usage: bb mailbox <agent_name>")
            return
        cmd_mailbox(sys.argv[2])
    elif cmd == "nudge":
        if len(sys.argv) < 4:
            print("Usage: bb nudge <agent> \"message\"")
            return
        cmd_nudge(sys.argv[2], sys.argv[3])
    elif cmd == "actions":
        cmd_actions()
    elif cmd == "recent":
        cmd_recent()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
