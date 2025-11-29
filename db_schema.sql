CREATE TABLE IF NOT EXISTS problems (
    problem_id TEXT PRIMARY KEY,
    title TEXT,
    difficulty TEXT,
    tags TEXT,
    date_added DATE
);

CREATE TABLE IF NOT EXISTS revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id TEXT REFERENCES problems(problem_id),
    due_date DATE,
    status TEXT CHECK(status IN ('pending','done','skipped')) DEFAULT 'pending',
    date_completed DATE,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id TEXT REFERENCES problems(problem_id),
    date DATE,
    result TEXT CHECK(result IN ('solved','failed')),
    quality INTEGER CHECK(quality BETWEEN 0 AND 5),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT
);
