# LeetRepeat 🔁

A personal spaced-revision recorder for LeetCode problems built with Streamlit and SQLite.

## Features

- **Spaced Repetition**: Automatically schedules revisions based on a custom interval sequence (default: 1, 2, 3, 5, 9, 15, 20, 30, 60 days).
- **Daily View**: See what's due today and what's overdue.
- **Calendar**: Visual monthly view of your revision load.
- **Analytics**: Track your progress and streaks.
- **Flexible**: Mark problems as Done, Failed (reschedules), or Snooze.
- **Export**: Download your data as CSV or SQLite DB.

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the app:

```bash
streamlit run app.py
```

## How it Works

1.  **Add Problem**: Enter a LeetCode URL or ID. The app normalizes it and schedules future revisions.
2.  **Today**: Check the "Today" tab to see due revisions.
    *   **Done**: Marks the revision complete and records a success in history.
    *   **Fail**: Records a failure and reschedules a short-term review (2 days later) or restarts the schedule (configurable).
    *   **Snooze**: Push the revision back by 1, 2, or 7 days.
3.  **Settings**: Customize your intervals and failure behavior.

## Testing

Run unit tests:

```bash
pytest test_scheduling.py
```

## Deployment on Streamlit Community Cloud

1.  **Push to GitHub**: Create a new repository on GitHub and push this code to it.
    *   Note: The `.gitignore` file ensures your local database (`leetrepeat.db`) is NOT pushed. A new, empty database will be created when the app starts in the cloud.
2.  **Deploy**:
    *   Go to [share.streamlit.io](https://share.streamlit.io/).
    *   Connect your GitHub account.
    *   Click "New app".
    *   Select your repository, branch (usually `main`), and the main file path (`app.py`).
    *   Click "Deploy".

### ⚠️ Important Note on Data Persistence
Streamlit Community Cloud is **ephemeral**. This means:
*   Your data (stored in `leetrepeat.db`) will be **RESET** whenever the app restarts or goes to sleep (which happens after periods of inactivity).
*   **Recommendation**: Use the "Export/Backup" tab frequently to download your `leetrepeat.db` or CSVs. You can upload them back if needed, or consider connecting to a cloud database (like Google Sheets, Firestore, or Supabase) for permanent storage.
