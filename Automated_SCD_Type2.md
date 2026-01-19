# Automated SCD Type 2 Implementation

## Overview
This document outlines the implementation of an automated Slowly Changing Dimension (SCD) Type 2 process using a metadata-driven Python engine with SQLite database.

---

## Phase 1: Environment Setup

### Step 1: Configure the Environment
Configure the environment using the `.env` parameters provided.

### Step 2: Automatic Table Targeting
The script will automatically target the base table (`sales_records`) and its historical counterpart (`sales_records_cdc`).

### Step 3: SCD Column Requirements
Ensure the `_cdc` table includes SCD columns:
- `row_start_date`
- `row_end_date`
- `is_current`

---

## SQL DDL Script for CDC Table Setup

Before running the Python script, you must create the `sales_records_cdc` table with the proper schema including all audit columns.

### Create sales_records_cdc Table

```sql
-- Drop existing table if needed (for clean setup)
DROP TABLE IF EXISTS sales_records_cdc;

-- Create the CDC table with source columns + SCD Type 2 audit columns
CREATE TABLE sales_records_cdc (
    -- Business columns (adjust based on your sales_records schema)
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

### Alternative: Create sales_records_cdc with AUTO_INCREMENT Surrogate Key

If you prefer a single-column primary key:

```sql
-- Drop existing table if needed
DROP TABLE IF EXISTS sales_records_cdc;

-- Create CDC table with surrogate key
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

-- Create indexes for performance
CREATE INDEX idx_cdc_is_current ON sales_records_cdc(is_current);
CREATE INDEX idx_cdc_id_current ON sales_records_cdc(id, is_current);
CREATE INDEX idx_cdc_row_hash ON sales_records_cdc(row_hash);
CREATE INDEX idx_cdc_dates ON sales_records_cdc(row_start_date, row_end_date);
```

### Column Descriptions

**Business Columns:**
- `id`: Primary key from the source table
- `transaction_date`, `product_name`, `category`, etc.: Business data columns from source

**SCD Type 2 Audit Columns:**
- `row_hash`: MD5 hash of changing attributes for efficient change detection
- `row_start_date`: Timestamp when this version of the record became effective
- `row_end_date`: Timestamp when this version expired ('9999-12-31 23:59:59' for current records)
- `is_current`: Flag indicating if this is the current active version (1 = current, 0 = historical)

### Important Notes

1. **Adjust Business Columns**: Modify the business columns in the DDL to match your actual `sales_records` table schema
2. **Run Before Python Script**: Execute this DDL script before running the Python SCD pipeline
3. **Indexes**: The indexes improve query performance for common SCD operations
4. **Data Types**: SQLite uses dynamic typing, but TEXT is used for dates to match Python datetime formatting

---

## Phase 2: Metadata-Driven Python Engine

### Step 4: JSON Config Loading
The script reads the `config.json` to identify which columns in `sales_records` need to be monitored for changes.

### Step 5: Extract & Hash

**Load the source table:**
- Extract data from the source table

**Generate MD5 Hash:**
- Generate an MD5 Hash of the "Changing Attributes" to detect updates efficiently

### Step 6: Delta Detection

**New Records:**
- IDs in source not present in `_cdc`

**Changed Records:**
- IDs present in both, but the Hash is different

### Step 7: The Load

**Close Out:**
- Update `is_current` to `False` and set the `row_end_date` for old versions of changed records

**Insert:**
- Append new records and the new versions of updated records

---

## Phase 3: Cleanup

### Step 8: Cleanup Operations
Close database connections and log the number of processed records.

---

## Python Implementation (Python + SQLite)

This script uses standard Python libraries to interact with your SQLite database and handle the SCD logic.

```python
import sqlite3
import json
import hashlib
from datetime import datetime

# 1. Environment Config (from your .env)
DB_NAME = "./data/test_database.db"
SOURCE_TABLE = "sales_records"
TARGET_TABLE = f"{SOURCE_TABLE}_cdc"

def generate_hash(row, attributes):
    """Creates a unique hash for the changing fields to detect updates."""
    combined_string = "-".join([str(row[attr]) for attr in attributes])
    return hashlib.md5(combined_string.encode()).hexdigest()

def run_scd_pipeline(config_path):
    # 2. Load Metadata Config
    with open(config_path, 'r') as f:
        conf = json.load(f)
    
    pk = conf['primary_key']
    changing_attrs = conf['changing_attributes']

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()

    # 3. Get Source Data
    cursor.execute(f"SELECT * FROM {SOURCE_TABLE}")
    source_rows = [dict(row) for row in cursor.fetchall()]

    # 4. Process each row from Source
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expiry_time = "9999-12-31 23:59:59"

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
            # SCENARIO: NEW RECORD
            cols = list(src_row.keys()) + ['row_hash', 'row_start_date', 'row_end_date', 'is_current']
            placeholders = ", ".join(["?"] * len(cols))
            vals = list(src_row.values()) + [src_hash, current_time, expiry_time, 1]
            
            cursor.execute(f"INSERT INTO {TARGET_TABLE} ({', '.join(cols)}) VALUES ({placeholders})", vals)

        elif tgt_record['row_hash'] != src_hash:
            # SCENARIO: CHANGED RECORD
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

    conn.commit()
    conn.close()
    print(f"SCD Type 2 complete for {TARGET_TABLE}")

if __name__ == "__main__":
    run_scd_pipeline("config.json")
```

---

## Key Features

1. **Metadata-Driven Approach**: Configuration through JSON files makes the solution flexible and reusable
2. **Efficient Change Detection**: MD5 hashing enables quick identification of changed records
3. **SCD Type 2 Implementation**: Maintains full historical records with temporal tracking
4. **Simple Dependencies**: Uses only standard Python libraries (sqlite3, json, hashlib, datetime)

## Configuration Example

The `config.json` should follow this structure:

```json
{
    "primary_key": "id",
    "changing_attributes": ["product_name", "price", "quantity", "status"]
}
```

## Database Schema

**Source Table: sales_records**
- Contains the current state of records
- Standard columns based on business requirements

**CDC Table: sales_records_cdc**
- All columns from source table
- Additional SCD columns:
  - `row_hash`: MD5 hash for change detection
  - `row_start_date`: When this version became active
  - `row_end_date`: When this version expired (9999-12-31 for current records)
  - `is_current`: Boolean flag (1 for current, 0 for historical)
