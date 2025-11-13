# 🗄️ Estrutura do Banco de Dados - Pipeline ETL COVID-19

## 📊 Visão Geral

O pipeline ETL utiliza **3 tabelas principais** seguindo o padrão de staging areas separadas:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ artigos_staging │     │ metadata_staging │     │ artigos_final   │
│  (Conteúdo)     │────►│   (Atributos)    │────►│ (Consolidado)   │
│   716k rows     │     │    716k rows     │     │   716k rows     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
    Staging 1               Staging 2              Tabela Final
```

---

## 📋 Tabela 1: `artigos_staging` (Conteúdo Textual)

### **Propósito:** 
Armazena o conteúdo textual completo dos artigos científicos.

### **Estrutura:**
```sql
CREATE TABLE artigos_staging (
    paper_id VARCHAR(100) PRIMARY KEY,
    title TEXT,
    full_text TEXT,              -- Texto completo do artigo
    sections JSONB,              -- Estrutura de seções (opcional)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Colunas:**

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| `paper_id` | VARCHAR(100) | ID único do artigo (SHA hash) | "abc123xyz..." |
| `title` | TEXT | Título do artigo | "COVID-19 in Russia..." |
| `full_text` | TEXT | Todo o body_text concatenado | "According to current..." |
| `sections` | JSONB | Estrutura de seções preservada | `[{"section": "Intro", "text": "..."}]` |
| `created_at` | TIMESTAMP | Data de inserção | "2025-10-30 12:00:00" |

### **Índices:**
```sql
CREATE INDEX idx_artigos_paper_id ON artigos_staging(paper_id);
CREATE INDEX idx_artigos_fulltext ON artigos_staging 
    USING gin(to_tsvector('english', full_text));
```

### **Tamanho Estimado:**
- **Linhas:** ~716,000
- **Tamanho médio por linha:** ~100 KB
- **Tamanho total:** ~70 GB

---

## 📋 Tabela 2: `metadata_staging` (Metadados)

### **Propósito:** 
Armazena metadados estruturados dos artigos (autores, journal, datas, etc.).

### **Estrutura:**
```sql
CREATE TABLE metadata_staging (
    -- Identificadores principais
    cord_uid VARCHAR(100) PRIMARY KEY,
    sha VARCHAR(100),
    s2_id VARCHAR(50),
    
    -- Identificadores externos
    pmcid VARCHAR(50),
    pubmed_id VARCHAR(50),
    doi VARCHAR(100),
    mag_id VARCHAR(50),
    who_covidence_id VARCHAR(50),
    arxiv_id VARCHAR(50),
    
    -- Metadados descritivos
    title TEXT,
    abstract TEXT,
    authors TEXT,
    journal TEXT,
    publish_time VARCHAR(50),
    
    -- Informações adicionais
    source_x TEXT,
    license TEXT,
    url TEXT,
    
    -- Arquivos JSON associados
    pdf_json_files TEXT,
    pmc_json_files TEXT,
    
    -- Controle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Colunas Principais:**

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| `cord_uid` | VARCHAR(100) | ID único CORD-19 (PK) | "ug7v899j" |
| `sha` | VARCHAR(100) | SHA hash (FK para artigos) | "abc123..." |
| `title` | TEXT | Título do artigo | "COVID-19 pandemic..." |
| `abstract` | TEXT | Resumo do artigo | "Background: This study..." |
| `authors` | TEXT | Lista de autores | "Smith, John; Doe, Jane" |
| `journal` | TEXT | Nome da revista | "Nature Medicine" |
| `publish_time` | VARCHAR(50) | Data de publicação | "2020-05-15" |
| `doi` | VARCHAR(100) | DOI | "10.1038/s41591..." |
| `pubmed_id` | VARCHAR(50) | PubMed ID | "32355581" |
| `license` | TEXT | Licença | "cc-by" |
| `url` | TEXT | URL do artigo | "https://..." |

### **Índices:**
```sql
CREATE INDEX idx_metadata_sha ON metadata_staging(sha);
CREATE INDEX idx_metadata_journal ON metadata_staging(journal);
CREATE INDEX idx_metadata_publish_time ON metadata_staging(publish_time);
CREATE INDEX idx_metadata_title_fulltext ON metadata_staging 
    USING gin(to_tsvector('english', title));
```

### **Tamanho Estimado:**
- **Linhas:** ~716,000
- **Tamanho médio por linha:** ~2 KB
- **Tamanho total:** ~1.5 GB

---

## 📋 Tabela 3: `artigos_final` (Consolidada)

### **Propósito:** 
Tabela final consolidada após JOIN e transformações (NLP, limpeza, etc.).

### **Estrutura:**
```sql
CREATE TABLE artigos_final (
    id SERIAL PRIMARY KEY,
    paper_id VARCHAR(100) UNIQUE,
    
    -- Metadados (do metadata_staging)
    cord_uid VARCHAR(100),
    title TEXT,
    authors TEXT[],
    journal TEXT,
    publish_date DATE,
    doi VARCHAR(100),
    abstract TEXT,
    
    -- Conteúdo (do artigos_staging)
    full_text TEXT,
    sections JSONB,
    
    -- Campos calculados (Transform phase)
    word_count INT,
    char_count INT,
    sentiment_score FLOAT,
    keywords TEXT[],
    main_topics TEXT[],
    
    -- Controle
    processed_at TIMESTAMP DEFAULT NOW(),
    quality_score FLOAT,
    
    FOREIGN KEY (paper_id) REFERENCES artigos_staging(paper_id)
);
```

### **Campos Derivados:**

| Campo | Cálculo | Descrição |
|-------|---------|-----------|
| `word_count` | `LENGTH(full_text) - LENGTH(REPLACE(full_text, ' ', '')) + 1` | Contagem de palavras |
| `sentiment_score` | NLP Processing | Score de sentimento (-1 a 1) |
| `keywords` | TF-IDF / NLP | Top keywords extraídos |
| `main_topics` | Topic Modeling | Tópicos principais |
| `quality_score` | Validação | Score de qualidade dos dados |

---

## 🔄 Relacionamentos Entre Tabelas

### **Chave de Ligação: `paper_id` / `sha`**

```sql
-- JOIN básico entre staging areas
SELECT 
    a.paper_id,
    a.full_text,
    m.title,
    m.authors,
    m.journal
FROM artigos_staging a
INNER JOIN metadata_staging m ON a.paper_id = m.sha;
```

### **Diagrama de Relacionamento:**

```
metadata_staging          artigos_staging
┌─────────────┐          ┌──────────────┐
│ cord_uid PK │          │ paper_id PK  │
│ sha         │─────────►│              │
│ title       │          │ full_text    │
│ authors     │          │ sections     │
└─────────────┘          └──────────────┘
       │                        │
       └────────┬───────────────┘
                ↓
        artigos_final
        ┌──────────────┐
        │ id PK        │
        │ paper_id UK  │
        │ (joined)     │
        └──────────────┘
```

---

## 📊 Queries Comuns

### **Query 1: Artigos por Journal**
```sql
SELECT 
    journal,
    COUNT(*) as total_articles,
    AVG(LENGTH(abstract)) as avg_abstract_length
FROM metadata_staging
WHERE journal IS NOT NULL
GROUP BY journal
ORDER BY total_articles DESC
LIMIT 10;
```

### **Query 2: Full-text Search**
```sql
SELECT 
    a.paper_id,
    m.title,
    m.authors,
    m.journal
FROM artigos_staging a
JOIN metadata_staging m ON a.paper_id = m.sha
WHERE to_tsvector('english', a.full_text) @@ 
      to_tsquery('english', 'machine & learning & COVID')
ORDER BY ts_rank(to_tsvector('english', a.full_text), 
                 to_tsquery('english', 'machine & learning & COVID')) DESC
LIMIT 20;
```

### **Query 3: Artigos por Período**
```sql
SELECT 
    DATE_TRUNC('month', publish_time::date) as month,
    COUNT(*) as articles_published
FROM metadata_staging
WHERE publish_time IS NOT NULL
  AND publish_time::date >= '2020-01-01'
GROUP BY month
ORDER BY month;
```

---

## 🎯 Estratégia de Indexação

### **Performance vs Storage:**

| Tipo de Índice | Uso de Disco | Velocidade SELECT | Velocidade INSERT |
|----------------|--------------|-------------------|-------------------|
| B-tree (padrão) | +15-20% | Muito rápido | Lento (-10%) |
| GIN (full-text) | +30-50% | Extremamente rápido | Muito lento (-30%) |
| Sem índice | 0% | Muito lento | Rápido |

**Recomendação:** 
- Criar índices **APÓS** inserir todos os dados
- Usar `CREATE INDEX CONCURRENTLY` para não bloquear tabela

---

## 📈 Estatísticas do Dataset

### **Dados do CORD-19:**

| Métrica | Valor |
|---------|-------|
| Total de JSONs | 716,956 |
| Artigos únicos | ~716,000 |
| Tamanho total staging | ~71.5 GB |
| Período coberto | 2019-2024 |
| Journals únicos | ~5,000+ |

---

## 🔧 Manutenção

### **Vacuum e Analyze:**
```sql
-- Após inserção massiva
VACUUM ANALYZE artigos_staging;
VACUUM ANALYZE metadata_staging;

-- Estatísticas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 📝 Para Sua Monografia

### **Conceitos Demonstrados:**

1. ✅ **Staging Areas Separadas** - Normalização de dados
2. ✅ **Star Schema** - Modelagem dimensional
3. ✅ **Indexação Estratégica** - Performance tuning
4. ✅ **JOIN SQL** - Consolidação de dados
5. ✅ **Full-text Search** - Busca avançada
6. ✅ **Data Quality** - Validação e controle

---

**Última atualização:** Outubro 2025  
**Status:** ✅ Estrutura completa definida  
**Pronto para:** Implementação do pipeline ETL

