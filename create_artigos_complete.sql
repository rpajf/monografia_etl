-- ============================================================================
-- Script SQL para criar a tabela artigos_complete
-- Resultante da junção entre artigos_stg e metadata_staging
-- JOIN ON: metadata_staging.cord_uid = artigos_stg.paper_id
-- ============================================================================

-- Remover tabela existente se houver
DROP TABLE IF EXISTS artigos_complete CASCADE;

-- Criar tabela artigos_complete
CREATE TABLE artigos_complete (
    -- ID único (usando paper_id como PK principal)
    paper_id VARCHAR(100) PRIMARY KEY,
    cord_uid VARCHAR(100) UNIQUE,
    
    -- Colunas de artigos_stg
    file_name TEXT,
    title_from_article TEXT,  -- Título do artigo (pode diferir do metadata)
    body_text TEXT,
    created_at_article TIMESTAMP,
    
    -- Colunas de metadata_staging
    sha VARCHAR(100),
    source_x TEXT,
    title TEXT,  -- Título do metadata
    doi VARCHAR(100),
    pmcid VARCHAR(50),
    pubmed_id VARCHAR(50),
    license TEXT,
    abstract TEXT,
    publish_time VARCHAR(50),
    authors TEXT,
    journal TEXT,
    mag_id VARCHAR(50),
    who_covidence_id VARCHAR(50),
    arxiv_id VARCHAR(50),
    pdf_json_files TEXT,
    pmc_json_files TEXT,
    url TEXT,
    s2_id VARCHAR(50),
    created_at_metadata TIMESTAMP,
    
    -- Campo de controle
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================================================

-- Índice na chave de junção
CREATE INDEX idx_artigos_complete_cord_uid ON artigos_complete(cord_uid);

-- Índice no SHA (pode ser usado para joins alternativos)
CREATE INDEX idx_artigos_complete_sha ON artigos_complete(sha);

-- Índices para filtros comuns
CREATE INDEX idx_artigos_complete_journal ON artigos_complete(journal);
CREATE INDEX idx_artigos_complete_publish_time ON artigos_complete(publish_time);
CREATE INDEX idx_artigos_complete_authors ON artigos_complete(authors);

-- Índices GIN para full-text search
CREATE INDEX idx_artigos_complete_body_text_gin ON artigos_complete 
    USING gin(to_tsvector('english', body_text));

CREATE INDEX idx_artigos_complete_abstract_gin ON artigos_complete 
    USING gin(to_tsvector('english', abstract));

CREATE INDEX idx_artigos_complete_title_gin ON artigos_complete 
    USING gin(to_tsvector('english', title));

-- ============================================================================
-- POPULAR TABELA COM JOIN
-- ============================================================================

-- Inserir dados fazendo JOIN entre as tabelas staging
INSERT INTO artigos_complete (
    paper_id,
    cord_uid,
    -- Colunas de artigos_stg
    file_name,
    title_from_article,
    body_text,
    created_at_article,
    -- Colunas de metadata_staging
    sha,
    source_x,
    title,
    doi,
    pmcid,
    pubmed_id,
    license,
    abstract,
    publish_time,
    authors,
    journal,
    mag_id,
    who_covidence_id,
    arxiv_id,
    pdf_json_files,
    pmc_json_files,
    url,
    s2_id,
    created_at_metadata
)
SELECT 
    a.paper_id,
    m.cord_uid,
    -- Colunas de artigos_stg
    a.file_name,
    a.title AS title_from_article,
    a.body_text,
    a.created_at AS created_at_article,
    -- Colunas de metadata_staging
    m.sha,
    m.source_x,
    m.title,
    m.doi,
    m.pmcid,
    m.pubmed_id,
    m.license,
    m.abstract,
    m.publish_time,
    m.authors,
    m.journal,
    m.mag_id,
    m.who_covidence_id,
    m.arxiv_id,
    m.pdf_json_files,
    m.pmc_json_files,
    m.url,
    m.s2_id,
    m.created_at AS created_at_metadata
FROM artigos_stg a
INNER JOIN metadata_staging m ON a.paper_id = m.cord_uid
ON CONFLICT (paper_id) DO NOTHING;

-- ============================================================================
-- VERIFICAÇÕES E ESTATÍSTICAS
-- ============================================================================

-- Verificar total de registros inseridos
SELECT 
    COUNT(*) as total_registros,
    COUNT(*) FILTER (WHERE body_text IS NOT NULL) as com_body_text,
    COUNT(*) FILTER (WHERE abstract IS NOT NULL) as com_abstract,
    COUNT(*) FILTER (WHERE authors IS NOT NULL) as com_authors,
    COUNT(*) FILTER (WHERE journal IS NOT NULL) as com_journal,
    COUNT(*) FILTER (WHERE doi IS NOT NULL) as com_doi
FROM artigos_complete;

-- Verificar taxa de match
SELECT 
    (SELECT COUNT(*) FROM artigos_complete) as registros_completos,
    (SELECT COUNT(*) FROM artigos_stg) as total_artigos,
    (SELECT COUNT(*) FROM metadata_staging) as total_metadata,
    ROUND(
        (SELECT COUNT(*)::numeric FROM artigos_complete) / 
        NULLIF((SELECT COUNT(*)::numeric FROM artigos_stg), 0) * 100, 
        2
    ) as taxa_match_percentual;

