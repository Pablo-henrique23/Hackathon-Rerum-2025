import requests
import psycopg2
import re
from llama_cpp import Llama
import atexit


with open("database_schema/database_to_json_small.json", "r", encoding="utf-8") as f:
    banco_json = json.load(f)


conn = psycopg2.connect(
    dbname="hackathon",
    user="luiza",
    password="senha",
    host="localhost",
    port="5432"
)
cur = conn.cursor()


llm = Llama(model_path="./models/llama-7b.Q8_0.gguf", n_ctx=2048)


def gerar_sql_inteligente(pergunta):
    """Gera SQL baseada no seu schema específico"""
    
    # Extrai informações do seu JSON
    tabelas_info = []
    for tabela in banco_json["tabelas"]:
        colunas_principais = tabela["colunas"][:4]  # Pega as 4 primeiras colunas
        tabelas_info.append(f"- {tabela['nome']}({', '.join(colunas_principais)})")
    
    schema_info = "\n".join(tabelas_info)
    
    prompt = f"""
SCHEMA DO BANCO:
{schema_info}

PERGUNTA: "{pergunta}"

BASEADO NO SCHEMA ACIMA, gere uma consulta SQL válida que responda à pergunta.

REGRAS:
- Para produção de leite: JOIN bovinos.codigo = fichalactacao.codigo_bovino
- Para eventos: JOIN bovinos.codigo = ocorrenciaevento.codigo_bovino
- Sempre use alias para as tabelas (ex: SELECT b.nome FROM bovinos b).


EXEMPLOS DE CONSULTAS VÁLIDAS:
• "Vacas com mais leite" → SELECT b.nome, f.qtdeleite305 FROM bovinos b JOIN fichalactacao f ON b.codigo = f.codigo_bovino WHERE b.sexo = 'F' ORDER BY f.qtdeleite305 DESC LIMIT 5;
• "Quais os últimos partos?" → SELECT b.nome, o.dataocorrencia FROM bovinos b JOIN ocorrenciaevento o ON b.codigo = o.codigo_bovino WHERE o.tipo_evento = 'parto' ORDER BY o.dataocorrencia DESC LIMIT 10;
• "Contar quantos bovinos são machos" → SELECT COUNT(*) FROM bovinos WHERE sexo = 'M';
• "Bovinos nascidos em 2023" → SELECT nome, data_nascimento FROM bovinos WHERE data_nascimento BETWEEN '2023-01-01' AND '2023-12-31';

SQL PARA "{pergunta}":
"""
    
    resposta = llm(prompt, max_tokens=250)
    sql_bruta = resposta['choices'][0]['text'].strip()
    
    print(f"SQL bruta gerada: {repr(sql_bruta)}")
    
    # Limpeza inteligente
    sql_limpa = limpar_e_validar_sql(sql_bruta, pergunta)
    
    return sql_limpa

def limpar_e_validar_sql(sql_bruta, pergunta):

    
    # Remove tudo antes do SELECT
    sql = sql_bruta
    if 'SELECT' in sql.upper():
        pos = sql.upper().index('SELECT')
        sql = sql[pos:]
    
    # Remove caracteres inválidos no início
    sql = re.sub(r'^[^A-Za-z]*', '', sql)
    
    # Pega apenas até o primeiro ponto e vírgula
    sql = sql.split(';')[0].strip()
    
    
    # Aplica correções baseadas na pergunta
    sql = aplicar_correcoes_contextuais(sql, pergunta)
    

    # Garante ponto e vírgula
    sql += ';'
    
    return sql

def aplicar_correcoes_contextuais(sql, pergunta):
    """Aplica correções baseadas no contexto da pergunta"""
    sql_lower = sql.lower()
    pergunta_lower = pergunta.lower()
    
    # CORREÇÃO 1: Produção de leite
    if any(palavra in pergunta_lower for palavra in ['leite', 'produ', 'lactacao', 'litros']):
        # Se não tem JOIN, mas menciona as duas tabelas, adiciona
        if 'join' not in sql_lower and 'bovinos' in sql_lower and 'fichalactacao' in sql_lower:
            print("INFO: Adicionando JOIN para produção de leite")
            # Substitui 'FROM bovinos' por um JOIN completo
            # Usamos uma expressão regular mais robusta para pegar 'bovinos' e seu alias
            sql = re.sub(
                r'FROM\s+bovinos(\s+as)?\s+([bB])\b', 
                'FROM bovinos b JOIN fichalactacao f ON b.codigo = f.codigo_bovino', 
                sql, 
                flags=re.IGNORECASE
            )
        
        # CORREÇÃO DE SEXO REFINADA:
        # Só adiciona filtro de sexo se a pergunta pede "vaca(s)"
        # E o SQL ainda não tem filtro de sexo
        if any(vaca in pergunta_lower for vaca in ['vaca', 'vacas']) and 'sexo' not in sql_lower:
            print("INFO: Adicionando filtro b.sexo = 'F' para 'vacas'")
            if 'where' in sql_lower:
                # Substitui 'WHERE' por 'WHERE b.sexo = 'F' AND' (só na primeira ocorrência)
                sql = re.sub(r'WHERE', "WHERE b.sexo = 'F' AND", sql, flags=re.IGNORECASE, count=1)
            elif 'join' in sql_lower: # Garante que só adiciona WHERE se já houver tabelas
                # Adiciona WHERE antes de GROUP BY, ORDER BY, etc.
                if re.search(r'\s(GROUP|ORDER|LIMIT)\b', sql, re.IGNORECASE):
                     sql = re.sub(r'(\s(GROUP|ORDER|LIMIT)\b)', r" WHERE b.sexo = 'F'\1", sql, flags=re.IGNORECASE, count=1)
                else:
                     sql += " WHERE b.sexo = 'F'"
    
    # CORREÇÃO 2: Eventos/partos
    elif any(palavra in pergunta_lower for palavra in ['parto', 'evento', 'nascimento', 'ocorrencia']):
        # Se não tem JOIN, adiciona
        if 'join' not in sql_lower and 'bovinos' in sql_lower and 'ocorrenciaevento' in sql_lower:
            print("INFO: Adicionando JOIN para eventos")
            sql = re.sub(
                r'FROM\s+bovinos(\s+as)?\s+([bB])\b', 
                'FROM bovinos b JOIN ocorrenciaevento o ON b.codigo = o.codigo_bovino', 
                sql, 
                flags=re.IGNORECASE
            )
        
        # Se não filtra por tipo de evento E a pergunta pede "parto"
        if 'tipo_evento' not in sql_lower and 'parto' in pergunta_lower:
            print("INFO: Adicionando filtro o.tipo_evento = 'parto'")
            if 'where' in sql_lower:
                sql = re.sub(r'WHERE', "WHERE o.tipo_evento = 'parto' AND", sql, flags=re.IGNORECASE, count=1)
            elif 'join' in sql_lower:
                if re.search(r'\s(GROUP|ORDER|LIMIT)\b', sql, re.IGNORECASE):
                     sql = re.sub(r'(\s(GROUP|ORDER|LIMIT)\b)', r" WHERE o.tipo_evento = 'parto'\1", sql, flags=re.IGNORECASE, count=1)
                else:
                     sql += " WHERE o.tipo_evento = 'parto'"
    
    # CORREÇÃO 3: Ordenação para "mais", "melhores", "últimos", "velhos"
    if any(palavra in pergunta_lower for palavra in ['mais', 'melhor', 'maior', 'último', 'recente', 'velho']):
        if 'order' not in sql_lower:
            print("INFO: Adicionando ORDER BY com base na pergunta")
            if 'qtdeleite305' in sql_lower:
                sql += " ORDER BY f.qtdeleite305 DESC"
            elif 'dataocorrencia' in sql_lower:
                sql += " ORDER BY o.dataocorrencia DESC"
            elif 'data_nascimento' in sql_lower:
                # "mais velho" = ASC, "mais novo/recente" = DESC
                if 'velho' in pergunta_lower:
                    sql += " ORDER BY data_nascimento ASC"
                else:
                    sql += " ORDER BY data_nascimento DESC"
            
            # Adiciona LIMIT se a pergunta sugere um ranking
            if 'limit' not in sql_lower:
                 # Tenta pegar um número da pergunta
                 match = re.search(r'\b(3|5|10)\b', pergunta)
                 if match:
                     sql += f" LIMIT {match.group(1)}"
                 else:
                     sql += " LIMIT 5" # Um padrão razoável
    
    return sql


def executar_sql(sql):
    try:
        cursor.execute(sql)
        colunas = [desc[0] for desc in cursor.description]
        linhas = cursor.fetchall()
        resultado = [dict(zip(colunas, row)) for row in linhas]
        return resultado
    except Exception as e:
        return f" Erro ao executar SQL: {e}"


def perguntar_ao_banco(pergunta_usuario):
    print(f"\nPERGUNTA: {pergunta_usuario}")
    
    sql = gerar_sql_inteligente(pergunta_usuario)
    print(f"SQL FINAL: {sql}")
    
    resultado = executar_sql(sql)
    return resultado, sql

if __name__ == "__main__":
    perguntas_teste = [
        "Mostre todos os bovinos", # Teste Simples
        "Quais são os 5 bovinos mais velhos?", # Teste ORDER BY ASC e LIMIT
        "Quantos bovinos fêmeas temos?", # Teste COUNT e WHERE
        # "Quais são os últimos 3 partos registrados?", # Teste JOIN ocorrenciaevento, ORDER BY DESC, LIMIT
        # "Qual a média de produção de leite das vacas?", # Teste AVG, JOIN fichalactacao, e filtro 'vacas'
        # "Liste todos os eventos do bovino 'MIMOSA'", # Teste JOIN e WHERE por nome
        # "Encontre bovinos nascidos depois de 2023-01-01", # Teste WHERE com data
        # "Qual a produção de leite total (soma) do rebanho?", # Teste SUM (sem filtro de sexo)
    ]
    
    for pergunta in perguntas_teste:
        print("\n" + "="*70)
        resultado, sql = perguntar_ao_banco(pergunta)
        print(f"RESULTADO: {resultado}")
        print("="*70)


def fechar_conexao():
    cursor.close()
    conn.close()

atexit.register(fechar_conexao)
