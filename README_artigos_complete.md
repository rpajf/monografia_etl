# 📊 Tabela artigos_complete

## Descrição

A tabela `artigos_complete` é o resultado da junção entre as tabelas staging:
- `artigos_stg` (conteúdo textual dos artigos)
- `metadata_staging` (metadados dos artigos)

## Relacionamento

A junção é feita através da condição:
```sql
JOIN ON metadata_staging.cord_uid = artigos_stg.paper_id
```

## Estrutura da Tabela

### Colunas Principais

| Coluna | Tipo | Origem | Descrição |
|--------|------|--------|-----------|
| `paper_id` | VARCHAR(100) | artigos_stg | PK - ID único do artigo |
| `cord_uid` | VARCHAR(100) | metadata_staging | ID CORD-19 (único) |
| `file_name` | TEXT | artigos_stg | Nome do arquivo JSON original |
| `title_from_article` | TEXT | artigos_stg | Título extraído do artigo |
| `body_text` | TEXT | artigos_stg | Texto completo do artigo |
| `title` | TEXT | metadata_staging | Título do metadata |
| `abstract` | TEXT | metadata_staging | Resumo do artigo |
| `authors` | TEXT | metadata_staging | Lista de autores |
| `journal` | TEXT | metadata_staging | Nome da revista |
| `publish_time` | VARCHAR(50) | metadata_staging | Data de publicação |
| `doi` | VARCHAR(100) | metadata_staging | DOI do artigo |
| `sha` | VARCHAR(100) | metadata_staging | SHA hash |

### Índices Criados

1. **Índices B-tree** (para filtros e joins):
   - `idx_artigos_complete_cord_uid`
   - `idx_artigos_complete_sha`
   - `idx_artigos_complete_journal`
   - `idx_artigos_complete_publish_time`
   - `idx_artigos_complete_authors`

2. **Índices GIN** (para full-text search):
   - `idx_artigos_complete_body_text_gin`
   - `idx_artigos_complete_abstract_gin`
   - `idx_artigos_complete_title_gin`

## Como Criar a Tabela

### Opção 1: Script Python (Recomendado)

```bash
python create_artigos_complete_table.py
```

O script:
- Verifica se as tabelas staging existem
- Mostra estatísticas do JOIN
- Cria a tabela e índices
- Popula com os dados

### Opção 2: SQL Direto

```bash
psql -U postgres -d etldb -f create_artigos_complete.sql
```

Ou execute o SQL diretamente no PostgreSQL.

## Queries Úteis

### Buscar artigos por journal

```sql
SELECT 
    journal,
    COUNT(*) as total_artigos,
    AVG(LENGTH(body_text)) as tamanho_medio_texto
FROM artigos_complete
WHERE journal IS NOT NULL
GROUP BY journal
ORDER BY total_artigos DESC
LIMIT 10;
```

### Full-text search no conteúdo

```sql
SELECT 
    paper_id,
    title,
    authors,
    journal,
    ts_rank(to_tsvector('english', body_text), query) as rank
FROM artigos_complete, 
     to_tsquery('english', 'COVID & vaccine') query
WHERE to_tsvector('english', body_text) @@ query
ORDER BY rank DESC
LIMIT 20;
```

### Artigos por período

```sql
SELECT 
    DATE_TRUNC('month', publish_time::date) as mes,
    COUNT(*) as artigos_publicados
FROM artigos_complete
WHERE publish_time IS NOT NULL
  AND publish_time::date >= '2020-01-01'
GROUP BY mes
ORDER BY mes;
```

### Estatísticas de completude

```sql
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE body_text IS NOT NULL) as com_texto,
    COUNT(*) FILTER (WHERE abstract IS NOT NULL) as com_abstract,
    COUNT(*) FILTER (WHERE authors IS NOT NULL) as com_autores,
    COUNT(*) FILTER (WHERE journal IS NOT NULL) as com_journal,
    COUNT(*) FILTER (WHERE doi IS NOT NULL) as com_doi
FROM artigos_complete;
```

## Notas Importantes

1. **Tamanho da Tabela**: A tabela pode ser muito grande (~70GB) devido ao campo `body_text`
2. **Performance**: Os índices GIN podem ser lentos para criar, mas são essenciais para buscas
3. **Manutenção**: Considere executar `VACUUM ANALYZE` periodicamente
4. **Atualização**: Se novas linhas forem inseridas nas tabelas staging, execute novamente o INSERT

## Troubleshooting

### Erro: "relation artigos_stg does not exist"
- Verifique se a tabela `artigos_stg` existe
- O nome pode ser `artigos_staging` em vez de `artigos_stg`
- Ajuste o script conforme necessário

### Erro: "relation metadata_staging does not exist"
- Execute o ETL para criar `metadata_staging` primeiro
- Veja `main_etl.py` para exemplo de criação

### Taxa de match baixa
- Verifique se `paper_id` em `artigos_stg` corresponde a `cord_uid` em `metadata_staging`
- Pode haver diferenças nos identificadores entre os datasets

