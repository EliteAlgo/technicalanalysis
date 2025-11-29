"""
login.py

Simple authentication utility for the Streamlit app.
Replace USERNAME and PASSWORD with your desired credentials.
"""

USERNAME = "admin"
PASSWORD = "password123"

def authenticate(user: str, pwd: str) -> bool:
    """Return True if credentials match the hard‑coded values."""
    return user == USERNAME and pwd == PASSWORD
