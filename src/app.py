import streamlit as st
import llm
import psycopg2
import pandas as pd
from operations import apply_plan
from time import time



privada = True


conn = psycopg2.connect(
    dbname="hackathon-rerum-2025",
    user="postgres",
    password="pablo",
    host="localhost"
)

cur = conn.cursor()


st.set_page_config(page_title="Bull Querier", page_icon="🐄")
st.title("Bull Querier 🐄")


if pergunta := st.chat_input("Faça sua pergunta!"):
    st.write(f'**Pergunta:** {pergunta}')
    
    chamada = llm.Chamar(pergunta)

    # ----- IMPORTANTE
    i = time()

    if privada:
        sql = chamada.local_llhama()
    else:
        sql = chamada.gpt()
    i2 = time()
    print(f'tempo: {i2 - i}')

    st.write("**SQL usado:**")
    st.code(f"{sql}", language="sql")
    
    resultado = None
    try:
        cur.execute(sql)
        colunas = [desc[0] for desc in cur.description]  # nomes das colunas retornadas
        rows = cur.fetchall()

        # Converte o retorno em lista de dicionários legíveis
        resultado = [dict(zip(colunas, row)) for row in rows]
        print("Resultado:", resultado)
        
        df = pd.DataFrame(resultado) if resultado else pd.DataFrame()
        try:
            if privada:
                calc_plan = chamada.gerar_calc_plan_llama(sql_query=sql, columns=list(df.columns))
            else:
                calc_plan = chamada.gerar_calc_plan_gpt(sql_query=sql, columns=list(df.columns))
        except Exception as e:
            st.warning(f"Não foi possível gerar calc_plan automaticamente. Erro: {e}")
            calc_plan = []

        st.write("### Plano de Cálculo (calc_plan)")
        st.json(calc_plan if calc_plan else {"info": "calc_plan vazio"})

        calc_results = {}
        if not df.empty and calc_plan:
            try:
                calc_results = apply_plan(df, calc_plan)
            except Exception as e:
                st.error(f"Erro ao executar calc_plan: {e}")
        else:
            st.info("Sem dados ou sem calc_plan para executar.")

        # Mostrar resultados do plano
        st.write("### Resultados do Plano (calc_results)")
        st.json(calc_results if calc_results else {"info": "sem resultados"})
        pacote_resultado = {"calc_results": calc_results, "preview_rows": resultado[:30]}

        # ---- IMPORTANTE
        if privada:
            resultado = chamada.traduzir_llama(sql, pacote_resultado)
        else:
            resultado = chamada.traduzir_gpt(sql, pacote_resultado)


    except Exception as e:
        st.write(f"Errei algo durante a execução da consulta! Talvez perguntar novamente resolva o problema")
        print("Erro na execução:", e)

    st.write(f"**Resultado:** {resultado if resultado else 'Sem resultado devido a erro na consulta. Tente de novo.'}")
    print(f'tempo: {time() - i}')
    conn.close()
