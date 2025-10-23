"""
Test PostgreSQL connection - Multiple methods
Run this after starting docker-compose
"""
import os
import psycopg
# Set environment variables - UPDATED to match current docker-compose.yml
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'etldb'  # Changed from covid_etl
os.environ['DB_USER'] = 'postgres'  # Changed from etl_user
os.environ['DB_PASSWORD'] = ''  # No password (trust auth)
os.environ['DB_SCHEMA'] = 'public'  # Changed from covid_data

print("🔍 Testing PostgreSQL Connection...\n")

with psycopg.connect("host=localhost port=5432 dbname=etldb user=postgres", connect_timeout=10) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✅ Connected! PostgreSQL version:")
        print(f"   {version[0][:80]}...")
        
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")

        tables = cur.fetchall()
        print(f"\n📊 Tables in public schema:")
        for table in tables:
            print(f"   - {table[0]}")
        cur.execute("SELECT * FROM Temporary_Data;")
        rows = cur.fetchall()
        for row in rows:
            print(f"   - {row}")
        
        cur.close()