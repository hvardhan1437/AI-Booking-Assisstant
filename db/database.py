import sqlite3
from datetime import datetime, timedelta

DB_PATH = "db/bookings.db"


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            booking_type TEXT,
            date TEXT,
            time TEXT,
            status TEXT,
            created_at TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        )
    """)

    conn.commit()
    conn.close()


# 🔒 AUTHORITATIVE SAVE (conflict enforced here)
def save_booking(booking):
    conn = get_connection()
    cursor = conn.cursor()

    # ---------- FINAL SLOT CONFLICT CHECK ----------
    existing = get_bookings_by_date(booking["date"])

    requested_dt = datetime.strptime(
        f"{booking['date']} {booking['time']}",
        "%Y-%m-%d %H:%M"
    )

    for b in existing:
        existing_dt = datetime.strptime(
            f"{b['date']} {b['time']}",
            "%Y-%m-%d %H:%M"
        )

        diff_minutes = abs(
            (requested_dt - existing_dt).total_seconds()
        ) / 60

        if diff_minutes < 30:
            conn.close()
            raise ValueError(
                f"An appointment already exists at {b['time']}. "
                f"Please choose a time after "
                f"{(existing_dt + timedelta(minutes=30)).strftime('%H:%M')}."
            )

    # ---------- INSERT CUSTOMER ----------
    cursor.execute("""
        INSERT INTO customers (name, email, phone)
        VALUES (?, ?, ?)
    """, (booking["name"], booking["email"], booking["phone"]))

    customer_id = cursor.lastrowid

    # ---------- INSERT BOOKING ----------
    cursor.execute("""
        INSERT INTO bookings (
            customer_id, booking_type, date, time, status, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        customer_id,
        booking["booking_type"],
        booking["date"],
        booking["time"],
        "CONFIRMED",
        datetime.now().isoformat()
    ))

    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return booking_id


def get_all_bookings():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            b.id,
            c.name,
            c.email,
            c.phone,
            b.booking_type,
            b.date,
            b.time,
            b.status,
            b.created_at
        FROM bookings b
        JOIN customers c ON b.customer_id = c.customer_id
        ORDER BY b.created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_bookings_by_date(date_str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, time
        FROM bookings
        WHERE date = ?
          AND status = 'CONFIRMED'
    """, (date_str,))

    rows = cursor.fetchall()
    conn.close()

    return [{"date": r[0], "time": r[1]} for r in rows]


def clear_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM bookings;")
    cursor.execute("DELETE FROM customers;")

    conn.commit()
    conn.close()
