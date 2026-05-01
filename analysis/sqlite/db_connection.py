import sqlite3

from config.env_settings import ENV

conn = sqlite3.connect(ENV.database_path)
