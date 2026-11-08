import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)
DB_NAME = "tasks.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html", tasks=tasks)

@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "General").strip()

    if title:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO tasks (title, category, status, created_at) VALUES (?, ?, 'Pending', ?)",
            (title, category, now)
        )
        conn.commit()
        conn.close()

    return redirect(url_for("index"))

@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_status(task_id):
    conn = get_db_connection()
    task = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if task:
        new_status = "Completed" if task["status"] == "Pending" else "Pending"
        conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
        conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/api/analytics")
def get_analytics():
    conn = get_db_connection()
    completed = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Completed'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Pending'").fetchone()[0]
    categories = conn.execute("SELECT category, COUNT(*) as count FROM tasks GROUP BY category").fetchall()
    conn.close()

    return jsonify({
        "status_distribution": {
            "completed": completed,
            "pending": pending
        },
        "categories": {row["category"]: row["count"] for row in categories}
    })

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
