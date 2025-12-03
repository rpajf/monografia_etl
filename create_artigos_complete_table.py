"""
Script para criar a tabela artigos_complete resultante da junção entre
artigos_staging e metadata_staging.

Baseado no diagrama: JOIN ON cord_uid = paper_id
"""

import os
import psycopg
from etl_psycopg3 import get_connection_string


def create_artigos_complete_table():
    """
    Cria a tabela artigos_complete com todas as colunas de ambas as tabelas staging.
    A junção é feita com: metadata_staging.cord_uid = artigos_staging.paper_id
    """
    conn_str = get_connection_string()
    
    print("=" * 70)
    print("📊 CRIANDO TABELA artigos_complete")
    print("=" * 70)
    print()
    
    # SQL para criar a tabela
    create_table_sql = """
    DROP TABLE IF EXISTS artigos_complete CASCADE;
    
    CREATE TABLE artigos_complete (
        -- ID único (usando paper_id como PK principal)
        paper_id VARCHAR(100) PRIMARY KEY,
        cord_uid VARCHAR(100) UNIQUE,
        
        -- Colunas de artigos_staging
        file_name TEXT,
        title_from_article TEXT,  -- Renomeado para evitar conflito
        body_text TEXT,
        created_at_article TIMESTAMP,  -- Renomeado para evitar conflito
        
        -- Colunas de metadata_staging
        sha VARCHAR(100),
        source_x TEXT,
        title TEXT,  -- Título do metadata (pode ser diferente do artigo)
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
        created_at_metadata TIMESTAMP,  -- Renomeado para evitar conflito
        
        -- Campo de controle
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Índices para performance
    CREATE INDEX idx_artigos_complete_cord_uid ON artigos_complete(cord_uid);
    CREATE INDEX idx_artigos_complete_sha ON artigos_complete(sha);
    CREATE INDEX idx_artigos_complete_journal ON artigos_complete(journal);
    CREATE INDEX idx_artigos_complete_publish_time ON artigos_complete(publish_time);
    CREATE INDEX idx_artigos_complete_authors ON artigos_complete(authors);
    
    -- Índice GIN para full-text search no body_text
    CREATE INDEX idx_artigos_complete_body_text_gin ON artigos_complete 
        USING gin(to_tsvector('english', body_text));
    
    -- Índice GIN para full-text search no abstract
    CREATE INDEX idx_artigos_complete_abstract_gin ON artigos_complete 
        USING gin(to_tsvector('english', abstract));
    """
    
    # SQL para popular a tabela com JOIN
    populate_table_sql = """
    INSERT INTO artigos_complete (
        paper_id,
        cord_uid,
        -- Colunas de artigos_staging
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
        -- Colunas de artigos_staging
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
    """
    
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                # Criar tabela
                print("🔨 Criando tabela artigos_complete...")
                cur.execute(create_table_sql)
                conn.commit()
                print("✅ Tabela criada com sucesso!")
                print()
                
                # Verificar se as tabelas staging existem
                print("🔍 Verificando tabelas staging...")
                cur.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name IN ('artigos_stg', 'metadata_staging')
                """)
                staging_tables_count = cur.fetchone()[0]
                
                if staging_tables_count < 2:
                    print("⚠️  ATENÇÃO: Uma ou ambas as tabelas staging não existem!")
                    print("   Certifique-se de que artigos_stg e metadata_staging existem.")
                    print()
                    print("   Para criar artigos_stg:")
                    print("   CREATE TABLE artigos_stg (")
                    print("       paper_id VARCHAR(100) PRIMARY KEY,")
                    print("       file_name TEXT,")
                    print("       title TEXT,")
                    print("       body_text TEXT,")
                    print("       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                    print("   );")
                    print()
                    print("   Para criar metadata_staging, veja main_etl.py")
                    return
                
                # Verificar quantos registros existem em cada tabela
                cur.execute("SELECT COUNT(*) FROM artigos_stg")
                artigos_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM metadata_staging")
                metadata_count = cur.fetchone()[0]
                
                print(f"📊 Registros em artigos_stg: {artigos_count:,}")
                print(f"📊 Registros em metadata_staging: {metadata_count:,}")
                print()
                
                # Popular tabela
                if artigos_count > 0 and metadata_count > 0:
                    print("🔄 Populando tabela artigos_complete com JOIN...")
                    print("   (Isso pode levar alguns minutos dependendo do tamanho dos dados)")
                    cur.execute(populate_table_sql)
                    inserted_count = cur.rowcount
                    conn.commit()
                    print(f"✅ {inserted_count:,} registros inseridos em artigos_complete!")
                else:
                    print("⚠️  Tabelas staging estão vazias. Execute o ETL primeiro.")
                    print("   A tabela artigos_complete foi criada, mas está vazia.")
                
                # Estatísticas finais
                print()
                print("📈 Estatísticas da tabela artigos_complete:")
                cur.execute("SELECT COUNT(*) FROM artigos_complete")
                total_complete = cur.fetchone()[0]
                print(f"   Total de registros: {total_complete:,}")
                
                if total_complete > 0:
                    cur.execute("""
                        SELECT 
                            COUNT(*) FILTER (WHERE body_text IS NOT NULL) as com_body_text,
                            COUNT(*) FILTER (WHERE abstract IS NOT NULL) as com_abstract,
                            COUNT(*) FILTER (WHERE authors IS NOT NULL) as com_authors,
                            COUNT(*) FILTER (WHERE journal IS NOT NULL) as com_journal
                        FROM artigos_complete
                    """)
                    stats = cur.fetchone()
                    print(f"   Com body_text: {stats[0]:,}")
                    print(f"   Com abstract: {stats[1]:,}")
                    print(f"   Com authors: {stats[2]:,}")
                    print(f"   Com journal: {stats[3]:,}")
                
    except psycopg.Error as e:
        print(f"❌ Erro ao criar tabela: {e}")
        raise
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        raise


def show_join_statistics():
    """
    Mostra estatísticas sobre o JOIN entre as tabelas staging.
    """
    conn_str = get_connection_string()
    
    print()
    print("=" * 70)
    print("📊 ESTATÍSTICAS DO JOIN")
    print("=" * 70)
    print()
    
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                # Total de registros em cada tabela
                cur.execute("SELECT COUNT(*) FROM artigos_stg")
                artigos_total = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM metadata_staging")
                metadata_total = cur.fetchone()[0]
                
                # Registros que fazem match
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM artigos_stg a
                    INNER JOIN metadata_staging m ON a.paper_id = m.cord_uid
                """)
                matched = cur.fetchone()[0]
                
                # Registros sem match em artigos_stg
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM artigos_stg a
                    LEFT JOIN metadata_staging m ON a.paper_id = m.cord_uid
                    WHERE m.cord_uid IS NULL
                """)
                artigos_no_match = cur.fetchone()[0]
                
                # Registros sem match em metadata_staging
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM metadata_staging m
                    LEFT JOIN artigos_stg a ON m.cord_uid = a.paper_id
                    WHERE a.paper_id IS NULL
                """)
                metadata_no_match = cur.fetchone()[0]
                
                print(f"📊 Total em artigos_stg: {artigos_total:,}")
                print(f"📊 Total em metadata_staging: {metadata_total:,}")
                print(f"✅ Registros que fazem match (cord_uid = paper_id): {matched:,}")
                print(f"⚠️  Artigos sem metadata: {artigos_no_match:,}")
                print(f"⚠️  Metadata sem artigo: {metadata_no_match:,}")
                
                if artigos_total > 0:
                    match_percentage = (matched / artigos_total) * 100
                    print(f"📈 Taxa de match: {match_percentage:.2f}%")
                
    except psycopg.Error as e:
        print(f"❌ Erro ao calcular estatísticas: {e}")


if __name__ == "__main__":
    # Mostrar estatísticas antes
    show_join_statistics()
    
    print()
    response = input("Deseja criar a tabela artigos_complete? (s/n): ")
    
    if response.lower() in ['s', 'sim', 'y', 'yes']:
        create_artigos_complete_table()
    else:
        print("Operação cancelada.")

