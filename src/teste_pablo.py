import requests
import psycopg2
import re
from time import time

i = time()
# conexão com o Postgres
conn = psycopg2.connect(
    dbname="hackathon-rerum-2025",
    user="postgres",
    password="pablo",
    host="localhost"
)
cur = conn.cursor()

schema = """
bovinos(
    codigo TEXT PRIMARY KEY,
    nome TEXT,
    sexo CHAR(1),              -- 'M' ou 'F'
    pais_origem TEXT,
    data_nascimento DATE,
    raca_id TEXT,
    numerorgpai TEXT REFERENCES bovinos(codigo),  -- Pai
    numerorgmae TEXT REFERENCES bovinos(codigo)   -- Mãe
)

fichalactacao(
    id SERIAL PRIMARY KEY,
    codigo_bovino TEXT REFERENCES bovinos(codigo),   -- Animal avaliado
    formacoleta TEXT,
    idademesesparto INTEGER,
    numeroordenhas INTEGER,
    qtdediaslactacao INTEGER,
    qtdeleite305 NUMERIC,      -- produção padronizada em 305 dias
    qtdegordura305 NUMERIC,
    qtdeproteina305 NUMERIC,
    dataencerramento DATE,
    ideventoparto INTEGER REFERENCES ocorrenciaEvento(id),
    ideventoseca INTEGER REFERENCES ocorrenciaEvento(id)
)

ocorrenciaEvento(
    id SERIAL PRIMARY KEY,
    idbovino INTEGER REFERENCES bovinos(codigo),     -- ID do bovino
    codigo_bovino TEXT REFERENCES bovinos(codigo),   -- Código do bovino
    dataocorrencia DATE,
    facilidade_parto TEXT,
    nro_crias INTEGER,
    qtde_litros NUMERIC,
    sexo_crias CHAR(1),
    tipo_evento INTEGER
)

bovinos_genealogia(
    codigo TEXT PRIMARY KEY REFERENCES bovinos(codigo),
    nome TEXT,
    sexo CHAR(1),

    -- Relações familiares
    codigo_pai TEXT REFERENCES bovinos(codigo),
    nome_pai TEXT,
    codigo_mae TEXT REFERENCES bovinos(codigo),
    nome_mae TEXT,

    -- Avós
    codigo_avo_paterno TEXT REFERENCES bovinos(codigo),
    nome_avo_paterno TEXT,
    codigo_avo_materno TEXT REFERENCES bovinos(codigo),
    nome_avo_materno TEXT,

    -- Bisavós
    codigo_bisavo_paterno_paterno TEXT REFERENCES bovinos(codigo),
    codigo_bisavo_paterno_materno TEXT REFERENCES bovinos(codigo),
    codigo_bisavo_materno_paterno TEXT REFERENCES bovinos(codigo),
    codigo_bisavo_materno_materno TEXT REFERENCES bovinos(codigo)
)

impacto_producao_genealogico(
    codigo_ancestral TEXT REFERENCES bovinos(codigo),
    nome_ancestral TEXT,
    sexo_ancestral CHAR(1),
    nivel_parentesco INTEGER,  -- 1=filhos, 2=netos, 3=bisnetos
    media_leite NUMERIC,
    producao_total NUMERIC,
    qtd_descendentes INTEGER,
    PRIMARY KEY (codigo_ancestral, nivel_parentesco)
)

-- VIEWS DE APOIO (referência sem definição completa)
media_filhas_por_touro(codigo_touro, nome_touro, qtd_filhas, media_leite_filhas, producao_total_filhas)
producao_vitalicia(codigo_vaca, nome_vaca, qtd_lactacoes, producao_total_leite, media_por_lactacao)
resumo_genealogico_produtivo(codigo, nome, codigo_pai, codigo_mae, media_leite, qtd_descendentes)
"""

query = "Qual o touro que possui as filhas com a maior média de produção?"

prompt = f"""
Você é um gerador SQL para PostgreSQL.
Gere uma query SQL CORRETA e EXECUTÁVEL que responda à pergunta.

Regras obrigatórias:
- Use SOMENTE tabelas e colunas do schema fornecido nem valores.
- NÃO invente aliases não declarados.
- Declare todos os aliases de forma explícita (ex: FROM bovinos b).
- Use apenas operadores padrão (=, >, <, LIKE, IN, BETWEEN, JOIN ... ON).
- NÃO use ANY(), ALL(), SOME(), operadores de array ou funções não definidas.
- NÃO use HAVING sem agregação válida.
- NÃO adicione explicações, textos ou comentários.
- Retorne APENAS o SQL entre as tags <SQL></SQL>.
- O SQL deve começar com SELECT e terminar com ponto e vírgula.

Schema:
{schema}

Pergunta: {query}
"""

resp = requests.post(
    "http://localhost:11434/api/generate",
    # json={"model": "phi3:mini:4bit", "prompt": prompt, "stream": False,
    json={"model": "phi3:mini", "prompt": prompt, "stream": False,
            "options": {
        #     # "temperature": 0.0,
        #     "num_ctx": 2048,
            "num_thread": 11,   # ou o número de núcleos do seu processador
        #     # "top_p": 0.9
        }
    }
)


resposta = resp.json()["response"].strip()
print("Resposta:", resposta)

match = re.search(r"<SQL>(.*?)</SQL>", resposta, re.DOTALL)

sql_query = match.group(1).strip() if match else resposta
sql_query = re.sub(r'--.*?\n', '', sql_query)  # remove comentários
sql_query = re.sub(r'/\*.*?\*/', '', sql_query, flags=re.DOTALL)
sql_query = sql_query.strip()


# loc = sql_query.find('```sql')
# print(f'loc = {loc}')
# sql_query = sql_query[loc:]
# if loc == 0:
sql_query = sql_query.replace('```','')
sql_query = sql_query.replace('sql','')

# sql_query = re.search(r"<SQL>(.*?)</SQL>", resposta, re.DOTALL).group(1).strip()
print("SQL gerada:", sql_query)

try:
    cur.execute(sql_query)
    rows = cur.fetchall()
    print("Resultado:", rows)
except Exception as e:
    print("Erro na execução:", e)

conn.close()    


print(f'tempo: {time() - i}')