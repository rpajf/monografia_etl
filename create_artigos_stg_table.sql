-- Tabela artigos_stg para armazenar artigos do dataset COVID-19
-- Suporta inserção com ON CONFLICT DO NOTHING e tratamento de UniqueViolation

DROP TABLE IF EXISTS artigos_stg CASCADE;

CREATE TABLE artigos_stg (
    paper_id VARCHAR(100) PRIMARY KEY,
    file_name TEXT,
    title TEXT,
    body_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para melhorar performance de queries por paper_id
CREATE INDEX IF NOT EXISTS idx_artigos_stg_paper_id ON artigos_stg(paper_id);

-- Comentários para documentação
COMMENT ON TABLE artigos_stg IS 'Tabela de staging para artigos científicos do dataset COVID-19';
COMMENT ON COLUMN artigos_stg.paper_id IS 'ID único do artigo (SHA hash) - PRIMARY KEY';
COMMENT ON COLUMN artigos_stg.file_name IS 'Nome do arquivo JSON de origem';
COMMENT ON COLUMN artigos_stg.title IS 'Título do artigo';
COMMENT ON COLUMN artigos_stg.body_text IS 'Conteúdo completo do artigo (body_text)';
COMMENT ON COLUMN artigos_stg.created_at IS 'Timestamp de criação do registro';


