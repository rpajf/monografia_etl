"""
Create Temporary_Data table and insert a test row
"""
import psycopg
import uuid

print("🔨 Creating Temporary_Data table...\n")

# Connect to database
conn_string = "host=localhost port=5432 dbname=etldb user=postgres"

with psycopg.connect(conn_string) as conn:
    with conn.cursor() as cur:
        
        # Drop table if exists (optional - for testing)
        print("Dropping existing table (if exists)...")
        cur.execute("DROP TABLE IF EXISTS Temporary_Data CASCADE;")
        
        # Create table
        print("Creating Temporary_Data table...")
        cur.execute("""
            CREATE TABLE Temporary_Data (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                fileId VARCHAR(255),
                size BIGINT,
                extension VARCHAR(50)
            );
        """)
        
        print("✅ Table created successfully!\n")
        
        # Insert a test row
        print("Inserting test row...")
        test_uuid = uuid.uuid4()
        
        cur.execute("""
            INSERT INTO Temporary_Data (id, fileId, size, extension)
            VALUES (%s, %s, %s, %s)
            RETURNING id, fileId, size, extension;
        """, (
            test_uuid,
            'file_12345',
            1024768,  # ~1MB in bytes
            'json'
        ))
        
        # Get the inserted row
        result = cur.fetchone()
        
        print(f"✅ Row inserted successfully!")
        print(f"\n📊 Inserted data:")
        print(f"   ID: {result[0]}")
        print(f"   File ID: {result[1]}")
        print(f"   Size: {result[2]} bytes")
        print(f"   Extension: {result[3]}")
        
        # Verify by counting rows
        cur.execute("SELECT COUNT(*) FROM Temporary_Data;")
        count = cur.fetchone()[0]
        print(f"\n📈 Total rows in Temporary_Data: {count}")
        
        # Show table structure
        print("\n📋 Table structure:")
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'temporary_data'
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        for col in columns:
            col_name, data_type, max_length = col
            if max_length:
                print(f"   - {col_name}: {data_type}({max_length})")
            else:
                print(f"   - {col_name}: {data_type}")
        
        conn.commit()

print("\n✨ Done!")


