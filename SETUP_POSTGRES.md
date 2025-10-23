# PostgreSQL Setup para Projeto ETL COVID-19

## 📋 Arquivos Criados

- `docker-compose.yml` - Configuração do PostgreSQL e pgAdmin
- `init_db.sql` - Script de inicialização do banco de dados
- `db_config.py` - Gerenciador de conexões Python
- `requirements.txt` - Atualizado com dependências PostgreSQL

## 🚀 Passo a Passo

### 1. Instalar Docker (se ainda não tiver)

```bash
# Verificar se Docker está instalado
docker --version
docker-compose --version
```

Se não tiver, baixe em: https://www.docker.com/products/docker-desktop

### 2. Iniciar PostgreSQL

```bash
# No diretório do projeto
cd /Users/raphaelportela/mono_2025

# Iniciar os containers (PostgreSQL + pgAdmin)
docker-compose up -d

# Verificar se os containers estão rodando
docker-compose ps
```

### 3. Instalar Dependências Python

```bash
# Ativar seu ambiente virtual (se tiver)
source venv/bin/activate

# Instalar novas dependências
pip install -r requirements.txt
```

### 4. Testar Conexão

```bash
# Testar conexão com o banco
python db_config.py
```

## 🔧 Configurações do Banco

### Credenciais Padrão:
- **Host:** localhost
- **Porta:** 5432
- **Database:** covid_etl
- **Usuário:** etl_user
- **Senha:** etl_password_2025
- **Schema:** covid_data

### Acessar pgAdmin (Interface Web):
1. Abra o navegador: http://localhost:5050
2. Login:
   - Email: admin@etl.com
   - Senha: admin
3. Adicionar servidor:
   - Host: postgres (ou host.docker.internal no Mac)
   - Porta: 5432
   - Database: covid_etl
   - Usuário: etl_user
   - Senha: etl_password_2025

## 📊 Tabelas Criadas

O script `init_db.sql` cria automaticamente:

1. **papers** - Armazena os 716K artigos JSON
2. **authors** - Informações dos autores
3. **paper_authors** - Relacionamento muitos-para-muitos
4. **metadata** - Metadados do arquivo metadata.csv (1.5 GB)
5. **embeddings** - Embeddings do arquivo de 14.8 GB
6. **etl_metrics** - Métricas de performance do ETL (para seu TCC!)

## 🛠️ Comandos Úteis

```bash
# Ver logs do PostgreSQL
docker-compose logs -f postgres

# Parar os containers
docker-compose stop

# Iniciar novamente
docker-compose start

# Parar e remover (CUIDADO: apaga os dados!)
docker-compose down

# Parar e remover INCLUINDO volumes (apaga tudo)
docker-compose down -v

# Acessar o PostgreSQL via linha de comando
docker exec -it etl_postgres psql -U etl_user -d covid_etl

# Backup do banco
docker exec etl_postgres pg_dump -U etl_user covid_etl > backup.sql

# Restaurar backup
docker exec -i etl_postgres psql -U etl_user covid_etl < backup.sql
```

## 🎯 Otimizações PostgreSQL Aplicadas

O `docker-compose.yml` já inclui otimizações para ETL:

- `max_connections=200` - Conexões paralelas
- `shared_buffers=256MB` - Cache de dados
- `effective_cache_size=1GB` - Otimização de queries
- `maintenance_work_mem=64MB` - Para COPY e CREATE INDEX
- `work_mem=2621kB` - Por operação de sort/hash

## 📝 Próximos Passos

1. ✅ PostgreSQL rodando
2. ✅ Schema e tabelas criadas
3. ⏭️ Criar script ETL para extrair dados do ZIP
4. ⏭️ Implementar estratégias de performance (baseline vs otimizado)
5. ⏭️ Adicionar métricas e benchmarking

## ❓ Troubleshooting

### Porta 5432 já está em uso
```bash
# Verificar o que está usando a porta
lsof -i :5432

# Ou mudar a porta no docker-compose.yml
ports:
  - "5433:5432"  # usa 5433 no host
```

### Container não inicia
```bash
# Ver logs de erro
docker-compose logs postgres

# Remover volumes e tentar novamente
docker-compose down -v
docker-compose up -d
```

### Erro de conexão Python
```bash
# Verificar se PostgreSQL está respondendo
docker-compose ps
docker exec etl_postgres pg_isready -U etl_user
```


