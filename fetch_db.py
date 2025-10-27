# Install dependencies as needed:
# pip install kagglehub[pandas-datasets]
# import kagglehub
# from kagglehub import KaggleDatasetAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Set the path to the file you'd like to load
import pandas as pd
import zipfile
import io
import csv
import json
from itertools import islice

from etl_psycopg3 import DatabaseConnector
from schemas import Artigo

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

path = '/Users/raphaelportela/datasetcovid.zip'
OUTPUT_DIR = '/Users/raphaelportela/monografia_2025/mono_2025'
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
            json_files = [f for f in all_files if f.endswith('.json')]
            csv_files = [f for f in all_files if f.endswith('.csv')]
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
            print(f"📊 File Size Statistics:")
            print(f"   Total files: {len(all_files):,}")
            print(f"   Total size: {total_size:,} bytes ({total_size / (1024**2):.2f} MB)")
            print(f"   Average size: {average_size:,.2f} bytes ({average_size / 1024:.2f} KB)")
            
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
    # Find the metadata.csv file (it might be nested)
            metadata_path = None
            for name in z.namelist():
                if "metadata.csv" in name:
                    metadata_path = name
                    print("✅ Found metadata file:", metadata_path)
                    break

            if metadata_path:
                with z.open(metadata_path) as f:
                    metadata_df = pd.read_csv(f, low_memory=False)
                print(f"✅ Loaded metadata.csv with {len(metadata_df):,} rows and {len(metadata_df.columns)} columns.")
                print("\n📄 First 20 rows:\n")
                print(metadata_df.head(20))
                print("Columns:", list(metadata_df.columns))
            else:
                print("❌ metadata.csv not found inside the ZIP.")
            if paper_id:
                matches = metadata_df[metadata_df['sha'].astype(str).str.contains(paper_id, na=False)]
                if not matches.empty:
                    print(f"\n🔍 Found {len(matches)} match(es) for paper_id = {paper_id}")
                    print(matches[['title', 'authors','doi', 'journal', 'publish_time', 'url']])
                    print('matches', matches)
                    return matches
            else:
                print(f"⚠️ No matches found for {paper_id}")
                return None



        

    def get_files_data(self, number_of_files):
        with zipfile.ZipFile(self.zip_path, "r") as z:
            # json_files = []
            # all_files = z.namelist()
            all_data = []
            body_records = []
            data_dict = {}
            records = []
            cite_rows = []
            json_files = [f for f in z.namelist() if f.endswith('.json')]
            for filename in json_files[:number_of_files]:
                with z.open(filename) as f:
                    data = json.load(f)
                    # all_data.append(data)
                    data_dict[filename] = data
                    body_text = " ".join([p["text"] for p in data.get("body_text", [])])

                    # Adiciona registro principal
                    records.append({
                        "file_name": filename,
                        "paper_id": data.get("paper_id"),
                        "title": data.get("metadata", {}).get("title"),
                        "authors": [a.get("last", "") for a in data.get("metadata", {}).get("authors", [])],
                        "body_text": body_text
                    })

                    for p in data.get("body_text", []):
                        cite_spans = p.get("cite_spans", [])
                        body_records.append({
                             "title": data.get("metadata", {}).get("title"),
                            "paper_id": data.get("paper_id"),
                            "section": p.get("section"),
                            "text": p.get("text"),

                        }) 
                        if cite_spans:
                            for c in cite_spans:
                                cite_rows.append({
                                    "paper_id": data.get("paper_id"),
                                    "section": p.get("section"),
                                    "cite_text": c.get("text"),
                                    "ref_id": c.get("ref_id")
                                })
                    # for p in data.get("body_text", []):
                    #     print('p', p)
                    #     cite_rows.append({
                    #         "paper_id": data.get("paper_id"),
                    #         "section": p.get("section"),
                    #         "cite_spans": p.get("cite_spans")
                    #     })     
            first_file = list(data_dict.keys())[0]
            articles_df = pd.DataFrame(records)
            body_text_df = pd.DataFrame(body_records)
            cite_rows_df = pd.DataFrame(cite_rows)
            # print("cite", cite_rows_df)
            # print("body", body_text_df)
            # files_df = 
            # print(f"First file name: {first_file}")
            # print(f"First file content:\n{json.dumps(data_dict[first_file], indent=2)}")

        return body_text_df, cite_rows_df
    
    def get_files_data_no_references(self, number_of_files=2):
        with zipfile.ZipFile(self.zip_path, "r") as z:
            data_dict = {}
            json_files = [f for f in z.namelist() if f.endswith('.json')]

            print('📦 Total de arquivos JSON encontrados:', len(json_files))

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
    def get_files_data_as_dataframe(self, number_of_files=2):
        """
        Lê arquivos JSON do dataset CORD-19 dentro de um ZIP,
        remove seções não utilizadas e converte em DataFrames.
        """
        with zipfile.ZipFile(self.zip_path, "r") as z:
            json_files = [f for f in z.namelist() if f.endswith('.json')]
            print('📦 Total de arquivos JSON encontrados:', len(json_files))

            records = []        # lista de artigos resumidos
            body_records = []   # lista de parágrafos (opcional)

            for filename in json_files[:number_of_files]:
                with z.open(filename) as f:
                    data = json.load(f)

                    # Concatena o corpo do texto em um único campo
                    body_text = " ".join([p["text"] for p in data.get("body_text", [])])

                    # Adiciona registro principal
                    records.append({
                        "file_name": filename,
                        "paper_id": data.get("paper_id"),
                        "title": data.get("metadata", {}).get("title"),
                        "authors": [a.get("last", "") for a in data.get("metadata", {}).get("authors", [])],
                        "body_text": body_text
                    })

                    # (Opcional) Armazena os parágrafos separadamente
                    for p in data.get("body_text", []):
                        body_records.append({
                            "paper_id": data.get("paper_id"),
                            "section": p.get("section"),
                            "text": p.get("text")
                        })

            # 🔹 Cria DataFrames principais
            articles_df = pd.DataFrame(records)
            body_text_df = pd.DataFrame(body_records)

            print(f"\n✅ {len(articles_df)} artigos carregados em 'articles_df'")
            print(f"✅ {len(body_text_df)} parágrafos carregados em 'body_text_df'")

            print("\n📄 Prévia dos dados (articles_df):")
            print(articles_df.head(3).to_string(index=False))

            return {
                "articles_df": articles_df,
                "body_text_df": body_text_df
            }



# ---------------------------------------
# with zipfile.ZipFile(zip_path, "r") as z:
#     # Count total files
#     all_files = z.namelist()
#     total_files = len(all_files)
    
#     print(f"📊 Total files in ZIP: {total_files:,}")
    
#     # Count by type
#     json_files = [f for f in all_files if f.endswith('.json')]
#     csv_files = [f for f in all_files if f.endswith('.csv')]
    
#     print(f"   JSON files: {len(json_files):,}")
#     print(f"   CSV files: {len(csv_files):,}")
#     print(f"   Other files: {total_files - len(json_files) - len(csv_files):,}")
#     print()
    
#     # Get just the first 10 entries
#     first_ten = all_files[:20]
#     print("📄 First 20 files:")
#     for name in first_ten:
#         print(f"   {name}") 

if __name__ == "__main__":
    analyzer = ZipFileAnalyzer(zip_path)
    
    # Analyze JSON files - you can change the number of files to analyze
    # results = analyzer.return_file_category(num_files=5)  # Change 5 to any number you want
    
    body_text_df, cite_text_df = analyzer.get_files_data(number_of_files=None)
    # print('body',body_text_df)
    # analyzer.return_file_category()
    # analyzer.average_file_size()
    # analyzer.return_files_size()
    # analyzer.get_metadata_info()
    # analyzer.get_files_data_as_dataframe()
    # analyzer.get_files_data_no_references(number_of_files=1)
    # paper_id = "0000028b5cc154f68b8a269f6578f21e31f62977"
    print('len', len(body_text_df))

    # analyzer.return_metada_as_df(paper_id=paper_id)
    connector = DatabaseConnector()
    table = 'artigos'
    models_artigos = [Artigo(**row) for row in body_text_df.to_dict(orient="records")]

    print(f"\n{'='*60}")
    print(f"🧪 TESTE DE PERFORMANCE - {len(models_artigos)} registros")
    print(f"{'='*60}\n")

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
        table_name=table,
        data_model_list=models_artigos
    )

    # MÉTODO 4: Paralelo com pool (útil apenas para datasets MUITO grandes)
    # print("\n📌 MÉTODO 4: Paralelo com ConnectionPool")
    # connector.batch_process_with_pool(
    #     table_name="artigos",
    #     data_model_list=models_artigos,
    #     batch_size=5000,  # Aumentado para reduzir overhead
    #     max_workers=3      # Reduzido para evitar contention
    # )

    # columns = """
    #     id SERIAL PRIMARY KEY,
    #     paper_id VARCHAR(100) NOT NULL,
    #     title TEXT,
    #     section TEXT,
    #     content TEXT,
    #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    # """
    # connector.create_table("articles", columns)

    # connector = DatabaseConnector()

    # columns = """
    #     id SERIAL PRIMARY KEY,
    #     paper_id VARCHAR(100) NOT NULL,
    #     section TEXT,
    #     ref_id VARCHAR(50),
    #     cite_text TEXT,
    #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    # """

    # connector.create_table("articles_citation", columns)


   
    # Access the results programmatically
    # print("\n🔑 Programmatic Access Example:")
    # if results:
    #     first_file = results[0]
    #     print(f"   First file: {first_file['file_name']}")
    #     print(f"   Keys available: {first_file['keys']}")
    #     print(f"   You can access data: first_file['data']['paper_id']")
    
    # Optional: uncomment to see more details
    # analyzer.return_file_category()
    # analyzer.return_files_size()
    # analyzer.average_file_size()