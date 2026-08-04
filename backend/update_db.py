import sqlite3
import os

DB_PATH = "clinicaflow.db"

def update_database():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Add email to patients
        cursor.execute("ALTER TABLE patients ADD COLUMN email VARCHAR;")
        print("Added 'email' to 'patients' table.")
    except sqlite3.OperationalError as e:
        print(f"Skipping email addition: {e}")

    try:
        # Add appointment_type to appointments
        cursor.execute("ALTER TABLE appointments ADD COLUMN appointment_type VARCHAR;")
        print("Added 'appointment_type' to 'appointments' table.")
    except sqlite3.OperationalError as e:
        print(f"Skipping appointment_type addition: {e}")

    try:
        # Add meeting_link to appointments
        cursor.execute("ALTER TABLE appointments ADD COLUMN meeting_link VARCHAR;")
        print("Added 'meeting_link' to 'appointments' table.")
    except sqlite3.OperationalError as e:
        print(f"Skipping meeting_link addition: {e}")

    conn.commit()
    conn.close()
    print("Database schema update complete.")

if __name__ == "__main__":
    update_database()
