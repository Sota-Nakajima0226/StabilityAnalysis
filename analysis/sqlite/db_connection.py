import sqlite3

# DB Connection
conn = sqlite3.connect("nonsusy_strings.db")
conn.execute("PRAGMA foreign_keys = ON;")

cur = conn.cursor()
