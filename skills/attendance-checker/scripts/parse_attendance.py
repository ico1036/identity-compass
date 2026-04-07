#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parse Zoom/meeting chat logs to extract attendance.
Input: chat text file (stdin or --file)
Output: JSON with attendees, stats, and anomalies.
"""
import re
import json
import sys
import argparse

def parse_chat(text):
    """Extract all participants and who wrote '출석'/'츌석'."""
    pattern = r'From\s+(.*?)\s*:'
    all_names = re.findall(pattern, text)
    
    participants = {}
    for raw in all_names:
        name = raw.strip()
        parsed = parse_group_name(name)
        if parsed:
            participants[parsed] = participants.get(parsed, 0) + 1

    # Find who explicitly checked in
    checked_in = set()
    for line in text.split('\n'):
        if re.search(r'(출석|츌석)', line) and 'From' in line:
            m = re.search(r'From\s+(.*?)\s*:', line)
            if m:
                parsed = parse_group_name(m.group(1).strip())
                if parsed:
                    checked_in.add(parsed)

    return participants, checked_in

def parse_group_name(raw):
    """Parse 'N조_이름' or 'N조 이름' into (group, name). Returns (0, name) for ungrouped."""
    m = re.match(r'(\d+)조[_\s]*(.*)', raw)
    if m:
        return (int(m.group(1)), m.group(2).strip())
    # Known special cases
    if 'iPhone' in raw:
        name = raw.split('의')[0].strip() if '의' in raw else raw
        return (0, name)
    if raw and not re.match(r'^(Reacted|Replying|Removed)', raw):
        return (0, raw)
    return None

def cross_check(participants, checked_in, roster=None):
    """Cross-check attendance against roster."""
    all_people = set(participants.keys())
    
    result = {
        'total_participants': len(all_people),
        'checked_in': len(checked_in),
        'chat_only': [],  # participated but didn't write 출석
        'attendees': [],  # final attendance list
    }
    
    chat_only = all_people - checked_in
    result['chat_only'] = [{'group': g, 'name': n} for g, n in sorted(chat_only)]
    
    # Include chat_only as attendees too (they were present)
    for g, n in sorted(all_people):
        grp = str(g) if g > 0 else '미배정'
        result['attendees'].append({
            'group': grp,
            'name': n,
            'explicit_checkin': (g, n) in checked_in,
            'message_count': participants.get((g, n), 0)
        })
    
    if roster:
        roster_set = set()
        for item in roster:
            roster_set.add((item['group'], item['name']))
        
        registered_attended = roster_set & all_people
        registered_absent = roster_set - all_people
        unregistered_attended = all_people - roster_set
        
        result['roster_stats'] = {
            'total_registered': len(roster_set),
            'registered_attended': len(registered_attended),
            'registered_absent': len(registered_absent),
            'unregistered_attended': len(unregistered_attended),
        }
        result['registered_absent'] = [{'group': g, 'name': n} for g, n in sorted(registered_absent)]
        result['unregistered_attended'] = [{'group': str(g) if g > 0 else '미배정', 'name': n} for g, n in sorted(unregistered_attended)]
    
    # Group stats
    group_counts = {}
    for g, n in all_people:
        if g > 0:
            group_counts[g] = group_counts.get(g, 0) + 1
    result['group_stats'] = {f'{g}조': cnt for g, cnt in sorted(group_counts.items())}
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Parse meeting chat for attendance')
    parser.add_argument('--file', '-f', help='Chat text file (default: stdin)')
    parser.add_argument('--roster', '-r', help='Roster JSON file (optional)')
    parser.add_argument('--include-chat-only', action='store_true', default=True,
                        help='Include chat-only participants as attendees (default: true)')
    args = parser.parse_args()
    
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    
    participants, checked_in = parse_chat(text)
    
    roster = None
    if args.roster:
        with open(args.roster, 'r', encoding='utf-8') as f:
            roster = json.load(f)
    
    result = cross_check(participants, checked_in, roster)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
