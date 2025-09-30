DROP TABLE IF EXISTS pmayg_fund_fact CASCADE;
DROP TABLE IF EXISTS pmayg_indicator CASCADE;
DROP TABLE IF EXISTS pmayg_report CASCADE;
DROP TABLE IF EXISTS pmayg_panchayat CASCADE;
DROP TABLE IF EXISTS pmayg_block CASCADE;
DROP TABLE IF EXISTS pmayg_district CASCADE;
DROP TABLE IF EXISTS pmayg_state CASCADE;

-- ==============================================================
-- PMAY-G Fund Allocation & Utilization Database Schema
-- ==============================================================

-- =====================
-- Geography hierarchy
-- =====================

-- Each state in India (e.g., 'Maharashtra', 'Bihar').
CREATE TABLE pmayg_state (
    state_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL -- Example: 'Maharashtra'
);

-- Districts belong to states (e.g., 'Pune' in 'Maharashtra').
CREATE TABLE pmayg_district (
    district_id SERIAL PRIMARY KEY,
    state_id INT NOT NULL REFERENCES pmayg_state(state_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    UNIQUE(state_id, name)
);

-- Blocks belong to districts (e.g., 'Khed' in 'Pune' district).
CREATE TABLE pmayg_block (
    block_id SERIAL PRIMARY KEY,
    district_id INT NOT NULL REFERENCES pmayg_district(district_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    UNIQUE(district_id, name)
);

-- Panchayats belong to blocks (e.g., 'Ambegaon' in 'Khed' block).
CREATE TABLE pmayg_panchayat (
    panchayat_id SERIAL PRIMARY KEY,
    block_id INT NOT NULL REFERENCES pmayg_block(block_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    UNIQUE(block_id, name)
);

-- =====================
-- Report metadata
-- =====================

-- Each PMAY-G financial progress report is a snapshot in time.
CREATE TABLE pmayg_report (
    report_id SERIAL PRIMARY KEY,
    report_type TEXT NOT NULL,       -- e.g. 'allocation', 'utilization'
    report_date TIMESTAMP NOT NULL,  -- the "As On" timestamp from Excel
    source_file TEXT                 -- filename or source path
);

-- =====================
-- Indicators (categories)
-- =====================

-- PMAY-G measures include:
--   Beneficiary categories: 'SC', 'ST', 'Minority', 'Others', 'Total'
--   Fund flows: 'Opening Balance', 'Central Allocation', 'Utilization of Funds', etc.
CREATE TABLE pmayg_indicator (
    indicator_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,  -- Example: 'SC', 'Utilization of Funds'
    type TEXT NOT NULL CHECK (type IN ('beneficiary', 'fund_flow'))
);

-- =====================
-- Facts (numerical values)
-- =====================

-- Stores the actual PMAY-G numbers:
-- Each row ties together:
--   - A report (which snapshot in time)
--   - A geography (state, district, block, or panchayat)
--   - An indicator (beneficiary group or fund flow measure)
--   - A numeric amount
CREATE TABLE pmayg_fund_fact (
    fact_id SERIAL PRIMARY KEY,
    report_id INT NOT NULL REFERENCES pmayg_report(report_id) ON DELETE CASCADE,

    -- One of these levels will be filled, others NULL depending on granularity
    state_id INT REFERENCES pmayg_state(state_id),
    district_id INT REFERENCES pmayg_district(district_id),
    block_id INT REFERENCES pmayg_block(block_id),
    panchayat_id INT REFERENCES pmayg_panchayat(panchayat_id),

    indicator_id INT NOT NULL REFERENCES pmayg_indicator(indicator_id),
    amount NUMERIC,   -- Example: 478164.35 (Maharashtra Utilization of Funds)
    note TEXT         -- Optional annotation, e.g. "From PMAY-G Report Sep 2025"
);