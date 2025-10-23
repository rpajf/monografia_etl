# JSON to CSV Export Guide 📊

Export JSON keys and values from your COVID-19 dataset to CSV format for easy analysis in Excel, Google Sheets, or pandas.

---

## 🚀 Quick Start

### Option 1: Run the main script

```bash
python fetch_db.py
```

This will create `covid_papers_data.csv` with data from 100 JSON files.

### Option 2: Run the example

```bash
python example_csv_export.py
```

This creates multiple CSV files with different sample sizes.

### Option 3: Custom export

```python
from fetch_db import ZipFileAnalyzer

analyzer = ZipFileAnalyzer("/Users/raphaelportela/datasetcovid.zip")

# Export 50 files
analyzer.save_json_to_csv(num_files=50, output_file='my_data.csv')
```

---

## 📋 CSV Format

The generated CSV has 4 columns:

| Column | Description | Example |
|--------|-------------|---------|
| `file_name` | Name of the JSON file | `document_parses/pdf_json/0001.json` |
| `key` | JSON key name | `paper_id`, `title`, `abstract` |
| `value_type` | Type of the value | `string`, `dict`, `list`, `number` |
| `value_preview` | Preview of the value | First 100 characters or description |

### Example CSV content:

```csv
file_name,key,value_type,value_preview
document_parses/pdf_json/0001.json,paper_id,string,abc123def456
document_parses/pdf_json/0001.json,metadata,dict,{dict with 5 keys}
document_parses/pdf_json/0001.json,abstract,list,[list with 3 items]
document_parses/pdf_json/0001.json,body_text,list,[list with 45 items]
```

---

## 📊 Value Types

The export recognizes these types:

- **string** - Text values (truncated to 100 chars)
- **dict** - Objects/dictionaries (shows number of keys)
- **list** - Arrays (shows number of items)
- **number** - Integers and floats
- **boolean** - True/False values
- **null** - Null values
- **other** - Any other type

---

## 💡 Use Cases

### 1. Quick Analysis in Excel

```bash
python fetch_db.py
# Open covid_papers_data.csv in Excel
# Create pivot tables, charts, etc.
```

### 2. Data Exploration with Pandas

```python
import pandas as pd

# Load the CSV
df = pd.read_csv('covid_papers_data.csv')

# What keys are most common?
print(df['key'].value_counts())

# What types of values?
print(df['value_type'].value_counts())

# Filter for specific keys
titles = df[df['key'] == 'title']
print(titles['value_preview'])

# Count papers
num_papers = df['file_name'].nunique()
print(f"Total papers: {num_papers}")
```

### 3. Data Quality Check

```python
import pandas as pd

df = pd.read_csv('covid_papers_data.csv')

# Check for missing data (nulls)
nulls = df[df['value_type'] == 'null']
print(f"Null values: {len(nulls)}")

# Find longest text fields
strings = df[df['value_type'] == 'string']
strings['length'] = strings['value_preview'].str.len()
print(strings.nlargest(10, 'length')[['key', 'length']])
```

### 4. Schema Analysis

```python
import pandas as pd

df = pd.read_csv('covid_papers_data.csv')

# What keys appear in every file?
files = df['file_name'].nunique()
key_counts = df.groupby('key')['file_name'].nunique()
common_keys = key_counts[key_counts == files]

print("Keys in all files:")
print(common_keys.index.tolist())
```

---

## ⚙️ Configuration

### Change number of files

```python
# Export 10 files (fast)
analyzer.save_json_to_csv(num_files=10, output_file='small_sample.csv')

# Export 1000 files (detailed)
analyzer.save_json_to_csv(num_files=1000, output_file='large_sample.csv')

# Export all files (will take time!)
analyzer.save_json_to_csv(num_files=999999, output_file='complete_data.csv')
```

### Change output filename

```python
# Different naming
analyzer.save_json_to_csv(num_files=100, output_file='research_papers.csv')
analyzer.save_json_to_csv(num_files=50, output_file='data/covid_subset.csv')
```

---

## 📈 Performance

| Files | Rows | Time | Size |
|-------|------|------|------|
| 10 | ~70 | ~1s | 10 KB |
| 100 | ~700 | ~5s | 100 KB |
| 1000 | ~7000 | ~45s | 1 MB |
| 10000 | ~70000 | ~7 min | 10 MB |

*Note: Times and sizes are approximate, depend on file content*

---

## 🎓 For Your Thesis

### Benefits of CSV Export:

1. **Easy Analysis** - Open in Excel, no coding needed
2. **Data Profiling** - Understand your dataset structure
3. **Schema Discovery** - Find common patterns
4. **Quality Checks** - Identify missing or malformed data
5. **Stakeholder Sharing** - Everyone can open CSV files

### Example Analyses:

```python
import pandas as pd

df = pd.read_csv('covid_papers_data.csv')

# 1. Schema completeness
schema = df.groupby('key').agg({
    'file_name': 'nunique',  # How many files have this key
    'value_type': lambda x: x.mode()[0]  # Most common type
})
print(schema)

# 2. Data type consistency
type_consistency = df.groupby('key')['value_type'].value_counts()
print(type_consistency)

# 3. Text field lengths
strings = df[df['value_type'] == 'string'].copy()
strings['length'] = strings['value_preview'].str.len()
print(strings.groupby('key')['length'].describe())
```

---

## 📝 Example Output

When you run `python fetch_db.py`:

```
💾 Saving JSON data to CSV: covid_papers_data.csv
🔍 Processing 100 files...

   Processed 10/100 files...
   Processed 20/100 files...
   Processed 30/100 files...
   ...
   Processed 100/100 files...

✅ CSV file created: covid_papers_data.csv
📊 Open with: Excel, Google Sheets, or pandas
   Example: df = pd.read_csv('covid_papers_data.csv')
```

---

## 🔧 Troubleshooting

### "UnicodeDecodeError"
- Some files have special characters
- CSV encoding is UTF-8 (should work in modern Excel)
- In Excel: Use "Data → From Text/CSV" and select UTF-8

### "File too large"
- Reduce `num_files` parameter
- Process in batches
- Use pandas to filter/subset

### "Memory error"
- The script processes one file at a time (memory efficient)
- Should work even with limited RAM
- If issues persist, use smaller batches

---

## 🌟 Advanced: Combine with Other Tools

### Load into SQLite

```python
import pandas as pd
import sqlite3

df = pd.read_csv('covid_papers_data.csv')
conn = sqlite3.connect('covid_data.db')
df.to_sql('json_keys', conn, if_exists='replace', index=False)

# Query with SQL
result = pd.read_sql("SELECT key, COUNT(*) FROM json_keys GROUP BY key", conn)
print(result)
```

### Load into PostgreSQL

```python
import pandas as pd
import psycopg

df = pd.read_csv('covid_papers_data.csv')

with psycopg.connect("host=localhost dbname=etldb user=postgres") as conn:
    with conn.cursor() as cur:
        # Create table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS json_metadata (
                file_name TEXT,
                key TEXT,
                value_type TEXT,
                value_preview TEXT
            )
        """)
        
        # Insert data
        for _, row in df.iterrows():
            cur.execute(
                "INSERT INTO json_metadata VALUES (%s, %s, %s, %s)",
                tuple(row)
            )
    conn.commit()
```

---

## ✨ Summary

**Simple export:**
```bash
python fetch_db.py
```

**Programmatic export:**
```python
analyzer.save_json_to_csv(num_files=100, output_file='my_data.csv')
```

**Analyze:**
```python
df = pd.read_csv('my_data.csv')
print(df.head())
```

That's it! 🎉

