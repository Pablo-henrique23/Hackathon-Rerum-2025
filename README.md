
# 🐄 Bull Querier — NL→SQL com `calc_plan` (Hackathon)

Interface em **Streamlit** que:
1. Recebe a pergunta em português  
2. Gera **SQL (PostgreSQL)** via LLM (GPT ou Ollama Privado local)  
3. Executa a consulta no banco  
4. Gera um **`calc_plan`** (lista de operações determinísticas)  
5. Roda os cálculos utilizando **pandas**
6. Redige a resposta final em linguagem natural via LLM em português (GPT ou Ollama Privado)

---

## Arquitetura (fluxo)
```
Usuário → 
pergunta ─┐
          ├─ LLM.gpt → SQL (SELECT-only, com LIMIT)
          └─ Execução SQL → DataFrame
          └─ LLM.gpt → calc_plan (JSON: sum/mean/topk/…)
          └─ pandas.apply_plan(df, plan) → calc_results
          └─ LLM.traduzir_gpt(SQL + resultados) → resposta PT-BR
```

## Requisitos

- **Docker** (PostgreSQL via docker-compose)
- **Python 3.10+**
- **pip**
- Provedor **OpenAI** (API) e/ou **Ollama** local para Private LLM

---

## Pacotes Python

```bash
pip install streamlit pandas psycopg2-binary requests openpyxl sqlglot
```

## Docker
Subir o banco de dados e popular com os dados do XLSX
```bash
docker compose up -d

# Copiar arquivo SQL com tabelas para o banco novo no docker
docker cp bd/bd.sql pg:/tmp/bd.sql
docker exec -it pg psql -U postgres -d mydb -f /tmp/bd.sql

# populador.py precisa ser executado a partir do próprio diretório em que ele está:
cd bd && python3 populador.py
```

## Rodar o App
```bash
# app.py precisa ser executado a partir do próprio diretório em que ele está:
cd src && streamlit run app.py
```

## Pastas e arquivos:
```bash
bd/
  ├─ bd.sql           # DDL + índices/views
  ├─ populador.py     # Le planilhas xlsx e importa no Postgres
  └─ xlsx/            # Planilhas de entrada
src/
  ├─ app.py           # Streamlit UI (pergunta → SQL → calc_plan → resposta)
  ├─ llm.py           # chamadas LLM (gpt/ private llhama)
  └─ operations.py    # apply_plan(df, plan) — cálculos determinísticos em pandas
docker-compose.yml    # Docker do Postgres
```
