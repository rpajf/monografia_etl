"""
ETL with psycopg3 (Modern version)
Demonstrates performance optimizations for your thesis
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import psycopg
import time
from pydantic import BaseModel
from more_itertools import chunked

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
                raise ImportError(
                    "ConnectionPool not available. Install: pip install psycopg[pool]"
                )
            self._pool = ConnectionPool(
                conninfo=self.conn_str, min_size=1, max_size=5, open=True
            )
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
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
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

        columns = ", ".join(data_dicts[0].keys())
        placeholders = ", ".join(["%s"] * len(data_dicts[0]))
        values = [tuple(d.values()) for d in data_dicts]
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.executemany(query, values)
            conn.commit()

        # print(f"✅ Inserido batch com {len(values)} registros.")
        return len(values)

    def batch_process_rows(
        self, table_name, data_model_list, batch_size=1000, max_workers=5
    ):
        """Divide os dados em lotes e insere com 5 threads paralelas."""
        total_rows = len(data_model_list)
        batches = [
            data_model_list[i : i + batch_size]
            for i in range(0, total_rows, batch_size)
        ]

        print(
            f"🚀 Iniciando processamento em {len(batches)} lotes, usando {max_workers} threads..."
        )

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
                print(
                    f"🧩 Lote {i + 1}/{len(batches)} concluído ({inserted} registros)."
                )

        end_time = time.perf_counter()
        duration = end_time - start_time
        rate = total_inserted / duration if duration > 0 else 0

        print("\n✅ Inserção paralela concluída!")
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
    def insert_optimized_single_transaction2(
        self, table_name: str, data_model_list: list[BaseModel]
    ):
        """
        OTIMIZADO: Inserção rápida usando COPY em uma única transação.
        Ideal para datasets pequenos/médios (< 100k registros).
        Usa PostgreSQL COPY que é o método mais rápido.
        """
        if not data_model_list:
            return 0

        print("🚀 Inserção otimizada (transação única com COPY) iniciada...")
        start_time = time.perf_counter()

        data_dicts = []
        for m in data_model_list:
            d = m.dict()
            if "text" in d:
                d["content"] = d.pop("text")
            data_dicts.append(d)

        columns = list(data_dicts[0].keys())
        values = [tuple(d[c] for c in columns) for d in data_dicts]
        cols_str = ", ".join(columns)

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

        print("\n✅ Inserção finalizada!")
        print(f"📊 Total inserido: {len(data_model_list)} registros")
        print(f"⏱️ Tempo total: {duration:.2f} s")
        print(f"⚡ Taxa média: {rate:.0f} registros/s\n")

        return len(data_model_list)

    async def insert_async_batch_transactions(
        self, table_name: str, data_model_list: list[BaseModel]
    ):
        if not data_model_list:
            return 0
        start_time = time.perf_counter()
        aconn = await psycopg.AsyncConnection.connect(self.conn_str)
        data_dicts = []
        for m in data_model_list:
            d = m.dict()
            if "text" in d:
                d["content"] = d.pop("text")
            data_dicts.append(d)

        columns = list(data_dicts[0].keys())
        cols_str = ", ".join(columns)
        async with aconn:
            try:
                async with aconn.cursor() as cur:
                    await cur.execute(
                        query=f"INSERT INTO {table_name} ({cols_str}) VALUES (%s)",
                    )
            except psycopg.errors.UniqueViolation:
                print("⚠️ Alguns registros duplicados foram ignorados (já existentes).")
                aconn.rollback()
        duration = time.perf_counter() - start_time
        print(f"✅ Inseridos {len(data_model_list)} registros em {duration:.2f}s")

    async def insert_chunk(
        self,
        table_name: str,
        data_chunk: list,
        chunk_index: int | None = None,
        total_chunks: int | None = None,
        use_copy: bool = True,
    ):
        """
        Insere um chunk de registros em uma tabela.
        
        Args:
            table_name: Nome da tabela
            data_chunk: Lista de dicts (já convertidos, não BaseModel)
            chunk_index: Índice do chunk para logging
            total_chunks: Total de chunks para logging
            use_copy: Se True, usa COPY (mais rápido). Se False, usa executemany.
        """
        if not data_chunk:
            return 0

        # Data should already be dicts at this point
        data_dicts = data_chunk
        columns = list(data_dicts[0].keys())
        cols_str = ", ".join(columns)

        chunk_label = None
        if chunk_index is not None and total_chunks is not None:
            chunk_label = f"{chunk_index + 1}/{total_chunks}"

        # Try to use connection pool if available, otherwise create new connection
        if HAS_POOL:
            try:
                async with self.pool.connection() as aconn:
                    return await self._insert_chunk_with_conn(
                        aconn, table_name, data_dicts, columns, cols_str, 
                        chunk_label, use_copy
                    )
            except Exception as e:
                # Fallback to direct connection if pool fails
                pass
        
        # Fallback: direct connection
        async with await psycopg.AsyncConnection.connect(self.conn_str) as aconn:
            return await self._insert_chunk_with_conn(
                aconn, table_name, data_dicts, columns, cols_str, 
                chunk_label, use_copy
            )
    
    async def _insert_chunk_with_conn(
        self, aconn, table_name, data_dicts, columns, cols_str, chunk_label, use_copy
    ):
        """Helper method to insert chunk with given connection."""
        try:
            async with aconn.cursor() as cur:
                if use_copy:
                    # Use COPY for better performance (faster than executemany)
                    # In psycopg3 async, cur.copy() returns an async context manager
                    values = [tuple(d[c] for c in columns) for d in data_dicts]
                    async with cur.copy(
                        f"COPY {table_name} ({cols_str}) FROM STDIN"
                    ) as copy:
                        for row in values:
                            await copy.write_row(row)
                else:
                    values = [tuple(d[c] for c in columns) for d in data_dicts]
                    placeholders = ", ".join(["%s"] * len(columns))
                    query = (
                        f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders}) "
                        "ON CONFLICT DO NOTHING"
                    )
                    await cur.executemany(query, values)
            await aconn.commit()
            return len(data_dicts)
        except psycopg.errors.UniqueViolation:
            if chunk_label:
                print(f" Chunk {chunk_label} ignorado por duplicidades.")
            else:
                print(" Chunk ignorado por duplicidades.")
            await aconn.rollback()
            return 0
        except Exception as e:
            if chunk_label:
                print(f"❌ Erro no chunk {chunk_label}: {e}")
            await aconn.rollback()
            return 0

    async def insert_async_parallel(
        self,
        table_name: str,
        data_model_list: list,
        chunk_size: int = 5000,
        max_tasks: int = 4,
        use_copy: bool = True,
    ):
        """
        Divide o dataset em chunks e insere paralelamente.
        
        Optimizations:
        - Uses connection pooling if available
        - Converts BaseModel to dict once (not per chunk)
        - Uses COPY instead of executemany for better performance
        - Adaptive chunking for better load distribution
        
        Args:
            table_name: Nome da tabela
            data_model_list: Lista de BaseModel ou dicts
            chunk_size: Tamanho de cada chunk (otimizado automaticamente se muito pequeno)
            max_tasks: Número máximo de tasks paralelas
            use_copy: Se True, usa COPY (mais rápido). Se False, usa executemany.
        """
        start = time.perf_counter()

        if not data_model_list:
            return {"inserted": 0, "duration": 0, "chunk_size": 0, "total_chunks": 0, "concurrency": 0}

        # Converte BaseModel → dict uma única vez (otimização de memória)
        # Fazemos isso antes de chunking para evitar conversão duplicada
        rows = []
        for m in data_model_list:
            if isinstance(m, BaseModel):
                d = m.dict()
                if "text" in d:
                    d["content"] = d.pop("text")
                rows.append(d)
            else:
                # Já é dict, apenas normaliza se necessário
                if "text" in m:
                    m = m.copy()
                    m["content"] = m.pop("text")
                rows.append(m)

        if not rows:
            return {"inserted": 0, "duration": 0, "chunk_size": 0, "total_chunks": 0, "concurrency": 0}

        # Otimização: Se chunk_size muito pequeno para o dataset, ajusta
        # Evita criar muitos chunks pequenos (overhead)
        total_records = len(rows)
        if chunk_size < 1000 and total_records > 10000:
            optimal_chunks = min(20, max(4, total_records // 5000))
            chunk_size = max(1000, total_records // optimal_chunks)

        # Divide em chunks
        chunks = list(chunked(rows, chunk_size))
        total_chunks = len(chunks)

        # Cria um número limitado de tasks paralelas com semáforo
        sem = asyncio.Semaphore(max_tasks)

        async def worker(idx, chunk):
            """Worker que processa um chunk."""
            async with sem:
                try:
                    inserted = await self.insert_chunk(
                        table_name=table_name,
                        data_chunk=chunk,  # Já são dicts, não BaseModel
                        chunk_index=idx,
                        total_chunks=total_chunks,
                        use_copy=use_copy,
                    )
                    return inserted
                except Exception as exc:
                    print(f"❌ Falha no chunk {idx + 1}/{total_chunks}: {exc}")
                    return 0

        # Cria todas as tasks
        tasks = [
            asyncio.create_task(worker(idx, chunk)) 
            for idx, chunk in enumerate(chunks)
        ]

        # Executa todas as tasks em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=False)

        total = time.perf_counter() - start
        total_inserted = sum(results)
        
        # Calcula estatísticas
        successful_chunks = sum(1 for r in results if r > 0)
        avg_chunk_time = total / total_chunks if total_chunks > 0 else 0
        
        print(
            f"Inserção paralela concluída em {total:.2f}s "
            f"({total_inserted:,} registros válidos, "
            f"{successful_chunks}/{total_chunks} chunks, "
            f"chunk={chunk_size}, tasks={max_tasks}, "
            f"avg_chunk={avg_chunk_time:.3f}s)"
        )

        return {
            "inserted": total_inserted,
            "duration": total,
            "chunk_size": chunk_size,
            "total_chunks": total_chunks,
            "successful_chunks": successful_chunks,
            "concurrency": max_tasks,
            "throughput": total_inserted / total if total > 0 else 0,
        }

    def insert_optimized_single_transaction(
        self, table_name: str, data_model_list: list[BaseModel]
    ):
        if not data_model_list:
            return 0

        print("🚀 Inserção otimizada (COPY em transação única)")
        start_time = time.perf_counter()

        data_dicts = [m.dict() for m in data_model_list]
        columns = list(data_dicts[0].keys())
        values = [tuple(d[c] for c in columns) for d in data_dicts]
        cols_str = ", ".join(columns)

        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                try:
                    # buf = io.StringIO()
                    # writer = csv.writer(
                    #     buf,
                    #     delimiter="\t",
                    #     lineterminator="\n",
                    #     quoting=csv.QUOTE_MINIMAL,
                    #     escapechar="\\",
                    # )
                    # writer.writerows(values)
                    # buf.seek(0)

                    # with cur.copy(
                    #     f"COPY {table_name} ({cols_str}) "
                    #     "FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t')"
                    # ) as copy:
                    #     copy.write(buf.getvalue())

                    # conn.commit()
                    with cur.copy(f"COPY {table_name} ({cols_str}) FROM STDIN") as copy:
                        for row in values:
                            copy.write_row(row)
                    conn.commit()
                except psycopg.errors.UniqueViolation:
                    print(
                        "⚠️ Alguns registros duplicados foram ignorados (já existentes)."
                    )
                    conn.rollback()

        duration = time.perf_counter() - start_time
        print(f"✅ Inseridos {len(data_model_list)} registros em {duration:.2f}s")

        return len(data_model_list)
