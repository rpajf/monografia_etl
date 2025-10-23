-- Initialization script for COVID-19 ETL Database
-- This script creates the initial schema for the ETL project

-- Create schema for organizing tables
CREATE SCHEMA IF NOT EXISTS covid_data;

-- Set default schema
SET search_path TO covid_data, public;

-- Create papers table (for JSON research papers)
CREATE TABLE IF NOT EXISTS papers (
    paper_id VARCHAR(100) PRIMARY KEY,
    title TEXT,
    abstract TEXT,
    publish_time DATE,
    source VARCHAR(100),
    url TEXT,
    full_text JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create authors table
CREATE TABLE IF NOT EXISTS authors (
    author_id SERIAL PRIMARY KEY,
    author_name VARCHAR(500) NOT NULL,
    email VARCHAR(255),
    affiliation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create paper_authors junction table (many-to-many)
CREATE TABLE IF NOT EXISTS paper_authors (
    paper_id VARCHAR(100) REFERENCES papers(paper_id) ON DELETE CASCADE,
    author_id INTEGER REFERENCES authors(author_id) ON DELETE CASCADE,
    author_order INTEGER,
    PRIMARY KEY (paper_id, author_id)
);

-- Create metadata table
CREATE TABLE IF NOT EXISTS metadata (
    cord_uid VARCHAR(100) PRIMARY KEY,
    sha VARCHAR(100),
    source_x VARCHAR(100),
    title TEXT,
    doi VARCHAR(255),
    pmcid VARCHAR(50),
    pubmed_id VARCHAR(50),
    license VARCHAR(100),
    abstract TEXT,
    publish_time DATE,
    authors TEXT,
    journal VARCHAR(500),
    mag_id VARCHAR(50),
    who_covidence_id VARCHAR(50),
    arxiv_id VARCHAR(50),
    pdf_json_files TEXT,
    pmc_json_files TEXT,
    url TEXT,
    s2_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create embeddings table (for the large 14.8 GB file)
CREATE TABLE IF NOT EXISTS embeddings (
    cord_uid VARCHAR(100) PRIMARY KEY,
    embedding_vector TEXT,  -- or use vector type if using pgvector extension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create ETL metrics table for tracking performance
CREATE TABLE IF NOT EXISTS etl_metrics (
    metric_id SERIAL PRIMARY KEY,
    process_name VARCHAR(100),
    strategy_type VARCHAR(50),  -- 'baseline' or 'optimized'
    records_processed INTEGER,
    duration_seconds NUMERIC(10, 2),
    memory_used_mb NUMERIC(10, 2),
    cpu_percent NUMERIC(5, 2),
    errors_count INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT
);

-- Create indexes for better query performance
-- Note: For ETL optimization demo, we'll test creating these BEFORE vs AFTER bulk load
CREATE INDEX idx_papers_publish_time ON papers(publish_time);
CREATE INDEX idx_papers_source ON papers(source);
CREATE INDEX idx_metadata_publish_time ON metadata(publish_time);
CREATE INDEX idx_metadata_doi ON metadata(doi);
CREATE INDEX idx_metadata_pmcid ON metadata(pmcid);
CREATE INDEX idx_authors_name ON authors(author_name);

-- Create GIN index for JSONB full_text search
CREATE INDEX idx_papers_full_text_gin ON papers USING GIN(full_text);

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA covid_data TO etl_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA covid_data TO etl_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA covid_data TO etl_user;

-- Display summary
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'COVID-19 ETL Database Initialized';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Database: covid_etl';
    RAISE NOTICE 'Schema: covid_data';
    RAISE NOTICE 'Tables created: papers, authors, paper_authors, metadata, embeddings, etl_metrics';
    RAISE NOTICE '========================================';
END $$;


