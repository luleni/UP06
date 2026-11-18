import os
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "tasks.db"


def connect():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    return db


with closing(connect()) as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
    """)
    db.commit()


PAGE = """
<!doctype html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Список задач</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f1f5f9;
            color: #172033;
            max-width: 760px;
            margin: 60px auto;
            padding: 0 20px;
        }
        .card {
            background: white;
            padding: 28px;
            border-radius: 16px;
            box-shadow: 0 8px 30px #17203312;
        }
        input {
            padding: 12px;
            width: 62%;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
        }
        button {
            padding: 12px 16px;
            border: 0;
            border-radius: 8px;
            background: #2563eb;
            color: white;
            cursor: pointer;
        }
        ul { padding: 0; list-style: none; }
        li {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            padding: 14px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        .done { text-decoration: line-through; color: #64748b; }
        .note { color: #64748b; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <p class="note">УП 06 · Практическое задание 4</p>
        <h1>Список задач</h1>

        <form method="post" action="/">
            <input name="title" placeholder="Новая задача"
                   maxlength="200" required>
            <button type="submit">Добавить</button>
        </form>

        <ul>
        {% for task in tasks %}
            <li>
                <span class="{{ 'done' if task['done'] else '' }}">
                    {{ task['title'] }}
                </span>
                <form method="post"
                      action="{{ url_for('toggle', task_id=task['id']) }}">
                    <button type="submit">
                        {{ 'Вернуть' if task['done'] else 'Выполнено' }}
                    </button>
                </form>
            </li>
        {% else %}
            <li>Пока нет задач. Добавьте первую.</li>
        {% endfor %}
        </ul>

        <p class="note">Хранилище данных: SQLite</p>
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if title and len(title) <= 200:
            with closing(connect()) as db:
                db.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
                db.commit()
        return redirect(url_for("index"))

    with closing(connect()) as db:
        tasks = db.execute(
            "SELECT id, title, done FROM tasks ORDER BY id DESC"
        ).fetchall()

    return render_template_string(PAGE, tasks=tasks)


@app.post("/toggle/<int:task_id>")
def toggle(task_id):
    with closing(connect()) as db:
        db.execute(
            "UPDATE tasks SET done = 1 - done WHERE id = ?",
            (task_id,),
        )
        db.commit()
    return redirect(url_for("index"))
