import sqlite3
import pandas as pd
from config import Config

def init_db():
    conn = sqlite3.connect(Config.DATABASE_URI)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS results
                 (email TEXT PRIMARY KEY, 
                  detected INTEGER, 
                  processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_result(email, detected):
    conn = sqlite3.connect(Config.DATABASE_URI)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO results (email, detected)
                 VALUES (?, ?)''', (email, int(detected)))
    conn.commit()
    conn.close()

def get_results_dataframe():
    conn = sqlite3.connect(Config.DATABASE_URI)
    df = pd.read_sql('SELECT * FROM results', conn)
    conn.close()
    return df