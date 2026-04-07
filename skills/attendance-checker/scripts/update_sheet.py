#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update Google Sheets attendance spreadsheet via gws CLI.
Usage: python3 update_sheet.py --sheet-id ID --date YYYY-MM-DD --attendance attendance.json [--roster roster.json]
"""
import json
import subprocess
import argparse
import sys

def get_existing_data(sheet_id):
    """Read existing sheet data."""
    result = subprocess.run([
        'gws', 'sheets', 'spreadsheets', 'values', 'get',
        '--params', json.dumps({
            'spreadsheetId': sheet_id,
            'range': '출석부!A1:ZZ1'
        })
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        return None
    
    try:
        data = json.loads(result.stdout)
        return data.get('values', [[]])[0]
    except:
        return None

def create_new_sheet(sheet_id, roster, date, attendance):
    """Create a new attendance sheet from scratch."""
    rows = [['조', '이름', '신청여부', date]]
    
    all_people = set()
    for item in roster:
        all_people.add((item['group'], item['name']))
    
    attended = set()
    for a in attendance['attendees']:
        g = int(a['group']) if a['group'] != '미배정' else 0
        attended.add((g, a['name']))
        all_people.add((g, a['name']))
    
    roster_set = set((item['group'], item['name']) for item in roster)
    
    for g, n in sorted(all_people):
        grp = str(g) if g > 0 else '미배정'
        registered = 'O' if (g, n) in roster_set else 'X'
        present = 'O' if (g, n) in attended else 'X'
        rows.append([grp, n, registered, present])
    
    return rows

def add_date_column(sheet_id, date, attendance):
    """Add a new date column to existing sheet."""
    # Read all existing data
    result = subprocess.run([
        'gws', 'sheets', 'spreadsheets', 'values', 'get',
        '--params', json.dumps({
            'spreadsheetId': sheet_id,
            'range': '출석부!A:ZZ'
        })
    ], capture_output=True, text=True)
    
    data = json.loads(result.stdout)
    existing = data.get('values', [])
    
    if not existing:
        return None
    
    # Build attendance lookup
    attended = set()
    for a in attendance['attendees']:
        attended.add((a['group'], a['name']))
    
    # Add new column
    header = existing[0]
    if date in header:
        col_idx = header.index(date)
    else:
        col_idx = len(header)
        header.append(date)
    
    new_rows = [header]
    for row in existing[1:]:
        while len(row) < len(header) - 1:
            row.append('')
        grp = row[0]
        name = row[1]
        present = 'O' if (grp, name) in attended else 'X'
        if len(row) <= col_idx:
            row.append(present)
        else:
            row[col_idx] = present
        new_rows.append(row)
    
    # Check for new attendees not in existing roster
    existing_people = set()
    for row in existing[1:]:
        if len(row) >= 2:
            existing_people.add((row[0], row[1]))
    
    for a in attendance['attendees']:
        key = (a['group'], a['name'])
        if key not in existing_people:
            new_row = [a['group'], a['name'], 'X']
            while len(new_row) < col_idx:
                new_row.append('')
            new_row.append('O')
            new_rows.append(new_row)
    
    return new_rows

def write_to_sheet(sheet_id, rows):
    """Write rows to sheet."""
    body = json.dumps({'values': rows}, ensure_ascii=False)
    result = subprocess.run([
        'gws', 'sheets', 'spreadsheets', 'values', 'update',
        '--params', json.dumps({
            'spreadsheetId': sheet_id,
            'range': '출석부!A1',
            'valueInputOption': 'RAW'
        }),
        '--json', body
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return False
    
    output = json.loads(result.stdout)
    print(json.dumps(output, indent=2))
    return True

def main():
    parser = argparse.ArgumentParser(description='Update attendance Google Sheet')
    parser.add_argument('--sheet-id', required=True, help='Google Sheets spreadsheet ID')
    parser.add_argument('--date', required=True, help='Session date (YYYY-MM-DD)')
    parser.add_argument('--attendance', required=True, help='Attendance JSON from parse_attendance.py')
    parser.add_argument('--roster', help='Roster JSON file (for new sheets)')
    parser.add_argument('--new', action='store_true', help='Create new sheet instead of adding column')
    args = parser.parse_args()
    
    with open(args.attendance, 'r', encoding='utf-8') as f:
        attendance = json.load(f)
    
    if args.new:
        roster = []
        if args.roster:
            with open(args.roster, 'r', encoding='utf-8') as f:
                roster = json.load(f)
        rows = create_new_sheet(args.sheet_id, roster, args.date, attendance)
    else:
        rows = add_date_column(args.sheet_id, args.date, attendance)
    
    if rows:
        write_to_sheet(args.sheet_id, rows)
    else:
        print("Error: could not build rows", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
