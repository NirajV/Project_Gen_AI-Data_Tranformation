"""
Automated SCD Type 2 Pipeline
==============================
A metadata-driven Python engine for implementing Slowly Changing Dimension (SCD) Type 2
data transformation with SQLite.

Author: Data Engineering Team
Version: 2.0
Date: January 19, 2026
"""

import sqlite3
import json
import hashlib
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================
DB_NAME = "./data/test_database.db"
SOURCE_TABLE = "sales_records"
TARGET_TABLE = f"{SOURCE_TABLE}_cdc"


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def generate_hash(row, attributes):
    """
    Creates a unique hash for the changing fields to detect updates.
    
    Args:
        row (dict): Row data from database
        attributes (list): List of column names to include in hash
        
    Returns:
        str: MD5 hash of concatenated attribute values
        
    Example:
        >>> row = {"id": 1, "product_name": "Laptop", "price": 999.99}
        >>> attrs = ["product_name", "price"]
        >>> hash_value = generate_hash(row, attrs)
    """
    combined_string = "-".join([str(row[attr]) for attr in attributes])
    return hashlib.md5(combined_string.encode()).hexdigest()


def run_scd_pipeline(config_path):
    """
    Main SCD Type 2 pipeline execution function.
    
    Process Flow:
    1. Load metadata configuration from JSON file
    2. Connect to SQLite database
    3. Extract source data
    4. Generate hashes for change detection
    5. Compare with CDC table to identify changes
    6. Insert new records or update changed records
    7. Maintain historical versions with temporal tracking
    8. Generate processing summary report
    
    Args:
        config_path (str): Path to config.json file
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        sqlite3.Error: If database operations fail
        KeyError: If required config keys are missing
    """
    print("=" * 60)
    print("Starting SCD Type 2 Pipeline")
    print("=" * 60)
    
    # ========================================================================
    # STEP 1: Load Metadata Configuration
    # ========================================================================
    print(f"\n[1/6] Loading configuration from {config_path}")
    try:
        with open(config_path, 'r') as f:
            conf = json.load(f)
    except FileNotFoundError:
        print(f"   ✗ ERROR: Configuration file '{config_path}' not found!")
        raise
    except json.JSONDecodeError as e:
        print(f"   ✗ ERROR: Invalid JSON in configuration file: {e}")
        raise
    
    # Validate configuration
    if 'primary_key' not in conf:
        raise KeyError("'primary_key' is required in configuration file")
    if 'changing_attributes' not in conf:
        raise KeyError("'changing_attributes' is required in configuration file")
    
    pk = conf['primary_key']
    changing_attrs = conf['changing_attributes']
    print(f"   ✓ Primary Key: {pk}")
    print(f"   ✓ Monitoring Columns: {', '.join(changing_attrs)}")

    # ========================================================================
    # STEP 2: Connect to Database
    # ========================================================================
    print(f"\n[2/6] Connecting to database: {DB_NAME}")
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # Access columns by name
        cursor = conn.cursor()
        print(f"   ✓ Database connection established")
    except sqlite3.Error as e:
        print(f"   ✗ ERROR: Failed to connect to database: {e}")
        raise

    # ========================================================================
    # STEP 3: Extract Source Data
    # ========================================================================
    print(f"\n[3/6] Extracting data from {SOURCE_TABLE}")
    try:
        cursor.execute(f"SELECT * FROM {SOURCE_TABLE}")
        source_rows = [dict(row) for row in cursor.fetchall()]
        print(f"   ✓ Found {len(source_rows)} records in source table")
    except sqlite3.Error as e:
        print(f"   ✗ ERROR: Failed to extract source data: {e}")
        conn.close()
        raise

    # ========================================================================
    # STEP 4: Process Each Row - Change Detection & Loading
    # ========================================================================
    print(f"\n[4/6] Processing records and detecting changes")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expiry_time = "9999-12-31 23:59:59"
    
    # Counters for summary
    new_count = 0
    changed_count = 0
    unchanged_count = 0

    try:
        for src_row in source_rows:
            src_pk_val = src_row[pk]
            src_hash = generate_hash(src_row, changing_attrs)

            # Check for the latest active version in the CDC table
            cursor.execute(f"""
                SELECT row_hash FROM {TARGET_TABLE} 
                WHERE {pk} = ? AND is_current = 1
            """, (src_pk_val,))
            tgt_record = cursor.fetchone()

            # ================================================================
            # SCENARIO 1: NEW RECORD
            # ================================================================
            if tgt_record is None:
                cols = list(src_row.keys()) + ['row_hash', 'row_start_date', 'row_end_date', 'is_current']
                placeholders = ", ".join(["?"] * len(cols))
                vals = list(src_row.values()) + [src_hash, current_time, expiry_time, 1]
                
                cursor.execute(
                    f"INSERT INTO {TARGET_TABLE} ({', '.join(cols)}) VALUES ({placeholders})", 
                    vals
                )
                new_count += 1
                print(f"   ✓ NEW: {pk}={src_pk_val}")

            # ================================================================
            # SCENARIO 2: CHANGED RECORD
            # ================================================================
            elif tgt_record['row_hash'] != src_hash:
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
                
                cursor.execute(
                    f"INSERT INTO {TARGET_TABLE} ({', '.join(cols)}) VALUES ({placeholders})", 
                    vals
                )
                changed_count += 1
                print(f"   ✓ CHANGED: {pk}={src_pk_val}")
            
            # ================================================================
            # SCENARIO 3: NO CHANGE
            # ================================================================
            else:
                unchanged_count += 1

    except sqlite3.Error as e:
        print(f"   ✗ ERROR: Failed during record processing: {e}")
        conn.rollback()
        conn.close()
        raise

    # ========================================================================
    # STEP 5: Commit Changes
    # ========================================================================
    print(f"\n[5/6] Committing changes to database")
    try:
        conn.commit()
        print(f"   ✓ Changes committed successfully")
    except sqlite3.Error as e:
        print(f"   ✗ ERROR: Failed to commit changes: {e}")
        conn.rollback()
        conn.close()
        raise
    
    # ========================================================================
    # STEP 6: Close Database Connection
    # ========================================================================
    print(f"\n[6/6] Closing database connection")
    conn.close()
    print(f"   ✓ Database connection closed")
    
    # ========================================================================
    # SUMMARY REPORT
    # ========================================================================
    print("\n" + "=" * 60)
    print("SCD Type 2 Pipeline Complete")
    print("=" * 60)
    print(f"📊 Processing Summary:")
    print(f"   • New Records:       {new_count}")
    print(f"   • Changed Records:   {changed_count}")
    print(f"   • Unchanged Records: {unchanged_count}")
    print(f"   • Total Processed:   {len(source_rows)}")
    print(f"   • Execution Time:    {current_time}")
    print("=" * 60)
    
    return {
        'new_count': new_count,
        'changed_count': changed_count,
        'unchanged_count': unchanged_count,
        'total_count': len(source_rows)
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    try:
        run_scd_pipeline("config.json")
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        exit(1)
