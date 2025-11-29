import streamlit as st
import pandas as pd
import datetime
import database as db
import calendar
import time

# Page config
st.set_page_config(
    page_title="LeetRepeat",
    page_icon="🔁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize DB
if 'db_initialized' not in st.session_state:
    db.init_db()
    st.session_state.db_initialized = True

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #4e8cff;
    }
    .card-overdue {
        border-left: 5px solid #ff4b4b;
    }
    .metric-container {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("LeetRepeat 🔁")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio("Navigation", ["Today", "Calendar", "Add Problem", "All Problems", "Analytics", "Settings", "Export/Backup"])

# Date Simulation (for testing)
st.sidebar.markdown("---")
st.sidebar.subheader("Time Travel 🕰️")
if 'current_date' not in st.session_state:
    st.session_state.current_date = datetime.date.today()

sim_date = st.sidebar.date_input("Simulate Date", value=st.session_state.current_date)
st.session_state.current_date = sim_date

# Quick Stats in Sidebar
due_revisions = db.get_due_revisions(st.session_state.current_date)
overdue_count = sum(1 for r in due_revisions if datetime.datetime.strptime(r['due_date'], '%Y-%m-%d').date() < st.session_state.current_date)
due_today_count = sum(1 for r in due_revisions if datetime.datetime.strptime(r['due_date'], '%Y-%m-%d').date() == st.session_state.current_date)

st.sidebar.markdown(f"**Due Today:** {due_today_count}")
st.sidebar.markdown(f"**Overdue:** {overdue_count}")

# Helper functions
def render_revision_card(revision):
    due_date = datetime.datetime.strptime(revision['due_date'], '%Y-%m-%d').date()
    is_overdue = due_date < st.session_state.current_date
    card_class = "card-overdue" if is_overdue else "card"
    
    with st.container():
        st.markdown(f"""
        <div class="{card_class}">
            <h4><a href="https://leetcode.com/problems/{revision['problem_id']}" target="_blank">{revision['title'] or revision['problem_id']}</a></h4>
            <p><strong>Difficulty:</strong> {revision['difficulty'] or 'N/A'} | <strong>Tags:</strong> {revision['tags'] or 'None'}</p>
            <p><strong>Due:</strong> {due_date} { "(Overdue)" if is_overdue else ""}</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("Done ✓", key=f"done_{revision['id']}"):
                db.mark_revision_done(revision['id'], revision['problem_id'], st.session_state.current_date, quality=5) # Default quality 5
                st.success("Marked as done!")
                time.sleep(0.5)
                st.rerun()
        with c2:
            if st.button("Fail ✗", key=f"fail_{revision['id']}"):
                db.mark_revision_failed(revision['id'], revision['problem_id'], st.session_state.current_date)
                st.error("Marked as failed. Rescheduled.")
                time.sleep(0.5)
                st.rerun()
        with c3:
            snooze_days = st.selectbox("Snooze", [1, 2, 7], key=f"snooze_sel_{revision['id']}", label_visibility="collapsed")
        with c4:
            if st.button("Snooze ⏰", key=f"snooze_btn_{revision['id']}"):
                db.snooze_revision(revision['id'], snooze_days)
                st.info(f"Snoozed for {snooze_days} days.")
                time.sleep(0.5)
                st.rerun()
        st.markdown("---")

# Pages
if page == "Today":
    st.header(f"Today's Revisions ({st.session_state.current_date})")
    
    col_main, col_right = st.columns([2, 1])
    
    with col_main:
        view_option = st.radio("Show", ["All Due", "Overdue Only", "Today Only"], horizontal=True)
        
        to_show = []
        for r in due_revisions:
            r_date = datetime.datetime.strptime(r['due_date'], '%Y-%m-%d').date()
            if view_option == "Overdue Only" and r_date < st.session_state.current_date:
                to_show.append(r)
            elif view_option == "Today Only" and r_date == st.session_state.current_date:
                to_show.append(r)
            elif view_option == "All Due":
                to_show.append(r)
                
        if not to_show:
            st.info("No revisions due!")
        else:
            for r in to_show:
                render_revision_card(r)

    with col_right:
        st.subheader("Calendar")
        # Mini Calendar
        year = st.session_state.current_date.year
        month = st.session_state.current_date.month
        
        # Navigation for mini calendar
        mc1, mc2, mc3 = st.columns([1, 2, 1])
        if mc1.button("<", key="mini_prev"):
            new_date = st.session_state.current_date.replace(day=1) - datetime.timedelta(days=1)
            st.session_state.current_date = new_date
            st.rerun()
        mc2.markdown(f"**{calendar.month_name[month]} {year}**", unsafe_allow_html=True)
        if mc3.button(">", key="mini_next"):
            if month == 12:
                new_date = datetime.date(year + 1, 1, 1)
            else:
                new_date = datetime.date(year, month + 1, 1)
            st.session_state.current_date = new_date
            st.rerun()
            
        counts = db.get_counts_per_day(year, month)
        cal = calendar.monthcalendar(year, month)
        
        # Small grid
        cols = st.columns(7)
        days = ["M", "T", "W", "T", "F", "S", "S"]
        for i, day in enumerate(days):
            cols[i].markdown(f"<small>{day}</small>", unsafe_allow_html=True)
            
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write("")
                else:
                    d_str = f"{year}-{month:02d}-{day:02d}"
                    count = counts.get(d_str, 0)
                    # Highlight current day
                    is_selected = (day == st.session_state.current_date.day and month == st.session_state.current_date.month and year == st.session_state.current_date.year)
                    
                    label = f"{day}"
                    if count > 0:
                        label += f" •" # Dot to indicate tasks
                    
                    if cols[i].button(label, key=f"mini_cal_{d_str}", help=f"{count} tasks"):
                        st.session_state.current_date = datetime.date(year, month, day)
                        st.rerun()
        
        st.markdown("---")
        st.subheader("Quick Stats")
        stats = db.get_analytics_stats()
        st.metric("Total Solved", stats['total_solved'])
        st.metric("Due Today", due_today_count)
        st.metric("Overdue", overdue_count)

elif page == "Add Problem":
    st.header("Add New Problem")
    
    with st.form("add_problem_form"):
        p_id_input = st.text_input("LeetCode URL or ID (Slug)")
        title = st.text_input("Title (Optional)")
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
        tags = st.text_input("Tags (Comma separated)")
        
        submitted = st.form_submit_button("Add and Schedule")
        
        if submitted and p_id_input:
            # Normalize slug
            slug = p_id_input.strip()
            if "leetcode.com/problems/" in slug:
                slug = slug.split("leetcode.com/problems/")[1].split("/")[0]
            
            success = db.add_problem(slug, title, difficulty, tags, st.session_state.current_date)
            if success:
                st.success(f"Added {slug} and scheduled revisions!")
            else:
                st.error("Problem already exists or error adding.")
    
    st.markdown("---")
    st.markdown("---")
    st.subheader("Bulk Import")
    st.markdown("Upload CSV with columns: `problem_id`, `title`, `difficulty`, `tags`, `date` (optional, YYYY-MM-DD)")
    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    if uploaded_file is not None:
        if st.button("Import CSV"):
            try:
                df = pd.read_csv(uploaded_file)
                success_count = 0
                fail_count = 0
                for _, row in df.iterrows():
                    # Basic validation
                    if 'problem_id' not in row:
                        continue
                    
                    p_id = str(row['problem_id']).strip()
                    title = row.get('title', None)
                    difficulty = row.get('difficulty', None)
                    tags = row.get('tags', None)
                    
                    # Date handling
                    date_added = st.session_state.current_date
                    if 'date' in row and pd.notna(row['date']):
                        try:
                            date_added = datetime.datetime.strptime(str(row['date']), '%Y-%m-%d').date()
                        except:
                            pass # Fallback to current date
                    
                    if db.add_problem(p_id, title, difficulty, tags, date_added):
                        success_count += 1
                    else:
                        fail_count += 1
                st.success(f"Imported {success_count} problems. {fail_count} failed (duplicates).")
            except Exception as e:
                st.error(f"Error processing CSV: {e}")

elif page == "Calendar":
    st.header("Calendar View")
    
    # Simple month view
    # We can use st.date_input to select a date, but to show counts we need a custom grid
    
    year = st.session_state.current_date.year
    month = st.session_state.current_date.month
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("Previous Month"):
            new_date = st.session_state.current_date.replace(day=1) - datetime.timedelta(days=1)
            st.session_state.current_date = new_date
            st.rerun()
    with c2:
        st.markdown(f"<h3 style='text-align: center'>{calendar.month_name[month]} {year}</h3>", unsafe_allow_html=True)
    with c3:
        if st.button("Next Month"):
            # Logic to go to next month
            if month == 12:
                new_date = datetime.date(year + 1, 1, 1)
            else:
                new_date = datetime.date(year, month + 1, 1)
            st.session_state.current_date = new_date
            st.rerun()

    counts = db.get_counts_per_day(year, month)
    
    cal = calendar.monthcalendar(year, month)
    
    cols = st.columns(7)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, day in enumerate(days):
        cols[i].markdown(f"**{day}**")
        
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                d_str = f"{year}-{month:02d}-{day:02d}"
                count = counts.get(d_str, 0)
                if cols[i].button(f"{day} {'(' + str(count) + ')' if count > 0 else ''}", key=f"cal_{d_str}"):
                    st.session_state.current_date = datetime.date(year, month, day)
                    st.rerun()

elif page == "All Problems":
    st.header("All Problems")
    df = db.get_all_problems_df()
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    
    # Edit Problem Section
    with st.expander("Edit Problem Details"):
        if not df.empty:
            # Select problem to edit
            edit_options = [f"{row['problem_id']} | {row['title']}" for _, row in df.iterrows()]
            edit_sel = st.selectbox("Select Problem to Edit", edit_options, key="edit_sel")
            
            # Get current data
            edit_id = edit_sel.split(" | ")[0]
            current_row = df[df['problem_id'] == edit_id].iloc[0]
            
            with st.form("edit_problem_form"):
                new_title = st.text_input("Title", value=current_row['title'] if current_row['title'] else "")
                new_difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=["Easy", "Medium", "Hard"].index(current_row['difficulty']) if current_row['difficulty'] in ["Easy", "Medium", "Hard"] else 1)
                new_tags = st.text_input("Tags", value=current_row['tags'] if current_row['tags'] else "")
                
                # Date handling
                curr_date_val = datetime.date.today()
                if pd.notna(current_row['date_added']):
                    try:
                        curr_date_val = datetime.datetime.strptime(str(current_row['date_added']), '%Y-%m-%d').date()
                    except:
                        pass
                
                new_date = st.date_input("Date Added (Changing this resets schedule!)", value=curr_date_val)
                
                if st.form_submit_button("Update Problem"):
                    update_data = {
                        'title': new_title,
                        'difficulty': new_difficulty,
                        'tags': new_tags,
                        'date_added': new_date
                    }
                    if db.update_problem(edit_id, update_data):
                        st.success("Problem updated successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to update problem.")
        else:
            st.info("No problems to edit.")

    with st.expander("Danger Zone: Delete Problem"):
        st.warning("This will permanently delete the problem, its revision schedule, and history.")
        
        if not df.empty:
            # Create a list of "ID | Title" for the selectbox
            problem_options = [f"{row['problem_id']} | {row['title']}" for _, row in df.iterrows()]
            selected_option = st.selectbox("Select Problem to Delete", problem_options)
            
            if st.button("Delete Selected Problem", type="primary"):
                # Extract problem_id
                selected_id = selected_option.split(" | ")[0]
                if db.delete_problem(selected_id):
                    st.success(f"Deleted problem {selected_id}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to delete problem.")
        else:
            st.info("No problems to delete.")

elif page == "Analytics":
    st.header("Analytics")
    stats = db.get_analytics_stats()
    
    c1, c2 = st.columns(2)
    c1.metric("Total Problems", stats['total_problems'])
    c2.metric("Total Solved (Unique)", stats['total_solved'])
    
    st.subheader("History")
    hist_df = db.get_history_df()
    st.dataframe(hist_df, use_container_width=True)

elif page == "Settings":
    st.header("Settings")
    
    current_intervals = db.get_config('intervals')
    intervals_str = st.text_input("Intervals (JSON list)", value=current_intervals)
    
    if st.button("Save Intervals"):
        try:
            import json
            json.loads(intervals_str) # Validate
            db.set_config('intervals', intervals_str)
            st.success("Saved!")
        except:
            st.error("Invalid JSON format")
            
    fail_behavior = st.selectbox("Fail Behavior", ["short_repeat", "restart"], index=0 if db.get_config('fail_behavior') == 'short_repeat' else 1)
    if st.button("Save Fail Behavior"):
        db.set_config('fail_behavior', fail_behavior)
        st.success("Saved!")

elif page == "Export/Backup":
    st.header("Export Data")
    
    if st.button("Export Problems CSV"):
        df = db.get_all_problems_df()
        st.download_button("Download Problems CSV", df.to_csv(index=False), "problems.csv", "text/csv")
        
    if st.button("Export Revisions CSV"):
        df = db.get_revisions_df()
        st.download_button("Download Revisions CSV", df.to_csv(index=False), "revisions.csv", "text/csv")
        
    if st.button("Export History CSV"):
        df = db.get_history_df()
        st.download_button("Download History CSV", df.to_csv(index=False), "history.csv", "text/csv")
        
    with open(db.DB_FILE, "rb") as f:
        st.download_button("Download SQLite DB", f, "leetrepeat.db")

