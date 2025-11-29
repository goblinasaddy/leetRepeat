import sqlite3
import datetime
import json
import pandas as pd

DB_FILE = "leetrepeat.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    with open("db_schema.sql", "r") as f:
        schema = f.read()
    conn.executescript(schema)
    
    # Initialize default config if not exists
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key='intervals'")
    if not cursor.fetchone():
        default_intervals = json.dumps([1, 2, 3, 5, 9, 15, 20, 30, 60])
        cursor.execute("INSERT INTO config (key, value) VALUES (?, ?)", ('intervals', default_intervals))
    
    cursor.execute("SELECT value FROM config WHERE key='day1_behavior'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO config (key, value) VALUES (?, ?)", ('day1_behavior', 'next_day')) # or 'same_day'
        
    cursor.execute("SELECT value FROM config WHERE key='fail_behavior'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO config (key, value) VALUES (?, ?)", ('fail_behavior', 'short_repeat')) # or 'restart'

    conn.commit()
    conn.close()

def get_config(key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key=?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row['value']
    return None

def set_config(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def add_problem(problem_id, title, difficulty, tags, date_added=None):
    if date_added is None:
        date_added = datetime.date.today()
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO problems (problem_id, title, difficulty, tags, date_added) VALUES (?, ?, ?, ?, ?)",
            (problem_id, title, difficulty, tags, date_added)
        )
        
        # Schedule revisions
        intervals = json.loads(get_config('intervals'))
        day1_behavior = get_config('day1_behavior')
        
        for i, days in enumerate(intervals):
            if i == 0 and day1_behavior == 'same_day':
                due_date = date_added
            else:
                due_date = date_added + datetime.timedelta(days=days)
            
            cursor.execute(
                "INSERT INTO revisions (problem_id, due_date, status) VALUES (?, ?, 'pending')",
                (problem_id, due_date)
            )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_due_revisions(date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, p.title, p.difficulty, p.tags, p.date_added as original_date
        FROM revisions r
        JOIN problems p ON r.problem_id = p.problem_id
        WHERE r.due_date <= ? AND r.status = 'pending'
        ORDER BY r.due_date ASC
    """, (date,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_problems_df():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM problems", conn)
    conn.close()
    return df

def get_revisions_df():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM revisions", conn)
    conn.close()
    return df

def get_history_df():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM history", conn)
    conn.close()
    return df

def mark_revision_done(revision_id, problem_id, date_completed, quality=None, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE revisions SET status='done', date_completed=?, notes=? WHERE id=?",
        (date_completed, notes, revision_id)
    )
    
    # Add history
    cursor.execute(
        "INSERT INTO history (problem_id, date, result, quality, notes) VALUES (?, ?, 'solved', ?, ?)",
        (problem_id, date_completed, quality, notes)
    )
    conn.commit()
    conn.close()

def mark_revision_failed(revision_id, problem_id, date_failed):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Record failure in history
    cursor.execute(
        "INSERT INTO history (problem_id, date, result, quality) VALUES (?, ?, 'failed', 0)",
        (problem_id, date_failed)
    )
    
    fail_behavior = get_config('fail_behavior')
    
    if fail_behavior == 'restart':
        # Delete future pending revisions
        cursor.execute("DELETE FROM revisions WHERE problem_id=? AND status='pending' AND due_date > ?", (problem_id, date_failed))
        # Re-schedule from today
        intervals = json.loads(get_config('intervals'))
        for days in intervals:
            due_date = date_failed + datetime.timedelta(days=days)
            cursor.execute(
                "INSERT INTO revisions (problem_id, due_date, status) VALUES (?, ?, 'pending')",
                (problem_id, due_date)
            )
        # Mark current revision as skipped or just leave it? 
        # The prompt says "move that problem to restart". 
        # Usually we mark the current one as done/failed or just delete it.
        # Let's mark the current revision as 'skipped' (since we failed it and are restarting)
        cursor.execute("UPDATE revisions SET status='skipped' WHERE id=?", (revision_id,))

    else: # short_repeat (default)
        # Insert a short repeat revision today + 2 days
        due_date = date_failed + datetime.timedelta(days=2)
        cursor.execute(
            "INSERT INTO revisions (problem_id, due_date, status) VALUES (?, ?, 'pending')",
            (problem_id, due_date)
        )
        # Keep the current revision as pending? No, we failed it.
        # The prompt says "If a revision day passes without completion, keep it pending".
        # But here we explicitly clicked fail.
        # So we should probably mark this specific revision instance as 'done' (but failed) or 'skipped'.
        # Since we have a history entry for failure, let's mark this revision row as 'done' (completed the attempt) 
        # or maybe we should just leave it?
        # If we leave it pending, it will show up again.
        # Let's mark it as 'done' so it clears from the list, but the history records the failure.
        cursor.execute("UPDATE revisions SET status='done', date_completed=? WHERE id=?", (date_failed, revision_id))

    conn.commit()
    conn.close()

def snooze_revision(revision_id, days):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT due_date FROM revisions WHERE id=?", (revision_id,))
    row = cursor.fetchone()
    if row:
        current_due = datetime.datetime.strptime(row['due_date'], '%Y-%m-%d').date()
        new_due = current_due + datetime.timedelta(days=days)
        cursor.execute("UPDATE revisions SET due_date=? WHERE id=?", (new_due, revision_id))
    conn.commit()
    conn.close()

def get_counts_per_day(year, month):
    # Return a dictionary of date -> count of pending revisions
    # This is for the calendar view
    start_date = datetime.date(year, month, 1)
    if month == 12:
        end_date = datetime.date(year + 1, 1, 1)
    else:
        end_date = datetime.date(year, month + 1, 1)
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT due_date, COUNT(*) as count
        FROM revisions
        WHERE status='pending' AND due_date >= ? AND due_date < ?
        GROUP BY due_date
    """, (start_date, end_date))
    rows = cursor.fetchall()
    conn.close()
    return {row['due_date']: row['count'] for row in rows}

def get_analytics_stats():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total problems
    cursor.execute("SELECT COUNT(*) FROM problems")
    total_problems = cursor.fetchone()[0]
    
    # Total solved (unique problems solved at least once)
    cursor.execute("SELECT COUNT(DISTINCT problem_id) FROM history WHERE result='solved'")
    total_solved = cursor.fetchone()[0]
    
    # Streak (consecutive days with at least one solved)
    # This is a bit complex in SQL, might be easier in Python with pandas
    conn.close()
    
    return {
        'total_problems': total_problems,
        'total_solved': total_solved
    }

def delete_problem(problem_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Delete from history
        cursor.execute("DELETE FROM history WHERE problem_id=?", (problem_id,))
        # Delete from revisions
        cursor.execute("DELETE FROM revisions WHERE problem_id=?", (problem_id,))
        # Delete from problems
        cursor.execute("DELETE FROM problems WHERE problem_id=?", (problem_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting problem: {e}")
        return False
    finally:
        conn.close()
