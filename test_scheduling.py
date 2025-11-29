import pytest
import database as db
import os
import datetime
import json

# Use a temporary DB for testing
TEST_DB = "test_leetrepeat.db"

@pytest.fixture
def setup_db():
    # Override DB_FILE in database module for testing
    # This is a bit hacky, better to have a class or pass db path, but for this script it works if we patch it or just swap the variable
    original_db = db.DB_FILE
    db.DB_FILE = TEST_DB
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
        
    db.init_db()
    yield
    
    db.DB_FILE = original_db
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_add_problem_scheduling(setup_db):
    # Test that adding a problem creates revisions
    today = datetime.date.today()
    db.add_problem("two-sum", "Two Sum", "Easy", "array", today)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM revisions WHERE problem_id='two-sum'")
    revisions = cursor.fetchall()
    conn.close()
    
    # Default intervals: [1, 2, 3, 5, 9, 15, 20, 30, 60] -> 9 revisions
    assert len(revisions) == 9
    
    # Check first revision due date (today + 1)
    first_due = datetime.datetime.strptime(revisions[0]['due_date'], '%Y-%m-%d').date()
    assert first_due == today + datetime.timedelta(days=1)

def test_mark_done(setup_db):
    today = datetime.date.today()
    db.add_problem("two-sum", "Two Sum", "Easy", "array", today)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM revisions WHERE problem_id='two-sum' LIMIT 1")
    rev_id = cursor.fetchone()['id']
    conn.close()
    
    db.mark_revision_done(rev_id, "two-sum", today)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM revisions WHERE id=?", (rev_id,))
    status = cursor.fetchone()['status']
    
    cursor.execute("SELECT * FROM history WHERE problem_id='two-sum'")
    history = cursor.fetchall()
    conn.close()
    
    assert status == 'done'
    assert len(history) == 1
    assert history[0]['result'] == 'solved'

def test_fail_behavior_short_repeat(setup_db):
    # Ensure default is short_repeat
    db.set_config('fail_behavior', 'short_repeat')
    
    today = datetime.date.today()
    db.add_problem("two-sum", "Two Sum", "Easy", "array", today)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM revisions WHERE problem_id='two-sum' LIMIT 1")
    rev_id = cursor.fetchone()['id']
    conn.close()
    
    db.mark_revision_failed(rev_id, "two-sum", today)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Check if a new revision was added for today + 2
    cursor.execute("SELECT * FROM revisions WHERE problem_id='two-sum' ORDER BY id DESC LIMIT 1")
    last_rev = cursor.fetchone()
    
    due_date = datetime.datetime.strptime(last_rev['due_date'], '%Y-%m-%d').date()
    assert due_date == today + datetime.timedelta(days=2)
    
    # Check history
    cursor.execute("SELECT * FROM history WHERE problem_id='two-sum' AND result='failed'")
    history = cursor.fetchall()
    assert len(history) == 1
    conn.close()
