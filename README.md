# Data Transformation - Automated SCD Type 2

> A metadata-driven Python engine for implementing Slowly Changing Dimension (SCD) Type 2 data transformation with SQLite

[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![SQLite](https://img.shields.io/badge/database-SQLite-lightgrey)](https://www.sqlite.org/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [What is Slowly Changing Dimension (SCD) Type 2?](#what-is-slowly-changing-dimension-scd-type-2)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Modules Documentation](#modules-documentation)
- [Examples](#examples)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This project provides an automated, metadata-driven solution for implementing **SCD Type 2** (Slowly Changing Dimension Type 2) data transformations. It efficiently tracks historical changes in your data warehouse by maintaining complete version history with temporal tracking.

**Key Highlights:**
- 🔄 Automatic change detection using MD5 hashing
- 📊 Complete historical tracking with temporal columns
- ⚙️ Metadata-driven configuration (JSON-based)
- 🐍 Pure Python implementation with no external dependencies
- 💾 SQLite database support (easily adaptable to other databases)
- 📈 Detailed logging and processing metrics

---

## What is Slowly Changing Dimension (SCD) Type 2?

**Slowly Changing Dimension (SCD) Type 2** is a data warehousing technique used to track historical changes by creating a new record for each change while preserving the complete history.

### How It Works

When a record changes, instead of updating the existing record, SCD Type 2:
1. **Expires the old version** by setting `is_current = 0` and updating `row_end_date`
2. **Inserts a new version** with `is_current = 1` and a new `row_start_date`
3. **Maintains full history** allowing you to query data at any point in time

### Example Scenario

**Original Record:**
```
ID: 101, Product: "Laptop Pro", Price: $999.99
row_start_date: 2024-01-01, row_end_date: 9999-12-31, is_current: 1
```

**After Price Change to $1299.99:**
```
Record 1 (Historical):
ID: 101, Product: "Laptop Pro", Price: $999.99
row_start_date: 2024-01-01, row_end_date: 2024-06-15, is_current: 0

Record 2 (Current):
ID: 101, Product: "Laptop Pro", Price: $1299.99
row_start_date: 2024-06-15, row_end_date: 9999-12-31, is_current: 1
```

This allows you to:
- ✅ Query the current state of data
- ✅ Query historical state at any point in time
- ✅ Track when changes occurred
- ✅ Analyze trends and changes over time
- ✅ Perform time-travel queries

---

## Features

### Core Features

- **🔍 Automatic Change Detection**
  - MD5 hashing for efficient comparison
  - Detects new, changed, and unchanged records
  - Configurable monitoring of specific columns

- **📚 Complete Historical Tracking**
  - Maintains all versions of records
  - Temporal validity tracking (start/end dates)
  - Current record flagging

- **⚙️ Metadata-Driven Configuration**
  - JSON-based configuration
  - Define primary keys and monitored columns
  - No code changes needed for different tables

- **📊 Detailed Reporting**
  - Processing statistics (new, changed, unchanged)
  - Execution progress tracking
  - Comprehensive logging

- **🚀 High Performance**
  - Efficient hash-based comparisons
  - Optimized database queries
  - Indexed CDC tables for fast lookups

- **🔒 Data Integrity**
  - Atomic transactions
  - Primary key constraints
  - Referential integrity support

### Advanced Features

- **Multi-Table Support** - Process multiple tables with different configurations
- **Deleted Record Detection** - Track records that no longer exist in source
- **Audit Trail** - Complete change history with timestamps
- **Point-in-Time Queries** - Query data as it existed at any date/time
- **Trend Analysis** - Analyze how data changed over time
- **Custom Hash Functions** - Support for custom change detection logic
- **Logging Integration** - File and console logging support
- **Performance Metrics** - Execution time tracking

---

## Quick Start

Get up and running in 5 minutes:

### 1. Clone the Repository

```bash
git clone https://github.com/NirajV/Project_Gen_AI-Data_Tranformation.git
cd Data_Tranformation
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install development dependencies (includes all tools for testing and development)
python -m pip install -r requirements-dev.txt

# OR install production dependencies only (none required - uses stdlib only)
python -m pip install -r requirements.txt
```

### 4. Create Required Directories

```bash
mkdir data
mkdir logs
```

### 5. Create Configuration File

Create `config.json`:

```json
{
    "primary_key": "id",
    "changing_attributes": ["product_name", "price", "quantity", "status"]
}
```

### 6. Set Up Database

Create your SQLite database and tables:

```bash
sqlite3 ./data/test_database.db < setup_database.sql
```

### 7. Run the Pipeline

```bash
python scd_pipeline.py
```

That's it! Your SCD Type 2 pipeline is now running.

---

## Installation

### Prerequisites

- **Python 3.6 or higher**
- **SQLite** (included with Python)

### Standard Libraries Used

All required libraries are part of Python's standard library:
- `sqlite3` - Database operations
- `json` - Configuration file parsing
- `hashlib` - MD5 hash generation
- `datetime` - Timestamp management

### Setup Steps

1. **Clone or Download the Repository**

```bash
git clone https://github.com/NirajV/Project_Gen_AI-Data_Tranformation.git
cd Data_Tranformation
```

2. **Verify Python Installation**

```bash
python --version
# Should show Python 3.6 or higher
```

3. **Create Virtual Environment (Recommended)**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate
```

**Why use a virtual environment?**
- ✅ Isolates project dependencies from system Python
- ✅ Prevents version conflicts with other projects
- ✅ Makes project portable and reproducible
- ✅ Easy to manage and clean up

4. **Install Dependencies**

```bash
# Install development dependencies (includes testing, linting, documentation tools)
python -m pip install -r requirements-dev.txt

# OR install production dependencies only (none required - uses Python stdlib only)
python -m pip install -r requirements.txt
```

**Note:** The core SCD Type 2 implementation uses only Python standard library modules, so no external packages are required for basic functionality. The `requirements-dev.txt` file contains optional development tools for testing, code quality, and documentation.

5. **Create Project Structure**
5. **Create Project Structure**

```bash
mkdir data
mkdir logs
```

6. **Verify Installation**

```bash
python -c "import sqlite3, json, hashlib, datetime; print('All dependencies available!')"
```

### Directory Structure After Installation

```
Data_Tranformation/
├── data/
│   └── test_database.db
├── logs/
│   └── scd_pipeline.log
├── config.json
├── scd_pipeline.py
├── setup_database.sql
├── Automated_SCD_Type2.md
└── README.md
```

---

## Configuration

### Configuration File (config.json)

The `config.json` file controls which columns are monitored for changes.

#### Basic Configuration

```json
{
    "primary_key": "id",
    "changing_attributes": ["product_name", "price", "quantity", "status"]
}
```

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `primary_key` | string | Yes | The unique identifier column name |
| `changing_attributes` | array | Yes | List of columns to monitor for changes |

#### Multi-Table Configuration

For processing multiple tables:

```json
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
            "changing_attributes": ["name", "email", "phone", "address"]
        }
    ]
}
```

### Environment Configuration

Set environment variables in your script or `.env` file:

```python
# Database configuration
DB_NAME = "./data/test_database.db"
SOURCE_TABLE = "sales_records"
TARGET_TABLE = "sales_records_cdc"

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = "./logs/scd_pipeline.log"
```

### Database Configuration

#### Source Table Setup

Your source table should contain the current state of records:

```sql
CREATE TABLE sales_records (
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
```

#### CDC Table Setup

The CDC table must include all source columns PLUS SCD audit columns:

```sql
CREATE TABLE sales_records_cdc (
    -- All columns from source table
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
    
    -- SCD Type 2 audit columns
    row_hash TEXT NOT NULL,
    row_start_date TEXT NOT NULL,
    row_end_date TEXT NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 1,
    
    PRIMARY KEY (id, row_start_date)
);
```

---

## Usage

### Basic Usage

#### 1. Run the Pipeline

```bash
python scd_pipeline.py
```

#### 2. Expected Output

```
============================================================
Starting SCD Type 2 Pipeline
============================================================

[1/6] Loading configuration from config.json
   Primary Key: id
   Monitoring Columns: product_name, price, quantity, status

[2/6] Connecting to database: ./data/test_database.db

[3/6] Extracting data from sales_records
   Found 150 records in source table

[4/6] Processing records and detecting changes
   ✓ NEW: id=1
   ✓ NEW: id=2
   ✓ CHANGED: id=3
   ...

[5/6] Committing changes to database

[6/6] Closing database connection

============================================================
SCD Type 2 Pipeline Complete
============================================================
📊 Processing Summary:
   • New Records:       120
   • Changed Records:   25
   • Unchanged Records: 5
   • Total Processed:   150
============================================================
```

### Advanced Usage

#### Schedule Automated Runs

**Windows Task Scheduler:**

```bash
schtasks /create /tn "SCD Pipeline" /tr "python C:\path\to\scd_pipeline.py" /sc daily /st 02:00
```

**Linux/Mac Cron:**

```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/project && python scd_pipeline.py >> logs/pipeline.log 2>&1
```

#### Programmatic Usage

```python
from scd_pipeline import run_scd_pipeline

# Run with default config
run_scd_pipeline("config.json")

# Run with custom config
run_scd_pipeline("config_custom.json")
```

#### Query Historical Data

**Get Current Records:**

```sql
SELECT * FROM sales_records_cdc WHERE is_current = 1;
```

**Get Full History:**

```sql
SELECT * FROM sales_records_cdc ORDER BY id, row_start_date DESC;
```

**Point-in-Time Query:**

```sql
SELECT * FROM sales_records_cdc
WHERE '2024-06-01 12:00:00' BETWEEN row_start_date AND row_end_date;
```

**Track Changes for a Specific Record:**

```sql
SELECT 
    id,
    product_name,
    price,
    row_start_date,
    row_end_date,
    is_current
FROM sales_records_cdc
WHERE id = 101
ORDER BY row_start_date;
```

---

## Project Structure

```
Data_Tranformation/
│
├── data/                           # Database files
│   └── test_database.db           # SQLite database
│
├── logs/                           # Log files
│   └── scd_pipeline.log           # Pipeline execution logs
│
├── config.json                     # Configuration file
│
├── scd_pipeline.py                 # Main pipeline script
│
├── setup_database.sql              # Database initialization script
│
├── Automated_SCD_Type2.md         # Detailed implementation guide
│
├── README.md                       # This file
│
├── requirements.txt                # Python dependencies (empty - using stdlib)
│
└── .gitignore                      # Git ignore file
```

### File Descriptions

| File | Purpose |
|------|---------|
| `scd_pipeline.py` | Main Python script implementing SCD Type 2 logic |
| `config.json` | Metadata configuration for table monitoring |
| `setup_database.sql` | SQL script to create tables and indexes |
| `Automated_SCD_Type2.md` | Comprehensive step-by-step guide |
| `README.md` | Project documentation (this file) |

---

## Modules Documentation

### Core Functions

#### `generate_hash(row, attributes)`

Generates an MD5 hash for change detection.

**Parameters:**
- `row` (dict): Row data from database
- `attributes` (list): List of column names to include in hash

**Returns:**
- `str`: MD5 hash of concatenated attribute values

**Example:**
```python
row = {"id": 1, "product_name": "Laptop", "price": 999.99}
attrs = ["product_name", "price"]
hash_value = generate_hash(row, attrs)
# Returns: "5d41402abc4b2a76b9719d911017c592"
```

#### `run_scd_pipeline(config_path)`

Main pipeline execution function.

**Parameters:**
- `config_path` (str): Path to configuration JSON file

**Process:**
1. Load metadata configuration
2. Connect to database
3. Extract source data
4. Generate hashes for change detection
5. Compare with CDC table
6. Insert new records or update changed records
7. Maintain historical versions
8. Report processing statistics

**Returns:**
- None (prints summary to console)

**Example:**
```python
run_scd_pipeline("config.json")
```

### Helper Functions

#### `connect_database(db_path)`

Establishes database connection with proper configuration.

```python
def connect_database(db_path):
    """Connect to SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
```

#### `get_current_timestamp()`

Returns formatted current timestamp.

```python
def get_current_timestamp():
    """Get current timestamp in standard format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

#### `get_expiry_timestamp()`

Returns the standard expiry timestamp for current records.

```python
def get_expiry_timestamp():
    """Get standard expiry timestamp."""
    return "9999-12-31 23:59:59"
```

---

## Examples

### Example 1: Basic Implementation

**Step 1: Create Configuration**

```json
{
    "primary_key": "id",
    "changing_attributes": ["product_name", "price"]
}
```

**Step 2: Create Source Data**

```sql
INSERT INTO sales_records (id, product_name, price) VALUES
(1, 'Laptop Pro', 1299.99),
(2, 'Mouse Wireless', 29.99);
```

**Step 3: Run Pipeline**

```bash
python scd_pipeline.py
```

**Step 4: Verify Results**

```sql
SELECT * FROM sales_records_cdc;
```

### Example 2: Detecting Changes

**Update Source Data:**

```sql
UPDATE sales_records SET price = 1399.99 WHERE id = 1;
```

**Run Pipeline Again:**

```bash
python scd_pipeline.py
```

**View History:**

```sql
SELECT id, product_name, price, row_start_date, row_end_date, is_current
FROM sales_records_cdc
WHERE id = 1
ORDER BY row_start_date;
```

**Result:**
```
id | product_name | price    | row_start_date      | row_end_date        | is_current
---|--------------|----------|---------------------|---------------------|------------
1  | Laptop Pro   | 1299.99  | 2024-01-15 10:00:00 | 2024-01-15 14:30:00 | 0
1  | Laptop Pro   | 1399.99  | 2024-01-15 14:30:00 | 9999-12-31 23:59:59 | 1
```

### Example 3: Point-in-Time Analysis

**Query data as it existed on January 15, 2024 at noon:**

```sql
SELECT id, product_name, price
FROM sales_records_cdc
WHERE '2024-01-15 12:00:00' BETWEEN row_start_date AND row_end_date;
```

### Example 4: Trend Analysis

**Analyze price changes over time:**

```sql
SELECT 
    id,
    product_name,
    price as old_price,
    LEAD(price) OVER (PARTITION BY id ORDER BY row_start_date) as new_price,
    row_start_date as change_date,
    ROUND((LEAD(price) OVER (PARTITION BY id ORDER BY row_start_date) - price) / price * 100, 2) as price_change_pct
FROM sales_records_cdc
WHERE id = 1;
```

### Example 5: Current vs Historical Count

**Compare current records with total historical records:**

```sql
SELECT 
    COUNT(*) as total_versions,
    SUM(CASE WHEN is_current = 1 THEN 1 ELSE 0 END) as current_records,
    COUNT(*) - SUM(CASE WHEN is_current = 1 THEN 1 ELSE 0 END) as historical_records
FROM sales_records_cdc;
```

---

## Security

### Database Security

1. **Access Control**
   - Use appropriate file permissions for database files
   - Implement database-level access controls
   - Store databases in secure locations

2. **Connection Security**
   - Use parameterized queries (already implemented)
   - Avoid SQL injection vulnerabilities
   - Validate input data

3. **Data Protection**
   - Implement encryption for sensitive data
   - Regular backups of database files
   - Secure backup storage

### Code Security

1. **Input Validation**
   ```python
   # Validate configuration
   if not conf.get('primary_key'):
       raise ValueError("Primary key must be defined in config")
   ```

2. **SQL Injection Prevention**
   ```python
   # Use parameterized queries
   cursor.execute("SELECT * FROM table WHERE id = ?", (record_id,))
   ```

3. **Error Handling**
   ```python
   try:
       run_scd_pipeline("config.json")
   except Exception as e:
       logging.error(f"Pipeline failed: {e}")
   ```

### Best Practices

- ✅ Never commit database files to version control
- ✅ Use `.gitignore` to exclude sensitive files
- ✅ Implement proper logging without exposing sensitive data
- ✅ Regularly update Python and dependencies
- ✅ Implement monitoring and alerting
- ✅ Use environment variables for sensitive configuration

### Recommended .gitignore

```
# Database files
*.db
*.sqlite
*.sqlite3

# Log files
*.log
logs/

# Environment files
.env
.env.local

# Python cache
__pycache__/
*.pyc
*.pyo
```

---

## Troubleshooting

### Common Issues

#### Issue 1: "Table already exists" Error

**Error:**
```
sqlite3.OperationalError: table sales_records_cdc already exists
```

**Solution:**
```sql
DROP TABLE IF EXISTS sales_records_cdc;
-- Then run CREATE TABLE again
```

#### Issue 2: "No such column" Error

**Error:**
```
sqlite3.OperationalError: table sales_records_cdc has no column named row_hash
```

**Solution:**
- Verify CDC table includes ALL source columns PLUS audit columns
- Check column names match exactly (case-sensitive)
- Recreate the CDC table with correct schema

#### Issue 3: All Records Detected as "Changed"

**Cause:** Data type inconsistencies or column ordering mismatch

**Solution:**
```python
# Add debugging to print hash values
print(f"Source Hash: {src_hash}")
print(f"Target Hash: {tgt_record['row_hash'] if tgt_record else 'None'}")
```

**Checklist:**
- [ ] Column names in `changing_attributes` match exactly
- [ ] Data types are consistent (NULL vs empty string)
- [ ] Date/time formats are standardized
- [ ] No trailing whitespace in text fields

#### Issue 4: Database Locked

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Solutions:**
1. Close SQLite browser/viewer tools
2. Ensure no other scripts are accessing the database
3. Check for stale database connections
4. Restart the application

#### Issue 5: Config File Not Found

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'config.json'
```

**Solutions:**
```bash
# Verify file exists
ls -la config.json

# Check current directory
pwd

# Use absolute path if needed
python scd_pipeline.py --config /absolute/path/to/config.json
```

### Debugging Tips

1. **Enable Verbose Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Print Hash Values**
   ```python
   print(f"Row: {src_row}")
   print(f"Hash: {src_hash}")
   ```

3. **Check Database Contents**
   ```bash
   sqlite3 ./data/test_database.db
   .tables
   .schema sales_records_cdc
   SELECT COUNT(*) FROM sales_records_cdc;
   ```

4. **Validate Configuration**
   ```python
   import json
   with open('config.json') as f:
       config = json.load(f)
       print(json.dumps(config, indent=2))
   ```

### Getting Help

If you encounter issues not covered here:

1. Check the [Automated_SCD_Type2.md](Automated_SCD_Type2.md) guide
2. Search existing issues on GitHub
3. Create a new issue with:
   - Error message
   - Steps to reproduce
   - Python version
   - Operating system
   - Configuration file content

---

## Contributing

We welcome contributions! Here's how you can help:

### Ways to Contribute

- 🐛 **Report Bugs** - Submit detailed bug reports
- 💡 **Suggest Features** - Propose new functionality
- 📝 **Improve Documentation** - Enhance guides and examples
- 🔧 **Submit Pull Requests** - Contribute code improvements
- ⭐ **Star the Project** - Show your support

### Contribution Guidelines

#### 1. Fork the Repository

```bash
git clone https://github.com/yourusername/Data_Tranformation.git
cd Data_Tranformation
```

#### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

#### 3. Make Your Changes

- Follow Python PEP 8 style guidelines
- Add docstrings to all functions
- Include unit tests for new features
- Update documentation

#### 4. Test Your Changes

```bash
# Run the pipeline
python scd_pipeline.py

# Verify functionality
python -m pytest tests/
```

#### 5. Commit Your Changes

```bash
git add .
git commit -m "Add feature: description of your changes"
```

#### 6. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

#### 7. Submit a Pull Request

- Provide a clear description of changes
- Reference any related issues
- Include screenshots if applicable

### Code Style

Follow these conventions:

```python
# Good: Clear variable names
def generate_hash(row, attributes):
    """Generate MD5 hash for change detection."""
    combined_string = "-".join([str(row[attr]) for attr in attributes])
    return hashlib.md5(combined_string.encode()).hexdigest()

# Good: Comprehensive docstrings
def run_scd_pipeline(config_path):
    """
    Execute the SCD Type 2 pipeline.
    
    Args:
        config_path (str): Path to configuration file
        
    Returns:
        None
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid
    """
    pass
```

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/Data_Tranformation.git
cd Data_Tranformation

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/
```

### Pull Request Checklist

Before submitting a pull request:

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with main

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed
- ⚠️ License and copyright notice required
- ❌ No liability
- ❌ No warranty

---

## Acknowledgments

- Inspired by data warehousing best practices
- Built with Python standard library
- SQLite for lightweight database operations
- Community feedback and contributions

---

## Contact

- **Author:** Data Engineering Team
- **Project Link:** [https://github.com/yourusername/Data_Tranformation](https://github.com/yourusername/Data_Tranformation)
- **Documentation:** [Automated_SCD_Type2.md](Automated_SCD_Type2.md)

---

## Changelog

### Version 2.0.0 (2026-01-19)
- ✨ Complete rewrite with comprehensive documentation
- 🔧 Enhanced configuration system
- 📊 Improved reporting and logging
- 🐛 Bug fixes and performance improvements
- 📝 Detailed step-by-step guide added

### Version 1.0.0 (Initial Release)
- 🎉 Initial release
- ⚙️ Basic SCD Type 2 implementation
- 📄 JSON configuration support
- 💾 SQLite database integration

---

<div align="center">

**[⬆ Back to Top](#data-transformation---automated-scd-type-2)**

Made with ❤️ by the Data Engineering Team

</div>
