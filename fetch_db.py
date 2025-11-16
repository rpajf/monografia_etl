# Install dependencies as needed:
# pip install kagglehub[pandas-datasets]
# import kagglehub
# from kagglehub import KaggleDatasetAdapter
import time

# Set the path to the file you'd like to load
import pandas as pd
import zipfile
import json

from etl_psycopg3 import DatabaseConnector
from schemas import Artigo, ArtigoStaging

# # Load the latest version
# df = kagglehub.load_dataset(
#   KaggleDatasetAdapter.PANDAS,
#   "allen-institute-for-ai/CORD-19-research-challenge",
#   file_path,
#   # Provide any additional arguments like
#   # sql_query or pandas_kwargs. See the
#   # documenation for more information:
#   # https://github.com/Kaggle/kagglehub/blob/main/README.md#kaggledatasetadapterpandas
# )

path = "/Users/raphaelportela/datasetcovid.zip"
OUTPUT_DIR = "/Users/raphaelportela/monografia_2025/mono_2025"
# https://pentaho.com/
# glue AWS
# INTEGRATION SERVICES
# df = pd.read_csv(
#     "/Users/raphaelportela/datasetcovid.zip",
#     compression="zip",
#     nrows=10  # only first 10 rows
# )
# chunks = pd.read_csv(
#     "/Users/raphaelportela/datasetcovid.zip",
#     compression="zip",
#     chunksize=10  # process 10 rows at a time
# )


zip_path = "/Users/raphaelportela/datasetcovid.zip"


class ZipFileAnalyzer:
    def __init__(self, zip_path):
        self.zip_path = zip_path

    def analyze(self):
        with zipfile.ZipFile(self.zip_path, "r") as z:
            all_files = z.namelist()
            total_files = len(all_files)
            print(f"📊 Total files in ZIP: {total_files:,}")

    def return_files_size(self):
        with zipfile.ZipFile(self.zip_path, "r") as z:
            all_files = z.namelist()
            total_files = len(all_files)
            small_files = []
            medium_files = []
            large_files = []
            for file in all_files:
                if z.getinfo(file).file_size < 1000000:
                    small_files.append(file)
                elif z.getinfo(file).file_size < 10000000:
                    medium_files.append(file)
                else:
                    large_files.append(file)
            print(f"📊 Small files: {len(small_files):,}")
            print(f"📊 Medium files: {len(medium_files):,}")
            print(f"📊 Large files: {len(large_files):,}")

    def return_file_category(self):
        with zipfile.ZipFile(self.zip_path, "r") as z:
            all_files = z.namelist()
            total_files = len(all_files)
            print(f"📊 Total files in ZIP: {total_files:,}")
            json_files = [f for f in all_files if f.endswith(".json")]
            csv_files = [f for f in all_files if f.endswith(".csv")]
            print(f"   JSON files: {len(json_files):,}")
            print(f"   CSV files: {len(csv_files):,}")
            print(f"   Other files: {total_files - len(json_files) - len(csv_files):,}")
            print()
            first_ten = all_files[:20]
            print("📄 First 20 files:")
            for name in first_ten:
                print(f"   {name}")

    def average_file_size(self):
        """Calculate and return the average file size in the ZIP"""
        with zipfile.ZipFile(self.zip_path, "r") as z:
            all_files = z.namelist()

            if not all_files:
                print("⚠️  ZIP file is empty!")
                return 0

            total_size = 0
            for file in all_files:
                total_size += z.getinfo(file).file_size

            average_size = total_size / len(all_files)

            # Print formatted results
            print("📊 File Size Statistics:")
            print(f"   Total files: {len(all_files):,}")
            print(
                f"   Total size: {total_size:,} bytes ({total_size / (1024**2):.2f} MB)"
            )
            print(
                f"   Average size: {average_size:,.2f} bytes ({average_size / 1024:.2f} KB)"
            )

            return average_size

    def get_metadata_info(self):
        with zipfile.ZipFile(zip_path, "r") as z:
            # Find the path of metadata.csv inside the zip
            metadata_path = None
            for name in z.namelist():
                if "metadata.csv" in name:
                    metadata_path = name
                    print("✅ Found metadata file:", metadata_path)
                    break

            if not metadata_path:
                print("❌ metadata.csv not found inside the zip.")
                return None
            with z.open(metadata_path) as f:
                metadata = pd.read_csv(f, low_memory=False)

        # Read the CSV directly from inside the ZIP using pandas
        # metadata = pd.read_csv(zip_path, compression="zip", storage_options={"archive_name": metadata_path})
        print("✅ Loaded metadata.csv successfully!")
        print("Columns:", list(metadata.columns))
        print("Number of records:", len(metadata))
        print(metadata.head(3))
        return metadata

    def return_metada_as_df(self, paper_id=None):
        with zipfile.ZipFile(zip_path, "r") as z:
            metadata_path = None
            for name in z.namelist():
                if "metadata.csv" in name:
                    metadata_path = name
                    print("✅ Found metadata file:", metadata_path)
                    break

            if metadata_path:
                with z.open(metadata_path) as f:
                    metadata_df = pd.read_csv(f, low_memory=False)
                print(
                    f"✅ Loaded metadata.csv with {len(metadata_df):,} rows and {len(metadata_df.columns)} columns."
                )
                print("\n📄 First 20 rows:\n")
                print(metadata_df.head(20))
                print("Columns:", list(metadata_df.columns))
            else:
                print("❌ metadata.csv not found inside the ZIP.")
            if paper_id:
                matches = metadata_df[
                    metadata_df["sha"].astype(str).str.contains(paper_id, na=False)
                ]
                if not matches.empty:
                    print(
                        f"\n🔍 Found {len(matches)} match(es) for paper_id = {paper_id}"
                    )
                    print(
                        matches[
                            [
                                "title",
                                "authors",
                                "doi",
                                "journal",
                                "publish_time",
                                "url",
                            ]
                        ]
                    )
                    print("matches", matches)
                    return matches
            else:
                print(f"⚠️ No matches found for {paper_id}")
                return None

    def get_paragraphs_data(self, number_of_files, offset=0):
        with zipfile.ZipFile(self.zip_path, "r") as z:
            body_records = []
            data_dict = {}
            records = []
            cite_rows = []
            start_index = offset
            json_files = [f for f in z.namelist() if f.endswith(".json")]
            end_index = offset + number_of_files if number_of_files else len(json_files)

            # DEBUG: Mostra informações do slice
            total_jsons = len(json_files)
            actual_slice = json_files[start_index:end_index]
            print(f"🔍 DEBUG: Total JSONs no ZIP: {total_jsons:,}")
            print(f"🔍 DEBUG: Slice solicitado: [{start_index:,}:{end_index:,}]")
            print(f"🔍 DEBUG: JSONs no slice: {len(actual_slice):,}")

            # for filename in json_files[:number_of_files]:
            for filename in actual_slice:
                with z.open(filename) as f:
                    data = json.load(f)
                    # all_data.append(data)
                    data_dict[filename] = data
                    body_text = " ".join([p["text"] for p in data.get("body_text", [])])

                    # Adiciona registro principal
                    records.append(
                        {
                            "file_name": filename,
                            "paper_id": data.get("paper_id"),
                            "title": data.get("metadata", {}).get("title"),
                            "authors": [
                                a.get("last", "")
                                for a in data.get("metadata", {}).get("authors", [])
                            ],
                            "body_text": body_text,
                        }
                    )

                    for p in data.get("body_text", []):
                        cite_spans = p.get("cite_spans", [])
                        body_records.append(
                            {
                                "title": data.get("metadata", {}).get("title"),
                                "paper_id": data.get("paper_id"),
                                "section": p.get("section"),
                                "text": p.get("text"),
                            }
                        )
                        if cite_spans:
                            for c in cite_spans:
                                cite_rows.append(
                                    {
                                        "paper_id": data.get("paper_id"),
                                        "section": p.get("section"),
                                        "cite_text": c.get("text"),
                                        "ref_id": c.get("ref_id"),
                                    }
                                )

            body_text_df = pd.DataFrame(body_records)
            cite_rows_df = pd.DataFrame(cite_rows)

            # Print de quantos JSONs foram processados neste batch
            num_jsons = len(data_dict)
            num_registros = len(body_records)
            print(
                f"📄 Lidos {num_jsons:,} arquivos JSON do ZIP (offset {start_index:,} a {start_index + num_jsons:,})"
            )
            print(
                f"📝 Gerados {num_registros:,} registros (média de {num_registros/num_jsons:.1f} registros por JSON)"
            )

        return body_text_df, cite_rows_df

    # def increment_offset_and_get_files_data(self, number_of_siles,offset, number_of_files, offset=0):

    def get_files_data_no_references(self, number_of_files=2):
        with zipfile.ZipFile(self.zip_path, "r") as z:
            data_dict = {}
            json_files = [f for f in z.namelist() if f.endswith(".json")]

            print("📦 Total de arquivos JSON encontrados:", len(json_files))

            for filename in json_files[:number_of_files]:
                with z.open(filename) as f:
                    data = json.load(f)

                    # 🔹 Remove campos que não queremos imprimir
                    data.pop("bib_entries", None)
                    data.pop("ref_entries", None)
                    data.pop("back_matter", None)

                    data_dict[filename] = data

            # 🔹 Exibe os dois primeiros arquivos sem as referências
            for file_name, content in list(data_dict.items())[:1]:
                print(f"\n📝 Arquivo: {file_name}")
                print(json.dumps(content, indent=2))

        return data_dict

    def get_files_data_as_dataframe(self, number_of_files, offset=0):
        """
        Lê arquivos JSON do dataset CORD-19 dentro de um ZIP,
        remove seções não utilizadas e converte em DataFrames.
        """
        with zipfile.ZipFile(self.zip_path, "r") as z:
            json_files = [f for f in z.namelist() if f.endswith(".json")]

            records = []
            body_records = []
            start_index = offset
            end_index = offset + number_of_files if number_of_files else len(json_files)

            total_jsons = len(json_files)
            actual_slice = json_files[start_index:end_index]
            print(f"🔍 DEBUG: Total JSONs no ZIP: {total_jsons:,}")
            print(f"🔍 DEBUG: Slice solicitado: [{start_index:,}:{end_index:,}]")
            print(f"🔍 DEBUG: JSONs no slice: {len(actual_slice):,}")

            for filename in actual_slice:
                with z.open(filename) as f:
                    data = json.load(f)
                    # Concatena o corpo do texto em um único campo
                    body_text = " ".join([p["text"] for p in data.get("body_text", [])])
                    # print('body_text', body_text)
                    # Adiciona registro principal
                    records.append(
                        {
                            "paper_id": data.get("paper_id"),
                            "title": data.get("metadata", {}).get("title"),
                            "file_name": filename,
                            # "authors": [a.get("last", "") for a in data.get("metadata", {}).get("authors", [])],
                            "body_text": body_text,
                        }
                    )

                    # (Opcional) Armazena os parágrafos separadamente
                    # for p in data.get("body_text", []):
                    #     body_records.append({
                    #         "paper_id": data.get("paper_id"),
                    #         "section": p.get("section"),
                    #         "text": p.get("text")
                    #     })

            # 🔹 Cria DataFrames principais
            articles_df = pd.DataFrame(records)
            # print('printando arquivos do body', body_records)
            # body_text_df = pd.DataFrame(body_records)

            return articles_df

    async def execute_batch_parallel(
        self, batch_size, num_of_files, offset=0, max_tasks: int = 4
    ):
        connector = DatabaseConnector()
        batch_count = 0
        total_processado = 0
        batch_metrics: list[dict] = []
        start_total = time.perf_counter()
        remaining = num_of_files
        current_offset = offset

        while remaining > 0:
            batch_count += 1
            start_batch = time.perf_counter()
            slice_size = min(batch_size, remaining)

            parse_start = time.perf_counter()
            articles_df = self.get_files_data_as_dataframe(
                number_of_files=slice_size, offset=current_offset
            )
            if articles_df.empty:
                print("nenhum arquivo encontrado")
                break

            models_artigos = [
                ArtigoStaging(**row) for row in articles_df.to_dict(orient="records")
            ]
            parse_time = time.perf_counter() - parse_start

            insert_result = await connector.insert_async_parallel(
                table_name="artigos_stg",
                data_model_list=models_artigos,
                chunk_size=min(slice_size, 5000),
                max_tasks=max_tasks,
                use_copy=False,  # Temporarily disable COPY until async issue is resolved
            )

            batch_time = time.perf_counter() - start_batch
            remaining -= len(models_artigos)
            current_offset += len(models_artigos)
            inserted = insert_result.get("inserted", 0)
            insert_time = insert_result.get("duration", 0.0)
            total_processado += inserted

            batch_metrics.append(
                {
                    "batch_index": batch_count,
                    "batch_size": len(models_artigos),
                    "parse_time": parse_time,
                    "insert_time": insert_time,
                    "total_time": batch_time,
                    "inserted": inserted,
                }
            )

            print(
                f"⏱Tempo do batch: {batch_time:.2f}s "
                f"(parse={parse_time:.2f}s, insert={insert_time:.2f}s, "
                f"{inserted:,} registros)"
            )

        total_time = time.perf_counter() - start_total
        print(f"Total de batches processados: {batch_count}")
        print(f"Tempo total: {total_time:.2f}s ({total_time/60:.2f} minutos)")
        return {
            "total_inserted": total_processado,
            "batch_metrics": batch_metrics,
            "total_time": total_time,
        }
            

    def execute_batch_insert(self, batch_size, num_of_files, offset=0):
        """
        Synchronous batch processing using COPY method (single transaction).
        Returns metrics compatible with benchmark framework.
        
        Args:
        batch_size (int): Number of files to process per batch.
        num_of_files (int): Total number of files to process.
        offset (int): Starting index for reading from the ZIP file.
        
        Returns:
        dict: Contains total_inserted, batch_metrics, and total_time
        """
        connector = DatabaseConnector()
        batch_count = 0
        total_processado = 0
        batch_metrics: list[dict] = []
        start_total = time.perf_counter()
        remaining = num_of_files
        current_offset = offset

        if not num_of_files:
            return {"total_inserted": 0, "batch_metrics": [], "total_time": 0.0}

        while remaining > 0:
            batch_count += 1
            start_batch = time.perf_counter()
            slice_size = min(batch_size, remaining)

            # Parse phase
            parse_start = time.perf_counter()
            articles_df = self.get_files_data_as_dataframe(
                number_of_files=slice_size, offset=current_offset
            )
            if articles_df.empty:
                print("nenhum arquivo encontrado")
                break

            models_artigos = [
                ArtigoStaging(**row) for row in articles_df.to_dict(orient="records")
            ]
            parse_time = time.perf_counter() - parse_start

            # Insert phase
            insert_start = time.perf_counter()
            inserted = connector.insert_optimized_single_transaction(
                table_name="artigos_stg", data_model_list=models_artigos
            )
            insert_time = time.perf_counter() - insert_start

            batch_time = time.perf_counter() - start_batch
            remaining -= len(models_artigos)
            current_offset += len(models_artigos)
            total_processado += inserted

            batch_metrics.append(
                {
                    "batch_index": batch_count,
                    "batch_size": len(models_artigos),
                    "parse_time": parse_time,
                    "insert_time": insert_time,
                    "total_time": batch_time,
                    "inserted": inserted,
                }
            )

            print(
                f"⏱Tempo do batch: {batch_time:.2f}s "
                f"(parse={parse_time:.2f}s, insert={insert_time:.2f}s, "
                f"{inserted:,} registros)"
            )

        total_time = time.perf_counter() - start_total
        print(f"Total de batches processados: {batch_count}")
        print(f"Tempo total: {total_time:.2f}s ({total_time/60:.2f} minutos)")
        
        return {
            "total_inserted": total_processado,
            "batch_metrics": batch_metrics,
            "total_time": total_time,
        }

    def join_tables(self, tables):
        pass


if __name__ == "__main__":
    analyzer = ZipFileAnalyzer(zip_path)

    connector = DatabaseConnector()
    table = "artigos"
    batch_size = 15000
    offset = 0
    total_processado = 0
    total_jsons_processados = 0
    batch_count = 0

    print(f"\n{'='*70}")
    print("🚀 INICIANDO PROCESSAMENTO EM BATCHES")
    print(f"{'='*70}")
    print(f"📦 Batch size: {batch_size:,} arquivos por vez")
    print("🎯 Método: COPY otimizado (transação única por batch)\n")

    # Tempo total de início
    start_total = time.perf_counter()
    analyzer.get_files_data_as_dataframe

    while True:
        batch_count += 1
        print(f"\n{'─'*70}")
        print(f"BATCH {batch_count} - Offset: {offset:,}")
        print(f"{'─'*70}")

        # Tempo do batch
        start_batch = time.perf_counter()

        # Lê arquivos do ZIP
        body_text_df, cite_text_df = analyzer.get_paragraphs_data(
            number_of_files=batch_size, offset=offset
        )

        # Se não tem mais dados, termina
        if len(body_text_df) == 0:
            print("✅ Nenhum dado retornado - processamento concluído!")
            break

        # Converte para modelos
        models_artigos = [
            Artigo(**row) for row in body_text_df.to_dict(orient="records")
        ]

        # Insere no banco
        connector.insert_optimized_single_transaction(
            table_name=table, data_model_list=models_artigos
        )

        # Calcula métricas do batch
        batch_time = time.perf_counter() - start_batch
        batch_rate = len(models_artigos) / batch_time if batch_time > 0 else 0

        jsons_neste_batch = min(
            batch_size, len(body_text_df)
        )  # Aproximação conservadora

        total_processado += len(models_artigos)
        total_jsons_processados += jsons_neste_batch
        offset += batch_size

        # Mostra progresso do batch
        print(f"Tempo do batch: {batch_time:.2f}s")
        print(f"Registros inseridos neste batch: {len(models_artigos):,}")
        print(f"⚡ Taxa do batch: {batch_rate:.0f} registros/s")
        print(f" JSONs processados neste batch: ~{jsons_neste_batch:,}")
        print(
            f"Total acumulado: {total_processado:,} registros de ~{total_jsons_processados:,} JSONs"
        )

    # Métricas finais
    end_total = time.perf_counter()
    total_time = end_total - start_total
    avg_rate = total_processado / total_time if total_time > 0 else 0

    print(f"\n{'='*70}")
    print("🎉 PROCESSAMENTO CONCLUÍDO!")
    print(f"{'='*70}")
    print(f"📊 Total de batches processados: {batch_count}")
    print(f"📁 Total de JSONs processados: ~{total_jsons_processados:,}")
    print(f"📈 Total de registros inseridos: {total_processado:,}")
    if total_jsons_processados > 0:
        print(
            f"📝 Média de registros por JSON: {total_processado/total_jsons_processados:.1f}"
        )
    print(f"⏱️  Tempo total: {total_time:.2f}s ({total_time/60:.2f} minutos)")
    print(f"⚡ Taxa média geral: {avg_rate:.0f} registros/segundo")
    print(f"{'='*70}\n")

    # MÉTODO 1: Inserção padrão (executemany)
    # print("📌 MÉTODO 1: Inserção Padrão (executemany)")
    # connector.insert_into_table_typed(
    #     data_model=models_artigos,
    #     table_name=table
    # )

    # MÉTODO 2: Paralelo com conexões novas (LENTO - não recomendado)
    # print("\n📌 MÉTODO 2: Paralelo com novas conexões (batch_process_rows)")
    # connector.batch_process_rows(
    #     data_model_list=models_artigos,
    #     table_name=table,
    #     batch_size=1000,
    #     max_workers=4
    # )

    # MÉTODO 3: RECOMENDADO para datasets pequenos/médios
    print("📌 MÉTODO 3 (RECOMENDADO): Transação única otimizada")
    connector.insert_optimized_single_transaction(
        table_name=table, data_model_list=models_artigos
    )
