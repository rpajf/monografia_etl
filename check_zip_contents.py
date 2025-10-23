"""
Analyze ZIP file contents - Count records and file types
"""
import zipfile
import json
from collections import defaultdict

zip_path = "/Users/raphaelportela/datasetcovid.zip"

print("🔍 Analyzing ZIP file contents...\n")
print("=" * 60)

with zipfile.ZipFile(zip_path, "r") as z:
    all_files = z.namelist()
    
    # Count by file extension
    file_types = defaultdict(int)
    total_size = 0
    
    for file_name in all_files:
        # Get extension
        if '.' in file_name:
            ext = file_name.split('.')[-1].lower()
        else:
            ext = 'no_extension'
        
        file_types[ext] += 1
        
        # Get size
        info = z.getinfo(file_name)
        total_size += info.file_size
    
    # Print summary
    print(f"📦 ZIP FILE: {zip_path.split('/')[-1]}")
    print(f"📊 TOTAL FILES: {len(all_files):,}")
    print(f"💾 TOTAL SIZE: {total_size / (1024**3):.2f} GB (uncompressed)")
    print()
    
    # Print breakdown by type
    print("📋 FILE TYPES BREAKDOWN:")
    print("-" * 60)
    for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(all_files)) * 100
        print(f"   {ext:15s}: {count:>8,} files ({percentage:>5.1f}%)")
    
    print("\n" + "=" * 60)
    
    # Sample file names
    print("\n📄 SAMPLE FILES (first 10):")
    for i, name in enumerate(all_files[:10], 1):
        size_kb = z.getinfo(name).file_size / 1024
        print(f"   {i:2d}. {name[:50]:50s} ({size_kb:>8.1f} KB)")
    
    # Check if JSON files and count records
    json_files = [f for f in all_files if f.endswith('.json')]
    
    if json_files:
        print(f"\n🔢 JSON FILES: {len(json_files):,}")
        print("   (Each JSON file is typically 1 research paper)")
        
        # Sample a few JSON files to show structure
        print("\n📖 SAMPLE PAPER DATA (first JSON file):")
        print("-" * 60)
        
        first_json = json_files[0]
        content = z.read(first_json)
        data = json.loads(content)
        
        print(f"   File: {first_json}")
        print(f"   Paper ID: {data.get('paper_id', 'N/A')}")
        print(f"   Title: {data.get('metadata', {}).get('title', 'N/A')[:100]}...")
        print(f"   Authors: {len(data.get('metadata', {}).get('authors', []))}")
        print(f"   Has Abstract: {'Yes' if data.get('abstract') else 'No'}")
        print(f"   Has Body Text: {'Yes' if data.get('body_text') else 'No'}")
    
    # CSV files
    csv_files = [f for f in all_files if f.endswith('.csv')]
    if csv_files:
        print(f"\n📊 CSV FILES: {len(csv_files)}")
        print("   Sample CSV files:")
        for csv_file in csv_files[:5]:
            print(f"      - {csv_file}")
        
        # Try to count rows in first CSV
        if csv_files:
            import csv
            import io
            first_csv = csv_files[0]
            content = z.read(first_csv).decode('utf-8')
            reader = csv.reader(io.StringIO(content))
            row_count = sum(1 for row in reader) - 1  # Exclude header
            print(f"\n   Rows in {first_csv}: {row_count:,}")

print("\n✨ Analysis complete!")
print("\n💡 SUMMARY:")
print(f"   • Total records (files): {len(all_files):,}")
if json_files:
    print(f"   • Research papers (JSON): {len(json_files):,}")
if csv_files:
    print(f"   • CSV files: {len(csv_files):,}")


