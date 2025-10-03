import mysql.connector
import bcrypt
from datetime import datetime, timedelta
import uuid
import smtplib
import ssl
from email.mime.text import MIMEText
import streamlit as st

# ===== MYSQL SETTINGS =====
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "Pks9948$1"
MYSQL_DB = "auth_db"

# ===== EMAIL SETTINGS =====
import os

EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ===== MYSQL CONNECTION HELPERS =====
def get_server_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )

def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )

def init_db():
    conn = get_server_connection()
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
    conn.commit()
    conn.close()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255) UNIQUE,
            password_hash VARCHAR(255),
            address TEXT,
            company VARCHAR(255),
            phone VARCHAR(50),
            is_admin BOOLEAN DEFAULT FALSE,
            reset_token VARCHAR(255),
            reset_expiry DATETIME
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ===== DATABASE FUNCTIONS =====
def get_user(email):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def add_user(name, email, password, address, company, phone):
    is_admin = get_user_count() == 0
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (name, email, password_hash, address, company, phone, is_admin)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (name, email, hashed.decode(), address, company, phone, is_admin))
    conn.commit()
    conn.close()

def update_password(email, new_password):
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash=%s, reset_token=NULL, reset_expiry=NULL WHERE email=%s",
                   (hashed.decode(), email))
    conn.commit()
    conn.close()

def set_reset_token(email):
    token = str(uuid.uuid4())
    expiry = datetime.now() + timedelta(minutes=30)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET reset_token=%s, reset_expiry=%s WHERE email=%s",
                   (token, expiry, email))
    conn.commit()
    conn.close()
    return token

def get_user_by_token(token):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE reset_token=%s AND reset_expiry > NOW()", (token,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user(user_id, name, email, address, company, phone, is_admin):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET name=%s, email=%s, address=%s, company=%s, phone=%s, is_admin=%s
        WHERE id=%s
    """, (name, email, address, company, phone, is_admin, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
    conn.commit()
    conn.close()

# ===== EMAIL FUNCTION =====
def send_reset_email(email, token):
    reset_link = f"http://localhost:8501?reset_token={token}"
    body = f"Click the link to reset your password:\n\n{reset_link}\n\nThis link expires in 30 minutes."
    msg = MIMEText(body)
    msg["Subject"] = "Password Reset Request"
    msg["From"] = EMAIL_USER
    msg["To"] = email

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, email, msg.as_string())
        st.success("Password reset link sent to your email.")
    except Exception as e:
        st.error(f"Error sending email: {e}")

