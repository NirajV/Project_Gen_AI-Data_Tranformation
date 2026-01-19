# Automated SCD Type 2 Implementation - Step by Step Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Understanding SCD Type 2](#understanding-scd-type-2)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Testing & Validation](#testing--validation)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Features](#advanced-features)

---

## Overview

This document provides a comprehensive step-by-step guide for implementing an automated Slowly Changing Dimension (SCD) Type 2 process using a metadata-driven Python engine with SQLite database.

### What is SCD Type 2?

SCD Type 2 is a data warehousing technique that tracks historical changes by creating a new record for each change while preserving the complete history. Each record includes:
- **Effective dates**: When the record version became active and when it expired
- **Current flag**: Indicates if this is the latest version
- **Hash key**: For efficient change detection

### Key Benefits

- ✅ **Full Historical Tracking**: Maintain complete history of all changes
- ✅ **Metadata-Driven**: Flexible configuration through JSON
- ✅ **Efficient Change Detection**: MD5 hashing for quick comparisons
- ✅ **Standard Python**: No external dependencies required

---

## Prerequisites

### 1. Software Requirements

- **Python**: Version 3.6 or higher
- **SQLite**: Built-in with Python (no separate installation needed)
- **Standard Libraries**: `sqlite3`, `json`, `hashlib`, `datetime` (all included with Python)

### 2. File Structure

Create the following directory structure:

```
Data_Tranformation/
├── data/
│   └── test_database.db          # SQLite database file
├── config.json                    # Metadata configuration
├── scd_pipeline.py                # Main Python script
└── Automated_SCD_Type2.md        # This documentation
```

### 3. Required Files

1. **Database**: SQLite database with source and CDC tables
2. **Configuration**: JSON file defining primary keys and changing attributes
3. **Python Script**: The SCD Type 2 implementation code

---

## Understanding SCD Type 2

### Example Scenario

**Original Record:**
```
ID: 101, Product: "Laptop", Price: 999.99, Status: "Active"
```

**After Price Change:**
```
Record 1 (Historical):
ID: 101, Product: "Laptop", Price: 999.99, Status: "Active"
row_start_date: 2024-01-01, row_end_date: 2024-06-15, is_current: 0

Record 2 (Current):
ID: 101, Product: "Laptop", Price: 1299.99, Status: "Active"
row_start_date: 2024-06-15, row_end_date: 9999-12-31, is_current: 1
```

This approach allows you to:
- Query current state (where is_current = 1)
- Query historical state at any point in time
- Track when changes occurred
- Analyze trends over time

---

## Step-by-Step Implementation

### Phase 1: Environment Setup

#### Step 1: Create the Configuration File

Create `config.json` in your project root:

```json
{
    "primary_key": "id",
    "changing_attributes": ["product_name", "price", "quantity", "status"]
}
```

**Configuration Parameters:**
- `primary_key`: The unique identifier column in your source table
- `changing_attributes`: List of columns to monitor for changes (excludes the primary key)

#### Step 2: Create the Source Table

First, create your source table `sales_records`:

```sql
-- Create source table
CREATE TABLE IF NOT EXISTS sales_records (
    id INTEGER PRIMARY KEY,
    transaction_date TEXT,
    product_name TEXT,
    category TEXT,
    price REAL,
    quantity INTEGER,
    total_amount REAL,
    customer_id INTEGER,
    region TEXT,
    status TEXT
);

-- Insert sample data
INSERT INTO sales_records VALUES 
(1, '2024-01-15', 'Laptop Pro', 'Electronics', 1299.99, 1, 1299.99, 1001, 'North', 'Active'),
(2, '2024-01-16', 'Mouse Wireless', 'Accessories', 29.99, 2, 59.98, 1002, 'South', 'Active'),
(3, '2024-01-17', 'Keyboard Mechanical', 'Accessories', 89.99, 1, 89.99, 1003, 'East', 'Active');
```

#### Step 3: Create the CDC Table with SCD Columns

Create the `sales_records_cdc` table with all required audit columns:

```sql
-- Drop existing table if needed (for clean setup)
DROP TABLE IF EXISTS sales_records_cdc;

-- Create the CDC table with source columns + SCD Type 2 audit columns
CREATE TABLE sales_records_cdc (
    -- Business columns (matching sales_records schema)
    id INTEGER NOT NULL,
    transaction_date TEXT,
    product_name TEXT,
    category TEXT,
    price REAL,
    quantity INTEGER,
    total_amount REAL,
    customer_id INTEGER,
    region TEXT,
    status TEXT,
    
    -- SCD Type 2 Audit Columns
    row_hash TEXT NOT NULL,
    row_start_date TEXT NOT NULL,
    row_end_date TEXT NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 1,
    
    -- Composite primary key to allow multiple versions of the same record
    PRIMARY KEY (id, row_start_date)
);

-- Create indexes for performance optimization
CREATE INDEX idx_cdc_is_current ON sales_records_cdc(is_current);
CREATE INDEX idx_cdc_id_current ON sales_records_cdc(id, is_current);
CREATE INDEX idx_cdc_row_hash ON sales_records_cdc(row_hash);
```

**Alternative with Surrogate Key:**

```sql
-- Create CDC table with auto-incrementing surrogate key
CREATE TABLE sales_records_cdc (
    -- Surrogate key for CDC table
    cdc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Business columns (from sales_records)
    id INTEGER NOT NULL,
    transaction_date TEXT,
    product_name TEXT,
    category TEXT,
    price REAL,
    quantity INTEGER,
    total_amount REAL,
    customer_id INTEGER,
    region TEXT,
    status TEXT,
    
    -- SCD Type 2 Audit Columns
    row_hash TEXT NOT NULL,
    row_start_date TEXT NOT NULL,
    row_end_date TEXT NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 1
);

-- Create indexes
CREATE INDEX idx_cdc_is_current ON sales_records_cdc(is_current);
CREATE INDEX idx_cdc_id_current ON sales_records_cdc(id, is_current);
CREATE INDEX idx_cdc_row_hash ON sales_records_cdc(row_hash);
CREATE INDEX idx_cdc_dates ON sales_records_cdc(row_start_date, row_end_date);
```

**Column Descriptions:**

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key from source table |
| `row_hash` | TEXT | MD5 hash of changing attributes for change detection |
| `row_start_date` | TEXT | When this version became effective |
| `row_end_date` | TEXT | When this version expired ('9999-12-31 23:59:59' for current) |
| `is_current` | INTEGER | Flag: 1 = current version, 0 = historical |

---

### Phase 2: Metadata-Driven Python Engine

#### Step 4: Create the Python Script

Create `scd_pipeline.py`:

```python
import sqlite3
import json
import hashlib
from datetime import datetime

# 1. Environment Configuration
DB_NAME = "./data/test_database.db"
SOURCE_TABLE = "sales_records"
TARGET_TABLE = f"{SOURCE_TABLE}_cdc"

def generate_hash(row, attributes):
    """
    Creates a unique hash for the changing fields to detect updates.
    
    Args:
        row (dict): Row data from database
        attributes (list): List of column names to include in hash
        
    Returns:
        str: MD5 hash of concatenated attribute values
    """
    combined_string = "-".join([str(row[attr]) for attr in attributes])
    return hashlib.md5(combined_string.encode()).hexdigest()

def run_scd_pipeline(config_path):
    """
    Main SCD Type 2 pipeline execution function.
    
    Process:
    1. Load metadata configuration
    2. Extract source data
    3. Generate hashes for change detection
    4. Compare with CDC table
    5. Insert new records or update changed records
    6. Maintain historical versions
    
    Args:
        config_path (str): Path to config.json file
    """
    print("=" * 60)
    print("Starting SCD Type 2 Pipeline")
    print("=" * 60)
    
    # 2. Load Metadata Config
    print(f"\n[1/6] Loading configuration from {config_path}")
    with open(config_path, 'r') as f:
        conf = json.load(f)
    
    pk = conf['primary_key']
    changing_attrs = conf['changing_attributes']
    print(f"   Primary Key: {pk}")
    print(f"   Monitoring Columns: {', '.join(changing_attrs)}")

    # 3. Connect to Database
    print(f"\n[2/6] Connecting to database: {DB_NAME}")
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()

    # 4. Extract Source Data
    print(f"\n[3/6] Extracting data from {SOURCE_TABLE}")
    cursor.execute(f"SELECT * FROM {SOURCE_TABLE}")
    source_rows = [dict(row) for row in cursor.fetchall()]
    print(f"   Found {len(source_rows)} records in source table")

    # 5. Process Each Row
    print(f"\n[4/6] Processing records and detecting changes")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expiry_time = "9999-12-31 23:59:59"
    
    new_count = 0
    changed_count = 0
    unchanged_count = 0

    for src_row in source_rows:
        src_pk_val = src_row[pk]
        src_hash = generate_hash(src_row, changing_attrs)

        # Check for the latest active version in the CDC table
        cursor.execute(f"""
            SELECT row_hash FROM {TARGET_TABLE} 
            WHERE {pk} = ? AND is_current = 1
        """, (src_pk_val,))
        tgt_record = cursor.fetchone()

        if tgt_record is None:
            # SCENARIO 1: NEW RECORD
            cols = list(src_row.keys()) + ['row_hash', 'row_start_date', 'row_end_date', 'is_current']
            placeholders = ", ".join(["?"] * len(cols))
            vals = list(src_row.values()) + [src_hash, current_time, expiry_time, 1]
            
            cursor.execute(f"INSERT INTO {TARGET_TABLE} ({', '.join(cols)}) VALUES ({placeholders})", vals)
            new_count += 1
            print(f"   ✓ NEW: {pk}={src_pk_val}")

        elif tgt_record['row_hash'] != src_hash:
            # SCENARIO 2: CHANGED RECORD
            # A. Expire the old record
            cursor.execute(f"""
                UPDATE {TARGET_TABLE} 
                SET row_end_date = ?, is_current = 0 
                WHERE {pk} = ? AND is_current = 1
            """, (current_time, src_pk_val))

            # B. Insert the new version
            cols = list(src_row.keys()) + ['row_hash', 'row_start_date', 'row_end_date', 'is_current']
            placeholders = ", ".join(["?"] * len(cols))
            vals = list(src_row.values()) + [src_hash, current_time, expiry_time, 1]
            
            cursor.execute(f"INSERT INTO {TARGET_TABLE} ({', '.join(cols)}) VALUES ({placeholders})", vals)
            changed_count += 1
            print(f"   ✓ CHANGED: {pk}={src_pk_val}")
        else:
            # SCENARIO 3: NO CHANGE
            unchanged_count += 1

    # 6. Commit and Close
    print(f"\n[5/6] Committing changes to database")
    conn.commit()
    
    print(f"\n[6/6] Closing database connection")
    conn.close()
    
    # 7. Summary
    print("\n" + "=" * 60)
    print("SCD Type 2 Pipeline Complete")
    print("=" * 60)
    print(f"📊 Processing Summary:")
    print(f"   • New Records:       {new_count}")
    print(f"   • Changed Records:   {changed_count}")
    print(f"   • Unchanged Records: {unchanged_count}")
    print(f"   • Total Processed:   {len(source_rows)}")
    print("=" * 60)

if __name__ == "__main__":
    run_scd_pipeline("config.json")
```

#### Step 5: Understanding the Delta Detection Logic

The script implements three scenarios:

**Scenario 1: New Records**
- **Detection**: ID exists in source but NOT in CDC table
- **Action**: Insert new record with is_current=1

**Scenario 2: Changed Records**
- **Detection**: ID exists in both, but hash values differ
- **Action**: 
  1. Update old record: set is_current=0 and row_end_date=current_time
  2. Insert new version: with is_current=1 and row_start_date=current_time

**Scenario 3: Unchanged Records**
- **Detection**: ID exists in both with matching hashes
- **Action**: No operation needed

---

### Phase 3: Execution and Validation

#### Step 6: Run the Pipeline

Execute the script from your terminal:

```bash
# Navigate to your project directory
cd c:/Users/niraj/Project_Gen_AI/Data_Tranformation

# Run the SCD pipeline
python scd_pipeline.py
```

**Expected Output:**

```
============================================================
Starting SCD Type 2 Pipeline
============================================================

[1/6] Loading configuration from config.json
   Primary Key: id
   Monitoring Columns: product_name, price, quantity, status

[2/6] Connecting to database: ./data/test_database.db

[3/6] Extracting data from sales_records
   Found 3 records in source table

[4/6] Processing records and detecting changes
   ✓ NEW: id=1
   ✓ NEW: id=2
   ✓ NEW: id=3

[5/6] Committing changes to database

[6/6] Closing database connection

============================================================
SCD Type 2 Pipeline Complete
============================================================
📊 Processing Summary:
   • New Records:       3
   • Changed Records:   0
   • Unchanged Records: 0
   • Total Processed:   3
============================================================
```

---

## Testing & Validation

### Step 7: Validate the Initial Load

Query the CDC table to verify records were inserted:

```sql
-- View all records in CDC table
SELECT 
    id,
    product_name,
    price,
    status,
    row_start_date,
    row_end_date,
    is_current
FROM sales_records_cdc
ORDER BY id, row_start_date;
```

### Step 8: Test Change Detection

#### 8.1 Update Source Data

```sql
-- Update price for product ID 1
UPDATE sales_records 
SET price = 1399.99, total_amount = 1399.99
WHERE id = 1;

-- Update status for product ID 2
UPDATE sales_records 
SET status = 'Inactive'
WHERE id = 2;
```

#### 8.2 Run Pipeline Again

```bash
python scd_pipeline.py
```

**Expected Output:**
```
[4/6] Processing records and detecting changes
   ✓ CHANGED: id=1
   ✓ CHANGED: id=2

📊 Processing Summary:
   • New Records:       0
   • Changed Records:   2
   • Unchanged Records: 1
   • Total Processed:   3
```

#### 8.3 Verify Historical Tracking

```sql
-- Query all versions of product ID 1
SELECT 
    id,
    product_name,
    price,
    row_start_date,
    row_end_date,
    is_current
FROM sales_records_cdc
WHERE id = 1
ORDER BY row_start_date;
```

**Expected Result:**
```
id | product_name | price    | row_start_date      | row_end_date        | is_current
---|--------------|----------|---------------------|---------------------|------------
1  | Laptop Pro   | 1299.99  | 2024-01-15 10:00:00 | 2024-01-15 11:30:00 | 0
1  | Laptop Pro   | 1399.99  | 2024-01-15 11:30:00 | 9999-12-31 23:59:59 | 1
```

### Step 9: Query Historical Data

#### Get Current State Only

```sql
-- View only current active records
SELECT 
    id,
    product_name,
    price,
    quantity,
    status
FROM sales_records_cdc
WHERE is_current = 1;
```

#### Get Full History

```sql
-- View complete history with version information
SELECT 
    id,
    product_name,
    price,
    row_start_date,
    row_end_date,
    CASE 
        WHEN is_current = 1 THEN 'Current'
        ELSE 'Historical'
    END as version_status
FROM sales_records_cdc
ORDER BY id, row_start_date DESC;
```

#### Point-in-Time Query

```sql
-- Query data as it existed on a specific date
SELECT 
    id,
    product_name,
    price,
    status
FROM sales_records_cdc
WHERE '2024-01-15 10:30:00' BETWEEN row_start_date AND row_end_date;
```

#### Track Price Changes Over Time

```sql
-- Analyze price changes for a specific product
SELECT 
    id,
    product_name,
    price as old_price,
    LEAD(price) OVER (PARTITION BY id ORDER BY row_start_date) as new_price,
    row_start_date as change_date,
    ROUND(
        (LEAD(price) OVER (PARTITION BY id ORDER BY row_start_date) - price) / price * 100,
        2
    ) as price_change_pct
FROM sales_records_cdc
WHERE id = 1;
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: "Table already exists" Error

**Error:**
```
sqlite3.OperationalError: table sales_records_cdc already exists
```

**Solution:**
```sql
-- Drop and recreate the table
DROP TABLE IF EXISTS sales_records_cdc;
-- Then run the CREATE TABLE statement again
```

#### Issue 2: "No such column" Error

**Error:**
```
sqlite3.OperationalError: table sales_records_cdc has no column named row_hash
```

**Solution:**
Ensure the CDC table includes ALL columns from the source table PLUS the audit columns. Verify your CREATE TABLE statement matches your source schema.

#### Issue 3: All Records Detected as "Changed" Every Run

**Cause:** Column ordering mismatch or data type inconsistencies

**Solution:**
```python
# Debug: Print hash values
print(f"Source Hash: {src_hash}")
print(f"Target Hash: {tgt_record['row_hash'] if tgt_record else 'None'}")
```

Ensure:
- Column names in `changing_attributes` match exactly (case-sensitive)
- Data types are consistent (NULL vs empty string, etc.)
- Date/time formats are standardized

#### Issue 4: Config File Not Found

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'config.json'
```

**Solution:**
- Verify `config.json` is in the same directory as `scd_pipeline.py`
- Use absolute path if needed: `run_scd_pipeline("C:/path/to/config.json")`

#### Issue 5: Database Lock Error

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
- Close any other connections to the database
- Close SQLite browser/viewer tools
- Ensure no other scripts are running

---

## Advanced Features

### 1. Add Deleted Record Detection

Track records that exist in CDC but not in source:

```python
def detect_deleted_records(cursor, pk, source_rows, current_time):
    """Mark records as deleted if they no longer exist in source."""
    source_ids = {row[pk] for row in source_rows}
    
    cursor.execute(f"""
        SELECT DISTINCT {pk} FROM {TARGET_TABLE} WHERE is_current = 1
    """)
    cdc_ids = {row[0] for row in cursor.fetchall()}
    
    deleted_ids = cdc_ids - source_ids
    
    for del_id in deleted_ids:
        cursor.execute(f"""
            UPDATE {TARGET_TABLE}
            SET row_end_date = ?, is_current = 0
            WHERE {pk} = ? AND is_current = 1
        """, (current_time, del_id))
    
    return len(deleted_ids)
```

### 2. Add Logging to File

```python
import logging

logging.basicConfig(
    filename='scd_pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# In your code:
logging.info(f"Processing {len(source_rows)} records")
logging.warning(f"Changed record detected: {pk}={src_pk_val}")
```

### 3. Add Performance Metrics

```python
import time

start_time = time.time()
# ... your pipeline code ...
end_time = time.time()

print(f"⏱️  Execution Time: {end_time - start_time:.2f} seconds")
```

### 4. Support Multiple Tables

```python
# config.json
{
    "tables": [
        {
            "source": "sales_records",
            "target": "sales_records_cdc",
            "primary_key": "id",
            "changing_attributes": ["product_name", "price", "quantity", "status"]
        },
        {
            "source": "customers",
            "target": "customers_cdc",
            "primary_key": "customer_id",
            "changing_attributes": ["name", "email", "phone"]
        }
    ]
}
```

### 5. Add Email Notifications

```python
import smtplib
from email.mime.text import MIMEText

def send_notification(summary):
    """Send email notification with pipeline results."""
    msg = MIMEText(f"Pipeline complete.\n{summary}")
    msg['Subject'] = 'SCD Pipeline Notification'
    msg['From'] = 'pipeline@example.com'
    msg['To'] = 'admin@example.com'
    
    # Configure and send email
    # ...
```

---

## Best Practices

### 1. Schedule Regular Runs

Use Windows Task Scheduler or cron (Linux/Mac):

**Windows Task Scheduler:**
```bash
# Run daily at 2 AM
schtasks /create /tn "SCD Pipeline" /tr "python C:\path\to\scd_pipeline.py" /sc daily /st 02:00
```

**Linux/Mac Cron:**
```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/project && python scd_pipeline.py >> logs/pipeline.log 2>&1
```

### 2. Backup Before Major Changes

```bash
# Backup database before running
sqlite3 ./data/test_database.db ".backup './data/test_database_backup.db'"
```

### 3. Monitor Table Growth

```sql
-- Check CDC table size
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT id) as unique_ids,
    COUNT(*) * 1.0 / COUNT(DISTINCT id) as avg_versions_per_id
FROM sales_records_cdc;
```

### 4. Archive Old Historical Data

```sql
-- Archive records older than 2 years
CREATE TABLE sales_records_cdc_archive AS
SELECT * FROM sales_records_cdc
WHERE row_end_date < date('now', '-2 years') AND is_current = 0;

-- Delete archived records
DELETE FROM sales_records_cdc
WHERE row_end_date < date('now', '-2 years') AND is_current = 0;
```

---

## Summary

This implementation provides a robust, metadata-driven SCD Type 2 solution that:

✅ Automatically tracks all changes to your data  
✅ Maintains complete historical records  
✅ Uses efficient MD5 hashing for change detection  
✅ Requires only standard Python libraries  
✅ Is easily configurable through JSON  
✅ Provides detailed logging and reporting  

### Next Steps

1. **Customize** the source table schema to match your data
2. **Configure** the `config.json` with your changing attributes
3. **Test** thoroughly with sample data
4. **Schedule** regular pipeline runs
5. **Monitor** and optimize performance as needed

For questions or issues, refer to the [Troubleshooting](#troubleshooting) section.

---

**Document Version:** 2.0  
**Last Updated:** January 19, 2026  
**Author:** Data Engineering Team
