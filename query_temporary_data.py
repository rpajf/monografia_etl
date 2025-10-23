"""
Different ways to query and print data from Temporary_Data table
"""
import psycopg

print("📊 Querying Temporary_Data table\n")

conn_string = "host=localhost port=5432 dbname=etldb user=postgres"

with psycopg.connect(conn_string) as conn:
    with conn.cursor() as cur:
        
        # Method 1: fetchall() - Get all rows
        print("=" * 60)
        print("Method 1: fetchall() - Get all rows at once")
        print("=" * 60)
        cur.execute("SELECT * FROM Temporary_Data;")
        rows = cur.fetchall()
        
        print(f"Found {len(rows)} row(s)\n")
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"File ID: {row[1]}")
            print(f"Size: {row[2]}")
            print(f"Extension: {row[3]}")
            print("-" * 40)
        
        
        # Method 2: fetchone() - Get one row at a time
        print("\n" + "=" * 60)
        print("Method 2: fetchone() - Get one row at a time")
        print("=" * 60)
        cur.execute("SELECT * FROM Temporary_Data;")
        
        row = cur.fetchone()
        while row:
            print(f"Row: {row}")
            row = cur.fetchone()
        
        
        # Method 3: With column names (dict-like)
        print("\n" + "=" * 60)
        print("Method 3: Using dict_row for column names")
        print("=" * 60)
        from psycopg.rows import dict_row
        
        with conn.cursor(row_factory=dict_row) as dict_cur:
            dict_cur.execute("SELECT * FROM Temporary_Data;")
            rows = dict_cur.fetchall()
            
            for row in rows:
                print(f"ID: {row['id']}")
                print(f"File ID: {row['fileid']}")  # Note: lowercase!
                print(f"Size: {row['size']}")
                print(f"Extension: {row['extension']}")
                print("-" * 40)
        
        
        # Method 4: Formatted table output
        print("\n" + "=" * 60)
        print("Method 4: Pretty table format")
        print("=" * 60)
        cur.execute("SELECT * FROM Temporary_Data;")
        rows = cur.fetchall()
        
        # Print header
        print(f"{'ID':<38} {'File ID':<15} {'Size':>10} {'Extension':<10}")
        print("-" * 80)
        
        # Print data
        for row in rows:
            print(f"{str(row[0]):<38} {row[1]:<15} {row[2]:>10} {row[3]:<10}")
        
        
        # Method 5: With pandas (best for large datasets)
        print("\n" + "=" * 60)
        print("Method 5: Using pandas DataFrame")
        print("=" * 60)
        import pandas as pd
        from sqlalchemy import create_engine
        
        engine = create_engine("postgresql://postgres@localhost:5432/etldb")
        df = pd.read_sql("SELECT * FROM Temporary_Data", engine)
        
        print(df)
        print(f"\nDataFrame shape: {df.shape}")
        print(f"\nColumn types:\n{df.dtypes}")
        
        
        # Method 6: Iterate directly (memory efficient)
        print("\n" + "=" * 60)
        print("Method 6: Iterate cursor directly (memory efficient)")
        print("=" * 60)
        cur.execute("SELECT * FROM Temporary_Data;")
        
        for i, row in enumerate(cur, start=1):
            print(f"Row {i}: {row}")

print("\n✨ Done!")



