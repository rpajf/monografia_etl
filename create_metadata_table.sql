-- Tabela de Metadata para o dataset COVID-19 (CORD-19)
-- Contém metadados dos artigos científicos

DROP TABLE IF EXISTS metadata_staging CASCADE;

CREATE TABLE metadata_staging (
    -- Identificadores principais
    cord_uid VARCHAR(100) PRIMARY KEY,          -- ID único do CORD-19
    sha VARCHAR(100),                            -- SHA hash do artigo
    s2_id VARCHAR(50),                          -- Semantic Scholar ID
    
    -- Identificadores externos
    pmcid VARCHAR(50),                          -- PubMed Central ID
    pubmed_id VARCHAR(50),                      -- PubMed ID
    doi VARCHAR(100),                           -- Digital Object Identifier
    mag_id VARCHAR(50),                         -- Microsoft Academic Graph ID
    who_covidence_id VARCHAR(50),               -- WHO Covidence ID
    arxiv_id VARCHAR(50),                       -- ArXiv ID
    
    -- Metadados descritivos
    title TEXT,                                 -- Título do artigo
    abstract TEXT,                              -- Resumo/Abstract
    authors TEXT,                               -- Autores (separados por ;)
    journal TEXT,                               -- Nome do journal/revista
    publish_time VARCHAR(50),                   -- Data de publicação
    
    -- Informações adicionais
    source_x TEXT,                              -- Fonte dos dados
    license TEXT,                               -- Licença do artigo
    url TEXT,                                   -- URL do artigo
    
    -- Arquivos JSON associados
    pdf_json_files TEXT,                        -- Caminhos dos JSONs de PDF
    pmc_json_files TEXT,                        -- Caminhos dos JSONs do PMC
    
    -- Controle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhorar performance de queries
CREATE INDEX idx_metadata_sha ON metadata_staging(sha);
CREATE INDEX idx_metadata_doi ON metadata_staging(doi);
CREATE INDEX idx_metadata_pubmed_id ON metadata_staging(pubmed_id);
CREATE INDEX idx_metadata_journal ON metadata_staging(journal);
CREATE INDEX idx_metadata_publish_time ON metadata_staging(publish_time);

-- Índice full-text para busca no título
CREATE INDEX idx_metadata_title_fulltext ON metadata_staging 
    USING gin(to_tsvector('english', title));

-- Índice full-text para busca no abstract
CREATE INDEX idx_metadata_abstract_fulltext ON metadata_staging 
    USING gin(to_tsvector('english', abstract));

-- Comentários na tabela e colunas
COMMENT ON TABLE metadata_staging IS 'Staging area para metadados do dataset COVID-19 CORD-19';
COMMENT ON COLUMN metadata_staging.cord_uid IS 'Identificador único do CORD-19';
COMMENT ON COLUMN metadata_staging.sha IS 'SHA hash do documento original';
COMMENT ON COLUMN metadata_staging.title IS 'Título do artigo científico';
COMMENT ON COLUMN metadata_staging.abstract IS 'Resumo do artigo';
COMMENT ON COLUMN metadata_staging.authors IS 'Lista de autores separados por ponto-e-vírgula';
COMMENT ON COLUMN metadata_staging.journal IS 'Nome da revista/journal';
COMMENT ON COLUMN metadata_staging.publish_time IS 'Data de publicação';

