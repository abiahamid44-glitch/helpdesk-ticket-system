from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from datetime import datetime

app = FastAPI(title="Help Desk Ticket API")

DB_NAME = "tickets.db"


class Ticket(BaseModel):
    title: str
    description: str
    priority: str
    status: str = "Open"


class TicketUpdate(BaseModel):
    status: str


class LoginRequest(BaseModel):
    username: str
    password: str


def get_connection():
    return sqlite3.connect(DB_NAME)


def log_activity(action):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO activity_logs (action, timestamp)
        VALUES (?, ?)
    """, (
        action,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password)
        VALUES ('admin', 'password123')
    """)

    conn.commit()
    conn.close()


create_tables()


@app.get("/")
def home():
    return {"message": "Help Desk Ticket API is running"}


@app.post("/login")
def login(data: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM users
        WHERE username = ? AND password = ?
    """, (data.username, data.password))

    user = cursor.fetchone()
    conn.close()

    if user:
        return {"success": True}

    return {"success": False}


@app.post("/tickets")
def create_ticket(ticket: Ticket):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tickets (title, description, priority, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        ticket.title,
        ticket.description,
        ticket.priority,
        ticket.status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    ticket_id = cursor.lastrowid

    conn.commit()
    conn.close()

    log_activity(f"Ticket #{ticket_id} created: {ticket.title}")

    return {"message": "Ticket created successfully"}


@app.get("/tickets")
def get_tickets():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tickets ORDER BY id DESC")
    rows = cursor.fetchall()

    conn.close()

    tickets = []

    for row in rows:
        tickets.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "priority": row[3],
            "status": row[4],
            "created_at": row[5]
        })

    return tickets


@app.put("/tickets/{ticket_id}")
def update_ticket(ticket_id: int, ticket_update: TicketUpdate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tickets
        SET status = ?
        WHERE id = ?
    """, (ticket_update.status, ticket_id))

    conn.commit()
    conn.close()

    log_activity(f"Ticket #{ticket_id} updated to {ticket_update.status}")

    return {"message": "Ticket updated successfully"}


@app.delete("/tickets/{ticket_id}")
def delete_ticket(ticket_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT title FROM tickets WHERE id = ?", (ticket_id,))
    ticket = cursor.fetchone()

    cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))

    conn.commit()
    conn.close()

    if ticket:
        log_activity(f"Ticket #{ticket_id} deleted: {ticket[0]}")
    else:
        log_activity(f"Ticket #{ticket_id} delete attempted")

    return {"message": "Ticket deleted successfully"}


@app.get("/activity")
def get_activity():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT action, timestamp
        FROM activity_logs
        ORDER BY id DESC
        LIMIT 10
    """)

    logs = cursor.fetchall()

    conn.close()

    return [
        {
            "action": row[0],
            "timestamp": row[1]
        }
        for row in logs
    ]