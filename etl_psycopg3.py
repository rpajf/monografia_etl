"""
ETL with psycopg3 (Modern version)
Demonstrates performance optimizations for your thesis
"""
import psycopg
from psycopg import sql
import pandas as pd
import time
from datetime import datetime

# Connection string
CONN_STRING = "host=localhost port=5432 dbname=etldb user=postgres"


class DatabaseConnector:
    def __init__(self):
        self.conn_str = CONN_STRING

    def create_table(self, table_name, columns):
        """
        Create a table dynamically with provided columns.
        Example columns: 'id SERIAL PRIMARY KEY, name TEXT, age INT'
        """
        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {columns}
        );
        """
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
            conn.commit()
        print(f"✅ Table '{table_name}' created successfully.")

    def insert_into_table(self, table_name, data):
        """
        Insert a row into a given table.
        - `data` should be a dictionary: {"column1": value1, "column2": value2, ...}
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = list(data.values())

        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
            conn.commit()

        print(f"✅ Inserted 1 record into '{table_name}' successfully.")




# def create_test_table():
#     """Create papers table for testing"""
#     with psycopg.connect(CONN_STRING) as conn:
#         with conn.cursor() as cur:
#             cur.execute("""
#                 DROP TABLE IF EXISTS papers CASCADE;
#                 CREATE TABLE papers (
#                     paper_id VARCHAR(100) PRIMARY KEY,
#                     title TEXT,
#                     abstract TEXT,
#                     publish_time DATE,
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 );
#             """)
#         conn.commit()
#     print("✅ Table created")


# # Strategy 1: BASELINE - Row by row (SLOW)
# def insert_row_by_row(data_list):
#     """Baseline: Insert one row at a time - SLOWEST"""
#     print("\n📊 Strategy 1: Row-by-row insert (BASELINE)")
    
#     with psycopg.connect(CONN_STRING) as conn:
#         with conn.cursor() as cur:
#             start = time.time()
            
#             for row in data_list:
#                 cur.execute(
#                     "INSERT INTO papers (paper_id, title, abstract) VALUES (%s, %s, %s)",
#                     row
#                 )
            
#             conn.commit()
#             duration = time.time() - start
    
#     print(f"   ⏱️  Time: {duration:.2f}s for {len(data_list)} rows")
#     print(f"   📈 Rate: {len(data_list)/duration:.0f} rows/sec")
#     return duration


# # Strategy 2: OPTIMIZED - Batch insert

