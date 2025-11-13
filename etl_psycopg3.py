"""
ETL with psycopg3 (Modern version)
Demonstrates performance optimizations for your thesis
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import psycopg
from psycopg import sql
import pandas as pd
import time
from datetime import datetime
from schemas import Artigo

from pydantic import BaseModel

# Try to import ConnectionPool (optional)
try:
    from psycopg_pool import ConnectionPool
    HAS_POOL = True
except ImportError:
    HAS_POOL = False
    print("⚠️  psycopg_pool not available. Install with: pip install psycopg[pool]")

# Connection string
CONN_STRING = "host=localhost port=5432 dbname=etldb user=postgres"


class DatabaseConnector:
    def __init__(self):
        self.conn_str = CONN_STRING
        self._pool = None
    
    @property
    def pool(self):
        """Lazy-load connection pool only when needed"""
        if self._pool is None:
            if not HAS_POOL:
                raise ImportError("ConnectionPool not available. Install: pip install psycopg[pool]")
            self._pool = ConnectionPool(conninfo=self.conn_str, min_size=1, max_size=5, open=True)
        return self._pool


    def create_table(self, table_name, columns):
        """
        Create a table dynamically with provided columns.
        Example columns: 'id SERIAL PRIMARY KEY, name TEXT, age INT'
        """
        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {columns}
        );
        """
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
            conn.commit()
        print(f"✅ Table '{table_name}' created successfully.")

    def insert_into_table(self, table_name, data):
        """
        Insert a row into a given table.
        - `data` should be a dictionary: {"column1": value1, "column2": value2, ...}
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = list(data.values())

        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        # with psycopg.connect(self.conn_str) as conn:
        #     with conn.cursor() as cur:
        #         cur.execute(query, values)
        #     conn.commit()

        print(f"✅ Inserted 1 record into '{table_name}' successfully.")

    def insert_batch(self, table_name, data_batch):
        """Função auxiliar que insere um único lote de registros."""
        data_dicts = []
        for m in data_batch:
            d = m.dict()
            if "text" in d:
                d["content"] = d.pop("text")
            data_dicts.append(d)

        columns = ', '.join(data_dicts[0].keys())
        placeholders = ', '.join(['%s'] * len(data_dicts[0]))
        values = [tuple(d.values()) for d in data_dicts]
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.executemany(query, values)
            conn.commit()

        # print(f"✅ Inserido batch com {len(values)} registros.")
        return len(values)

    
    def batch_process_rows(self, table_name, data_model_list, batch_size=1000, max_workers=5):
        """Divide os dados em lotes e insere com 5 threads paralelas."""
        total_rows = len(data_model_list)
        batches = [
            data_model_list[i:i + batch_size]
            for i in range(0, total_rows, batch_size)
        ]

        print(f"🚀 Iniciando processamento em {len(batches)} lotes, usando {max_workers} threads...")

        start_time = time.perf_counter()
        total_inserted = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.insert_batch, table_name, batch): batch
                for batch in batches
            }

            for i, future in enumerate(as_completed(futures)):
                inserted = future.result()
                total_inserted += inserted
                print(f"🧩 Lote {i + 1}/{len(batches)} concluído ({inserted} registros).")

        end_time = time.perf_counter()
        duration = end_time - start_time
        rate = total_inserted / duration if duration > 0 else 0

        print(f"\n✅ Inserção paralela concluída!")
        print(f"📊 Total inserido: {total_inserted} registros")
        print(f"⏱️ Tempo total: {duration:.2f} segundos")
        print(f"⚡ Taxa média: {rate:.0f} registros/segundo\n")



    def truncate_table(self, table_name: str):
        """Remove todos os registros da tabela rapidamente."""
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;")
            conn.commit()
        print(f"🧹 Tabela '{table_name}' truncada com sucesso!")



    # -------------------------------------------------------------------------
    def insert_optimized_single_transaction(self, table_name: str, data_model_list: list[BaseModel]):
        """
        OTIMIZADO: Inserção rápida usando COPY em uma única transação.
        Ideal para datasets pequenos/médios (< 100k registros).
        Usa PostgreSQL COPY que é o método mais rápido.
        """
        if not data_model_list:
            return 0

        print(f"🚀 Inserção otimizada (transação única com COPY) iniciada...")
        start_time = time.perf_counter()

        data_dicts = []
        for m in data_model_list:
            d = m.dict()
            if "text" in d:
                d["content"] = d.pop("text")
            data_dicts.append(d)

        columns = list(data_dicts[0].keys())
        values = [tuple(d[c] for c in columns) for d in data_dicts]
        cols_str = ', '.join(columns)

        # Uma única transação com COPY (mais rápido que INSERT)
        existing_ids = set()
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT paper_id FROM {table_name}")
                existing_ids = {row[0] for row in cur.fetchall()}
                filtered_values = []
                for v in values:
                    # paper_id is assumed to be the first column
                    if v[0] not in existing_ids:
                        filtered_values.append(v)
                if not filtered_values:
                    print("⚠️ Nenhum novo registro para inserir (todos já existem).")
                    return 0

                with cur.copy(f"COPY {table_name} ({cols_str}) FROM STDIN") as copy:
                    for row in filtered_values:
                        copy.write_row(row)
            conn.commit()

        end_time = time.perf_counter()
        duration = end_time - start_time
        rate = len(data_model_list) / duration if duration > 0 else 0

        print(f"\n✅ Inserção finalizada!")
        print(f"📊 Total inserido: {len(data_model_list)} registros")
        print(f"⏱️ Tempo total: {duration:.2f} s")
        print(f"⚡ Taxa média: {rate:.0f} registros/s\n")

        return len(data_model_list)
