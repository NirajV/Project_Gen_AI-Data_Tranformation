-- ============================================================================
-- Automated SCD Type 2 Database Setup Script
-- ============================================================================
-- This script creates the necessary tables for SCD Type 2 implementation
-- 
-- Tables Created:
--   1. sales_records      - Source table with current data
--   2. sales_records_cdc  - CDC table with historical tracking
--
-- Author: Data Engineering Team
-- Version: 2.0
-- Date: January 19, 2026
-- ============================================================================

-- ============================================================================
-- STEP 1: Create Source Table (sales_records)
-- ============================================================================

-- Drop existing source table if it exists (for clean setup)
DROP TABLE IF EXISTS sales_records;

-- Create source table
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

-- ============================================================================
-- STEP 2: Insert Sample Data into Source Table
-- ============================================================================

INSERT INTO sales_records VALUES 
(1, '2024-01-15', 'Laptop Pro', 'Electronics', 1299.99, 1, 1299.99, 1001, 'North', 'Active'),
(2, '2024-01-16', 'Mouse Wireless', 'Accessories', 29.99, 2, 59.98, 1002, 'South', 'Active'),
(3, '2024-01-17', 'Keyboard Mechanical', 'Accessories', 89.99, 1, 89.99, 1003, 'East', 'Active'),
(4, '2024-01-18', 'Monitor 27-inch', 'Electronics', 399.99, 1, 399.99, 1004, 'West', 'Active'),
(5, '2024-01-19', 'USB Hub', 'Accessories', 24.99, 3, 74.97, 1005, 'North', 'Active');

-- ============================================================================
-- STEP 3: Create CDC Table with SCD Type 2 Columns (Option 1: Composite PK)
-- ============================================================================

-- Drop existing CDC table if it exists
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

-- ============================================================================
-- STEP 4: Create Indexes for Performance Optimization
-- ============================================================================

-- Index on is_current flag for quick filtering of current records
CREATE INDEX idx_cdc_is_current ON sales_records_cdc(is_current);

-- Composite index on id and is_current for efficient lookups
CREATE INDEX idx_cdc_id_current ON sales_records_cdc(id, is_current);

-- Index on row_hash for change detection optimization
CREATE INDEX idx_cdc_row_hash ON sales_records_cdc(row_hash);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify source table
SELECT '=== Source Table ===' AS info;
SELECT COUNT(*) AS source_record_count FROM sales_records;
SELECT * FROM sales_records LIMIT 5;

-- Verify CDC table structure
SELECT '=== CDC Table Structure ===' AS info;
PRAGMA table_info(sales_records_cdc);

-- ============================================================================
-- ALTERNATIVE: CDC Table with Surrogate Key (Uncomment if preferred)
-- ============================================================================

/*
-- Drop existing CDC table if it exists
DROP TABLE IF EXISTS sales_records_cdc;

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

-- Create indexes for performance
CREATE INDEX idx_cdc_is_current ON sales_records_cdc(is_current);
CREATE INDEX idx_cdc_id_current ON sales_records_cdc(id, is_current);
CREATE INDEX idx_cdc_row_hash ON sales_records_cdc(row_hash);
CREATE INDEX idx_cdc_dates ON sales_records_cdc(row_start_date, row_end_date);
*/

-- ============================================================================
-- SETUP COMPLETE
-- ============================================================================

SELECT '=== Database Setup Complete ===' AS info;
SELECT 'Ready to run SCD Type 2 pipeline!' AS status;
