# Nota pra mim mesmo: Precisa ser executado a partir do diretorio do script. nada de executar python bd/populador.py. Deve ser `cd bd; python populador.py`

import psycopg2
import pandas as pd
import numpy as np


conn = psycopg2.connect(
    host="localhost",
    dbname="hackathon-rerum-2025",
    user="postgres",
    password="pablo"
)
cur = conn.cursor()

# cur.execute("SET search_path TO hackathon;")
# conn.commit()


bovinos_file = "xlsx/bovinos.xlsx"
fichalactacao_file = "xlsx/fichalactacao.xlsx"
ocorrencia_file = "xlsx/ocorrenciaEvento.xlsx"

df_bovinos = pd.read_excel(bovinos_file)
df_ficha = pd.read_excel(fichalactacao_file)
df_eventos = pd.read_excel(ocorrencia_file)

## CONSERTANDO ALGUNS DADOS!

df_bovinos["pais_origem"] = (
    df_bovinos["pais_origem"].astype(str).str.strip().replace({
        "NULL":None, "": None, "nan": None, "NaN": None, "NAN": None, np.nan: None, pd.NA: None, "None": None
    })
)
df_bovinos["numerorgpai"] = (
    df_bovinos["numerorgpai"].astype(str).str.strip().replace({
        "NULL":None, "": None, "nan": None, "NaN": None, "NAN": None, np.nan: None, pd.NA: None, "None": None
    })
)
df_bovinos["numerorgmae"] = (
    df_bovinos["numerorgmae"].astype(str).str.strip().replace({
        "NULL":None, "": None, "nan": None, "NaN": None, "NAN": None, np.nan: None, pd.NA: None, "None": None
    })
)


df_ficha["formacoleta"] = (
    df_ficha["formacoleta"].astype(str).str.strip().replace({
        "NULL":None, "": None, "nan": None, "NaN": None, "NAN": None, np.nan: None, pd.NA: None, "None": None
    })
)


# isso vai ser útil la na frente pq ta rolando vários erros nesse tipo de dado
df_eventos["idbovino"] = pd.to_numeric(df_eventos["idbovino"], errors="coerce").astype("Int64")
df_eventos["nro_crias"] = pd.to_numeric(df_eventos["nro_crias"], errors="coerce").astype("Int64")
df_eventos["tipo_evento"] = pd.to_numeric(df_eventos["tipo_evento"], errors="coerce").astype("Int64")
df_eventos = df_eventos.where(pd.notna(df_eventos), None)
df_eventos = df_eventos.replace({pd.NA: None, np.nan: None})
df_eventos = df_eventos.replace('nan', None)

df_eventos["sexo_crias"] = (
    df_eventos["sexo_crias"]
    .astype(str)
    .str.strip()
    .replace({
        "MACHO": "M", "Macho": "M", "macho": "M",
        "FÊMEA": "F", "FEMEA": "F", "Fêmea": "F", "fêmea": "F",
        "Femea": "F", "femea": "F",
        "0": None, "":None, "None":None, "nan":None, "NaN":None, "NAN":None, "NULL": None
    })
)

df_eventos.loc[~df_eventos["sexo_crias"].isin(["M", "F"]), "sexo_crias"] = None

df_eventos["nro_crias"] = (
    df_eventos["nro_crias"].astype(str).str.strip().replace({
        "NULL":0, "": 0, "nan": 0, "NaN": 0, "NAN": 0, np.nan: 0, pd.NA: 0, "None": 0
    })
)

df_eventos["qtde_litros"] = (
    df_eventos["qtde_litros"].astype(str).str.strip().replace({
        "NULL":0, "": 0, "nan": 0, "NaN": 0, "NAN": 0, np.nan: 0, pd.NA: 0, None: 0, "None": 0
    })
)

df_eventos["facilidade_parto"] = (
    df_eventos["facilidade_parto"].astype(str).str.strip().replace({
        "nan": None, "NaN": None, "NAN": None, "": None, "0": None, np.nan: None, pd.NA: None, "None": None
    })
)




df_bovinos.drop_duplicates(inplace=True)

num_cols_ficha = ["qtdeleite305", "qtdegordura305", "qtdeproteina305"]
for col in num_cols_ficha:
    df_ficha[col] = (
        df_ficha[col].astype(str).str.replace(",", ".", regex=False).replace("nan", None).astype(float)
    )

df_eventos["qtde_litros"] = (
    df_eventos["qtde_litros"].replace({pd.NA: np.nan, "nan": np.nan, "None": np.nan}).astype(str).str.replace(",", ".", regex=False)
)
df_eventos["qtde_litros"] = pd.to_numeric(df_eventos["qtde_litros"], errors="coerce")

for col in ["codigo", "numerorgpai", "numerorgmae"]:
    df_bovinos[col] = df_bovinos[col].astype(str).str.strip()

for col in ["codigo_bovino"]:
    df_ficha[col] = df_ficha[col].astype(str).str.strip()
    df_eventos[col] = df_eventos[col].astype(str).str.strip()



print("bovinos")
for _, row in df_bovinos.iterrows():
    cur.execute("""
        INSERT INTO bovinos (codigo, nome, sexo, pais_origem, data_nascimento, raca_id, numerorgpai, numerorgmae)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (codigo) DO NOTHING;
    """, (
        row["codigo"], row["nome"], row["sexo"],
        row["pais_origem"], row["data_nascimento"],
        row["raca_id"], row["numerorgpai"], row["numerorgmae"]
    ))

conn.commit()

print("fichalactacao")
cur.execute("SELECT codigo FROM bovinos;")
codigos_validos = {c[0] for c in cur.fetchall()}

for _, row in df_ficha.iterrows():
    if row["codigo_bovino"] not in codigos_validos:
        continue

    cur.execute("""
        INSERT INTO fichalactacao (
            codigo_bovino, formacoleta, idademesesparto,
            numeroordenhas, qtdediaslactacao,
            qtdeleite305, qtdegordura305, qtdeproteina305,
            dataencerramento, ideventoparto, ideventoseca
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
    """, (
        row["codigo_bovino"], row["formacoleta"], row["idademesesparto"],
        row["numeroordenhas"], row["qtdediaslactacao"],
        row["qtdeleite305"], row["qtdegordura305"], row["qtdeproteina305"],
        row["dataencerramento"], row["ideventoparto"], row["ideventoseca"]
    ))

conn.commit()


print("ocorrenciaEvento")
for _, row in df_eventos.iterrows():
    if row["codigo_bovino"] not in codigos_validos:
        continue
    try:
        cur.execute("""
            INSERT INTO ocorrenciaEvento (
                idbovino, codigo_bovino, dataocorrencia,
                facilidade_parto, nro_crias,
                qtde_litros, sexo_crias, tipo_evento
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);
        """, (
            row["idbovino"], row["codigo_bovino"], row["dataocorrencia"],
            row["facilidade_parto"], row["nro_crias"],
            row["qtde_litros"], row["sexo_crias"], row["tipo_evento"]
        ))
    except Exception as e:
        print(f'''row["idbovino"] = {row["idbovino"]}
        row["codigo_bovino"] = {row["codigo_bovino"]}
        row["dataocorrencia"] = {row["dataocorrencia"]}
        row["facilidade_parto"] = {row["facilidade_parto"]}
        row["nro_crias"] = {row["nro_crias"]}
        row["qtde_litros"] = {row["qtde_litros"]}
        row["sexo_crias"] = {row["sexo_crias"]}
        row["tipo_evento"] = {row["tipo_evento"]}''')
        print(e)
        quit()

conn.commit()



print("bovinos_genealogia")
cur.execute("TRUNCATE TABLE bovinos_genealogia;")


cur.execute("""
INSERT INTO bovinos_genealogia (
    codigo, nome, sexo,
    codigo_pai, nome_pai, codigo_mae, nome_mae,
    codigo_avo_paterno, nome_avo_paterno,
    codigo_avo_paterna, nome_avo_paterna,
    codigo_avo_materno, nome_avo_materno,
    codigo_avo_materna, nome_avo_materna
)
SELECT 
    f.codigo, f.nome, f.sexo,
    f.numerorgpai AS codigo_pai, p.nome AS nome_pai,
    f.numerorgmae AS codigo_mae, m.nome AS nome_mae,
    p.numerorgpai AS codigo_avo_paterno, pp.nome AS nome_avo_paterno,
    p.numerorgmae AS codigo_avo_paterna, pm.nome AS nome_avo_paterna,
    m.numerorgpai AS codigo_avo_materno, mp.nome AS nome_avo_materno,
    m.numerorgmae AS codigo_avo_materna, mm.nome AS nome_avo_materna
FROM bovinos f
LEFT JOIN bovinos p  ON f.numerorgpai = p.codigo
LEFT JOIN bovinos m  ON f.numerorgmae = m.codigo
LEFT JOIN bovinos pp ON p.numerorgpai = pp.codigo
LEFT JOIN bovinos pm ON p.numerorgmae = pm.codigo
LEFT JOIN bovinos mp ON m.numerorgpai = mp.codigo
LEFT JOIN bovinos mm ON m.numerorgmae = mm.codigo;
""")

conn.commit()

print("impacto_producao_genealogico")

cur.execute("TRUNCATE TABLE impacto_producao_genealogico;")


cur.execute("""
INSERT INTO impacto_producao_genealogico (
    codigo_ancestral, nome_ancestral, sexo_ancestral,
    nivel_parentesco, media_leite, producao_total, qtd_descendentes
)
SELECT
    g.codigo_pai AS codigo_ancestral,
    p.nome AS nome_ancestral,
    p.sexo AS sexo_ancestral,
    1 AS nivel_parentesco,
    AVG(f.qtdeleite305) AS media_leite,
    SUM(f.qtdeleite305) AS producao_total,
    COUNT(DISTINCT f.codigo_bovino) AS qtd_descendentes
FROM bovinos_genealogia g
JOIN bovinos p ON p.codigo = g.codigo_pai
JOIN fichalactacao f ON f.codigo_bovino = g.codigo
WHERE g.codigo_pai IS NOT NULL
GROUP BY g.codigo_pai, p.nome, p.sexo

UNION ALL

SELECT
    g.codigo_avo_paterno AS codigo_ancestral,
    av.nome AS nome_ancestral,
    av.sexo AS sexo_ancestral,
    2 AS nivel_parentesco,
    AVG(f.qtdeleite305),
    SUM(f.qtdeleite305),
    COUNT(DISTINCT f.codigo_bovino)
FROM bovinos_genealogia g
JOIN bovinos av ON av.codigo = g.codigo_avo_paterno
JOIN fichalactacao f ON f.codigo_bovino = g.codigo
WHERE g.codigo_avo_paterno IS NOT NULL
GROUP BY g.codigo_avo_paterno, av.nome, av.sexo;
""")

conn.commit()



print("concluída com sucesso")
cur.close()
conn.close()
