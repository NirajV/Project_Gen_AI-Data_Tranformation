"""
Database Setup Helper Script
=============================
Automates the creation of SQLite database and tables for SCD Type 2 implementation.

This script:
1. Creates the data directory if it doesn't exist
2. Creates the SQLite database
3. Executes the setup_database.sql script
4. Verifies the setup was successful

Author: Data Engineering Team
Version: 2.0
Date: January 19, 2026
"""

import sqlite3
import os
import sys

# ============================================================================
# CONFIGURATION
# ============================================================================
DATA_DIR = "./data"
DB_PATH = os.path.join(DATA_DIR, "scdType_db.db")
SQL_SCRIPT = "setup_database.sql"


# ============================================================================
# FUNCTIONS
# ============================================================================

def create_directory(dir_path):
    """
    Create directory if it doesn't exist.
    
    Args:
        dir_path (str): Directory path to create
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"✓ Created directory: {dir_path}")
    else:
        print(f"✓ Directory already exists: {dir_path}")


def execute_sql_script(db_path, script_path):
    """
    Execute SQL script file against the database.
    
    Args:
        db_path (str): Path to SQLite database file
        script_path (str): Path to SQL script file
        
    Raises:
        FileNotFoundError: If SQL script file doesn't exist
        sqlite3.Error: If database operations fail
    """
    # Check if SQL script exists
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"SQL script not found: {script_path}")
    
    # Read SQL script
    print(f"\n📄 Reading SQL script: {script_path}")
    with open(script_path, 'r') as f:
        sql_script = f.read()
    
    # Connect to database and execute script
    print(f"📊 Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print(f"⚙️  Executing SQL script...")
        cursor.executescript(sql_script)
        conn.commit()
        print(f"✓ SQL script executed successfully")
    except sqlite3.Error as e:
        print(f"✗ ERROR: Failed to execute SQL script: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def verify_setup(db_path):
    """
    Verify database setup by checking tables and data.
    
    Args:
        db_path (str): Path to SQLite database file
    """
    print(f"\n🔍 Verifying database setup...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('sales_records_current', 'sales_records_cdc')
        """)
        tables = cursor.fetchall()
        
        if len(tables) == 2:
            print(f"✓ Both tables created successfully:")
            print(f"  - sales_records_current")
            print(f"  - sales_records_cdc")
        else:
            print(f"✗ WARNING: Expected 2 tables, found {len(tables)}")
            return False
        
        # Check source table record count
        cursor.execute("SELECT COUNT(*) FROM sales_records_current")
        source_count = cursor.fetchone()[0]
        print(f"✓ Source table has {source_count} records")
        
        # Check CDC table structure
        cursor.execute("PRAGMA table_info(sales_records_cdc)")
        cdc_columns = cursor.fetchall()
        audit_columns = [col[1] for col in cdc_columns if col[1] in 
                        ['row_hash', 'row_start_date', 'row_end_date', 'is_current']]
        
        if len(audit_columns) == 4:
            print(f"✓ CDC table has all required SCD Type 2 audit columns:")
            print(f"  - row_hash")
            print(f"  - row_start_date")
            print(f"  - row_end_date")
            print(f"  - is_current")
        else:
            print(f"✗ WARNING: Missing some audit columns")
            return False
        
        # Check indexes
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND tbl_name='sales_records_cdc'
        """)
        indexes = cursor.fetchall()
        print(f"✓ Created {len(indexes)} indexes on CDC table")
        
        return True
        
    except sqlite3.Error as e:
        print(f"✗ ERROR during verification: {e}")
        return False
    finally:
        conn.close()


def main():
    """Main execution function."""
    print("=" * 70)
    print("Automated SCD Type 2 - Database Setup")
    print("=" * 70)
    
    try:
        # Step 1: Create data directory
        print(f"\n[1/4] Creating data directory...")
        create_directory(DATA_DIR)
        
        # Step 2: Check if database already exists
        print(f"\n[2/4] Checking database status...")
        if os.path.exists(DB_PATH):
            response = input(f"⚠️  Database already exists at {DB_PATH}. Overwrite? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("❌ Setup cancelled by user")
                sys.exit(0)
            else:
                os.remove(DB_PATH)
                print(f"✓ Removed existing database")
        
        # Step 3: Execute SQL script
        print(f"\n[3/4] Setting up database...")
        execute_sql_script(DB_PATH, SQL_SCRIPT)
        
        # Step 4: Verify setup
        print(f"\n[4/4] Verifying setup...")
        if verify_setup(DB_PATH):
            print("\n" + "=" * 70)
            print("✅ Database Setup Complete!")
            print("=" * 70)
            print(f"\n📂 Database Location: {os.path.abspath(DB_PATH)}")
            print(f"\n🚀 Next Steps:")
            print(f"   1. Review config.json to ensure it matches your requirements")
            print(f"   2. Run the SCD pipeline: python scd_pipeline.py")
            print("=" * 70)
            return 0
        else:
            print("\n❌ Setup verification failed. Please check the error messages above.")
            return 1
            
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
        print(f"   Make sure {SQL_SCRIPT} exists in the current directory")
        return 1
    except sqlite3.Error as e:
        print(f"\n❌ Database error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    sys.exit(main())
