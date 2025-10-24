import requests, re, json, os


def _call_openai(messages, temperature=0.0, max_tokens=800):
    base = "https://api.openai.com/v1"
    # key -->"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"
    api_key = os.getenv("OPENAI_API_KEY")
    model = "gpt-4o-mini"

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": messages
    }
    print(f"MESSAGES: {messages}")
    r = requests.post(f"{base}/chat/completions", headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()

def _extract_and_sanitize_sql(text: str) -> str:
    # pega entre <SQL>...</SQL> se existir; senão usa o texto inteiro
    m = re.search(r"<SQL>(.*?)</SQL>", text, flags=re.DOTALL | re.IGNORECASE)
    sql = m.group(1) if m else text

    # remove codefences, comentários e rótulos 'sql'
    sql = re.sub(r"```+", "", sql)
    sql = re.sub(r"(?i)\bsql\b", "", sql)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)         # /* ... */
    sql = re.sub(r"^\s*--.*?$", "", sql, flags=re.MULTILINE)     # -- ...
    sql = sql.strip()

    # tenta isolar primeiro SELECT se vier lixo antes/depois
    m2 = re.search(r"(?is)(select\b.*)", sql)
    if m2:
        sql = m2.group(1).strip()

    # garante ; no fim
    if not sql.rstrip().endswith(";"):
        sql = sql.rstrip() + ";"

    return sql

def _compact_rows(rows, max_rows=50, max_chars=8000):
    """
    Converte o resultado (list[dict] ou semelhante) em JSON legível,
    cortando para no máximo max_rows e max_chars.
    """
    try:
        # garante lista de dicts
        if isinstance(rows, dict):
            data = [rows]
        elif isinstance(rows, list):
            # se vier lista de tuplas, deixa como veio
            data = rows[:max_rows]
        else:
            data = [rows]
        txt = json.dumps(data, ensure_ascii=False, indent=2)
    except Exception:
        txt = str(rows)[:max_chars]

    if len(txt) > max_chars:
        txt = txt[:max_chars] + "\n... [TRUNCADO]"
    return txt

def _extract_json_block(text: str) -> dict:
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception as e:
        raise ValueError(f"LLM não retornou JSON válido: {e}. Trecho: {text[:200]}")




class Chamar():
    def __init__(self, pergunta):
        self.pergunta = pergunta
        self.superior = """
Você é um gerador SQL para PostgreSQL.
Gere uma query SQL CORRETA e EXECUTÁVEL que responda à pergunta.
- NÃO adicione explicações, textos ou comentários.

Regras obrigatórias:
- Use SOMENTE tabelas e colunas do schema fornecido nem valores.
- NÃO invente aliases não declarados.
- Declare todos os aliases de forma explícita (ex: FROM bovinos b).
- Use apenas operadores padrão (=, >, <, LIKE, IN, BETWEEN, JOIN ... ON).
- NÃO use ANY(), ALL(), SOME(), operadores de array ou funções não definidas.
- NÃO use HAVING sem agregação válida.
- Retorne APENAS o SQL entre as tags <SQL></SQL>.
- O SQL deve começar com SELECT e terminar com ponto e vírgula."""
        self.schema = schema = """
bovinos(
    codigo TEXT PRIMARY KEY,               -- (ex: FSC00072)
    nome TEXT,                             -- (ex: Touro05223 / Vaca90993)
    sexo CHAR(1),                          -- 'M' = macho, 'F' = fêmea
    pais_origem TEXT,                      -- (ex: BR)
    data_nascimento DATE,                  
    raca_id TEXT,                          -- Código da raça
    numerorgpai TEXT REFERENCES bovinos(codigo),  -- Código do pai
    numerorgmae TEXT REFERENCES bovinos(codigo)   -- Código da mãe
)

fichalactacao(
    id SERIAL PRIMARY KEY,
    codigo_bovino TEXT REFERENCES bovinos(codigo),  -- codigo do animal
    formacoleta TEXT,
    idademesesparto INTEGER,
    numeroordenhas INTEGER,
    qtdediaslactacao INTEGER,
    qtdeleite305 NUMERIC,
    qtdegordura305 NUMERIC,
    qtdeproteina305 NUMERIC,
    dataencerramento DATE,
    ideventoparto INTEGER REFERENCES ocorrenciaEvento(id),
    ideventoseca INTEGER REFERENCES ocorrenciaEvento(id)
)

ocorrenciaEvento(
    id SERIAL PRIMARY KEY,
    codigo_bovino TEXT REFERENCES bovinos(codigo),  -- Código do bovino
    idbovino INTEGER,                               -- Parte numérica do código
    dataocorrencia DATE,
    facilidade_parto TEXT,
    nro_crias INTEGER,
    qtde_litros NUMERIC,
    sexo_crias CHAR(1),                             -- 'M' ou 'F'
    tipo_evento INTEGER                             -- 1=parto, 2=seca, 3=outros
)

bovinos_genealogia(
    codigo TEXT PRIMARY KEY REFERENCES bovinos(codigo),
    nome TEXT,
    sexo CHAR(1),
    codigo_pai TEXT REFERENCES bovinos(codigo),
    nome_pai TEXT,
    codigo_mae TEXT REFERENCES bovinos(codigo),
    nome_mae TEXT,
    
    codigo_avo_paterno TEXT REFERENCES bovinos(codigo),
    nome_avo_paterno TEXT,
    codigo_avo_paterna TEXT REFERENCES bovinos(codigo),
    nome_avo_paterna TEXT,
    
    codigo_avo_materno TEXT REFERENCES bovinos(codigo),
    nome_avo_materno TEXT,
    codigo_avo_materna TEXT REFERENCES bovinos(codigo),
    nome_avo_materna TEXT,


    codigo_bisavo_paterno_paterno TEXT REFERENCES bovinos(codigo),
    nome_bisavo_paterno_paterno TEXT,
    codigo_bisavo_paterna_paterno TEXT REFERENCES bovinos(codigo),
    nome_bisavo_paterna_paterno TEXT,

    codigo_bisavo_paterno_materno TEXT REFERENCES bovinos(codigo),
    nome_bisavo_paterno_materno TEXT,

    codigo_bisavo_paterna_materna TEXT REFERENCES bovinos(codigo),
    nome_bisavo_paterna_materna TEXT,

    codigo_bisavo_materno_paterno TEXT REFERENCES bovinos(codigo),
    nome_bisavo_materno_paterno TEXT,

    codigo_bisavo_materna_paterno TEXT REFERENCES bovinos(codigo),
    nome_bisavo_materna_paterno TEXT,

    codigo_bisavo_materno_materno TEXT REFERENCES bovinos(codigo),
    nome_bisavo_materno_materno TEXT,

    codigo_bisavo_materna_materna TEXT REFERENCES bovinos(codigo),
    nome_bisavo_materna_materna TEXT,
)

impacto_producao_genealogico(
    codigo_ancestral TEXT REFERENCES bovinos(codigo),
    nome_ancestral TEXT,
    sexo_ancestral CHAR(1),
    nivel_parentesco INTEGER,       -- 1=filhos, 2=netos, 3=bisnetos
    media_leite NUMERIC,     
    producao_total NUMERIC,  
    qtd_descendentes INTEGER,
    PRIMARY KEY (codigo_ancestral, nivel_parentesco)
)


"""
        self.prompt = f'{self.superior}\nSchema: {schema}\nPergunta: {self.pergunta}'


    def gpt(self):
        print("CHAMANDO GPT! PROMPT= ", self.prompt)
        messages = [
			{"role": "system", "content": self.superior},
			{"role": "user", "content": self.prompt}
		]
        content = _call_openai(messages, temperature=0.0, max_tokens=800)
        sql = _extract_and_sanitize_sql(content)
        return sql

    def gerar_calc_plan_gpt(self, sql_query: str, columns: list[str]) -> list[dict]:
        """
		Pede ao GPT um plano de cálculos (calc_plan) baseado na pergunta, SQL e colunas do resultado.
		Saída: lista de etapas (JSON) com operações whitelist.
		"""
        system_msg = (
			"Você gera um PLANO DE CÁLCULOS determinístico (JSON) para resultados de SQL. "
			"NÃO calcule números; apenas descreva as operações. "
			"A saída deve ser APENAS JSON com a chave 'calc_plan'."
		)

		# operações suportadas — mantenha curto e objetivo
        allowed_ops = (
			"sum|mean|median|min|max|std|var|count|nunique|topk|percentile|ratio|rate_per|cumsum"
		)

        user_prompt = f"""
	Pergunta do usuário (PT-BR):
	{self.pergunta}

	SQL executada:
	{sql_query}

	Colunas disponíveis no resultado (ordem e nomes exatos):
	{columns}

	Gere APENAS JSON no formato:
	{{
	"calc_plan": [
		{{
		"id": "m1",
		"op": "{allowed_ops}",
		"on": "col_ou_lista",
		"by": ["col_agrupamento_opcional"],
		"where": {{"coluna":"valor"}},           // opcional (igualdade)
		"k": 5,                                   // para topk
		"q": 0.9,                                 // para percentile (0..1)
		"numerator": "col", "denominator": "col_ou_constante",
		"per": 1000,                              // para rate_per
		"label": "nome_da_medida"
		}}
	]
	}}

	Regras:
	- Use SOMENTE colunas presentes em {columns}.
	- NÃO invente métricas; descreva o que medir (ex.: média, top-k, p90).
	- O plano deve responder à pergunta, com 1–5 medidas no máximo.
	- NÃO devolva explicações fora do JSON.
	"""

        content = _call_openai(
			messages=[{"role": "system", "content": system_msg},
					{"role": "user", "content": user_prompt}],
			temperature=0.0, max_tokens=800
		)
        payload = _extract_json_block(content)
        plan = payload.get("calc_plan") or []
        
        # sanity: garantir lista
        if not isinstance(plan, list):
            plan = []
        return plan
        

    def traduzir_gpt(self, sql_query, rows):
        """
		Gera uma explicação em PT-BR com base na pergunta original (self.pergunta),
		na SQL executada e nos resultados (rows). Não inventa números.
		"""
        rows_txt = _compact_rows(rows, max_rows=60, max_chars=10000)

        system_msg = (
			"Você é um analista de dados que explica resultados de consultas SQL em PT-BR, "
			"de forma breve, clara e sem inventar números. "
			"Use APENAS os dados fornecidos. Se o resultado estiver vazio, diga isso explicitamente. "
			"Quando útil, mostre contagens e médias simples, mas somente se estiverem no resultado."
		)

        user_prompt = (
			"Pergunta original do usuário:\n"
			f"{self.pergunta}\n\n"
			"SQL executada (contexto):\n"
			f"{sql_query}\n\n"
			"Resultados (JSON, possivelmente truncado):\n"
			f"{rows_txt}\n\n"
			"Tarefa: Explique o que os dados respondem sobre a pergunta, em 1–3 parágrafos curtos "
			"ou uma lista objetiva. Não invente valores que não estejam no resultado. "
			"Se houver colunas-chave, cite-as nominalmente. Se o conjunto estiver vazio, diga que não há registros compatíveis."
		)

        content = _call_openai(
			messages=[{"role": "system", "content": system_msg},
					{"role": "user", "content": user_prompt}],
			temperature=0.0,
			max_tokens=600
		)
        return content


    def local_llhama(self):
        # print(self.prompt)
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "mistral:instruct", "prompt": self.prompt, "stream": False,
                    "options": {
                    "temperature": 0.0,
                    "num_ctx": 5700,
                    "num_thread": 11, # numero de threads pra usar 
                    "top_p": 0.7
                }
            }
        )
        print(f"RESP = {resp.json()}")
        resposta = resp.json()["response"].strip()
        match = re.search(r"<SQL>(.*?)</SQL>", resposta, re.DOTALL)

        sql_query = match.group(1).strip() if match else resposta
        sql_query = re.sub(r'--.*?\n', '', sql_query)  # remove comentários
        sql_query = re.sub(r'/\*.*?\*/', '', sql_query, flags=re.DOTALL)
        sql_query = sql_query.strip()
        
        sql_query = sql_query.replace('```','')
        sql_query = sql_query.replace('sql','')

        return sql_query

    def traduzir_llama(self, sql_query, rows):
        prompt = f"Sabendo que a query SQL usada para acessar o Banco de Dados foi {sql_query} \n e os resultados foram \n {rows} \n crie uma resposta para a seguinte pergunta: {self.pergunta}"

        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "mistral:instruct", "prompt": self.prompt, "stream": False,
                    "options": {
                    "temperature": 0.0,
                    "num_ctx": 5700,
                    "num_thread": 11, # numero de threads pra usar 
                    "top_p": 0.7
                }
            }
        )
        resposta = resp.json()["response"].strip()

        return resposta


    def gerar_calc_plan_llama(self, sql_query: str, columns: list[str]) -> list[dict]:
        """
		Pede ao mixtral um plano de cálculos (calc_plan) baseado na pergunta, SQL e colunas do resultado.
		Saída: lista de etapas (JSON) com operações whitelist.
		"""
        system_msg = (
			"Você gera um PLANO DE CÁLCULOS determinístico (JSON) para resultados de SQL. "
			"NÃO calcule números; apenas descreva as operações. "
			"A saída deve ser APENAS JSON com a chave 'calc_plan'."
		)

		# operações suportadas — mantenha curto e objetivo
        allowed_ops = (
			"sum|mean|median|min|max|std|var|count|nunique|topk|percentile|ratio|rate_per|cumsum"
		)

        user_prompt = f"""
	Pergunta do usuário (PT-BR):
	{self.pergunta}

	SQL executada:
	{sql_query}

	Colunas disponíveis no resultado (ordem e nomes exatos):
	{columns}

	Gere APENAS JSON no formato:
	{{
	"calc_plan": [
		{{
		"id": "m1",
		"op": "{allowed_ops}",
		"on": "col_ou_lista",
		"by": ["col_agrupamento_opcional"],
		"where": {{"coluna":"valor"}},           // opcional (igualdade)
		"k": 5,                                   // para topk
		"q": 0.9,                                 // para percentile (0..1)
		"numerator": "col", "denominator": "col_ou_constante",
		"per": 1000,                              // para rate_per
		"label": "nome_da_medida"
		}}
	]
	}}

	Regras:
	- Use SOMENTE colunas presentes em {columns}.
	- NÃO invente métricas; descreva o que medir (ex.: média, top-k, p90).
	- O plano deve responder à pergunta, com 1–5 medidas no máximo.
	- NÃO devolva explicações fora do JSON.
	"""

        content = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "mistral:instruct", "prompt": self.prompt, "stream": False,
                    "options": {
                    "temperature": 0.0,
                    "num_ctx": 5700,
                    "num_thread": 11, # numero de threads pra usar 
                    "top_p": 0.7
                }
            }
        )
        
        payload = _extract_json_block(content)
        plan = payload.get("calc_plan") or []
        
        # sanity: garantir lista
        if not isinstance(plan, list):
            plan = []
        return plan