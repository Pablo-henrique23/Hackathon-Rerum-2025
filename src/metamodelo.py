metamodelo = {
    "bovinos": {
        "descricao": "Tabela base com informações de identificação e filiação de cada animal da raça leiteira.",
        "campos": {
            "codigo": "Identificação única do animal (ex: FSC292177)",
            "nome": "Nome do animal (ex: Vaca292177)",
            "sexo": "Sexo do animal, M = macho, F = fêmea",
            "pais_origem": "País de origem do animal (ex: BR)",
            "data_nascimento": "Data de nascimento",
            "raca_id": "Identificador da raça (ex: Raça 01)",
            "numerorgpai": "Código de registro do pai",
            "numerorgmae": "Código de registro da mãe"
        }
    },

    "fichalactacao": {
        "descricao": "Registros de lactação de cada animal, contendo volume, gordura e proteína produzidos em cada ciclo produtivo.",
        "campos": {
            "codigo_bovino": "Código do animal (chave estrangeira para bovinos.codigo)",
            "formacoleta": "Forma de coleta do leite (ex: ordenhadeira, manual)",
            "idademesesparto": "Idade em meses no momento do parto",
            "numeroordenhas": "Número de ordenhas por dia",
            "qtdediaslactacao": "Número total de dias de lactação",
            "qtdeleite305": "Quantidade de leite produzida em 305 dias (padrão de comparação)",
            "qtdegordura305": "Quantidade de gordura produzida em 305 dias",
            "qtdeproteina305": "Quantidade de proteína produzida em 305 dias",
            "dataencerramento": "Data de encerramento da lactação",
            "ideventoparto": "Identificador do evento de parto associado",
            "ideventoseca": "Identificador do evento de seca associado"
        }
    },

    "ocorrenciaEvento": {
        "descricao": "Eventos biológicos e produtivos associados a cada bovino, como partos, secas e outras ocorrências relevantes.",
        "campos": {
            "idbovino": "Identificador numérico interno do bovino",
            "codigo_bovino": "Código do animal (chave estrangeira para bovinos.codigo)",
            "dataocorrencia": "Data do evento registrado",
            "facilidade_parto": "Descrição do parto (sem auxílio, difícil, tração etc.)",
            "nro_crias": "Número de crias geradas no evento",
            "qtde_litros": "Volume de leite produzido no evento (se aplicável)",
            "sexo_crias": "Sexo das crias (M ou F)",
            "tipo_evento": "Tipo do evento (1 = parto, 2 = seca, 3 = inseminação, etc.)"
        }
    },

    "bovinos_genealogia": {
        "descricao": "Tabela redundante que armazena a árvore genealógica completa até a 3ª geração (pais, avós e bisavós), para consultas rápidas.",
        "campos": {
            "codigo": "Código do animal",
            "nome": "Nome do animal",
            "sexo": "Sexo do animal",
            "codigo_pai": "Código do pai",
            "nome_pai": "Nome do pai",
            "codigo_mae": "Código da mãe",
            "nome_mae": "Nome da mãe",
            "codigo_avo_paterno": "Código do pai do pai",
            "nome_avo_paterno": "Nome do pai do pai",
            "codigo_avo_paterna": "Código da mãe do pai",
            "nome_avo_paterna": "Nome da mãe do pai",
            "codigo_avo_materno": "Código do pai da mãe",
            "nome_avo_materno": "Nome do pai da mãe",
            "codigo_avo_materna": "Código da mãe da mãe",
            "nome_avo_materna": "Nome da mãe da mãe",
            "codigo_bisavo_paterno_paterno": "Código do pai do avô paterno",
            "nome_bisavo_paterno_paterno": "Nome do pai do avô paterno",
            "codigo_bisavo_paterna_paterno": "Código da mãe do avô paterno",
            "nome_bisavo_paterna_paterno": "Nome da mãe do avô paterno",
            "codigo_bisavo_paterno_materno": "Código do pai da avó paterna",
            "nome_bisavo_paterno_materno": "Nome do pai da avó paterna",
            "codigo_bisavo_paterna_materna": "Código da mãe da avó paterna",
            "nome_bisavo_paterna_materna": "Nome da mãe da avó paterna",
            "codigo_bisavo_materno_paterno": "Código do pai do avô materno",
            "nome_bisavo_materno_paterno": "Nome do pai do avô materno",
            "codigo_bisavo_materna_paterno": "Código da mãe do avô materno",
            "nome_bisavo_materna_paterno": "Nome da mãe do avô materno",
            "codigo_bisavo_materno_materno": "Código do pai da avó materna",
            "nome_bisavo_materno_materno": "Nome do pai da avó materna",
            "codigo_bisavo_materna_materna": "Código da mãe da avó materna",
            "nome_bisavo_materna_materna": "Nome da mãe da avó materna"
        }
    },

    "impacto_producao_genealogico": {
        "descricao": "Tabela derivada que consolida médias e totais de produção de leite dos descendentes de cada ancestral até a 3ª geração.",
        "campos": {
            "codigo_ancestral": "Código do animal ancestral (pai, avô, bisavô)",
            "nome_ancestral": "Nome do ancestral",
            "sexo_ancestral": "Sexo do ancestral (M ou F)",
            "nivel_parentesco": "Nível de parentesco: 1 = filhos, 2 = netos, 3 = bisnetos",
            "media_leite": "Média de produção de leite dos descendentes desse ancestral",
            "producao_total": "Soma total da produção dos descendentes",
            "qtd_descendentes": "Número total de descendentes considerados na média"
        }
    },
    "vw_genealogia_completa": {
        "descricao": "View que reúne toda a genealogia de cada animal até a 3ª geração, com nomes legíveis para pais, avós e bisavós.",
        "origem": "bovinos_genealogia"
    },

    "media_filhas_por_touro": {
        "descricao": "View que calcula a média de produção de leite das filhas de cada touro, permitindo avaliar desempenho genético masculino.",
        "origem": "bovinos JOIN fichalactacao"
    },

    "producao_vitalicia": {
        "descricao": "View que consolida a produção vitalícia total e média de cada vaca ao longo de todas as lactações registradas.",
        "origem": "bovinos JOIN fichalactacao"
    },

    "vw_eventos_completos": {
        "descricao": "View que integra dados de eventos (partos, secas, etc.) com métricas de produção e lactação do animal.",
        "origem": "ocorrenciaEvento JOIN bovinos JOIN fichalactacao"
    },

    "vw_producao_por_bovino": {
        "descricao": "View que agrega, para cada bovino, a produção total, média e composição (gordura, proteína) das lactações.",
        "origem": "bovinos JOIN fichalactacao"
    },

    "vw_producao_por_descendencia": {
        "descricao": "View que mostra o impacto produtivo de cada ancestral em diferentes níveis de descendência (1 a 3 gerações).",
        "origem": "impacto_producao_genealogico JOIN bovinos"
    },

    "vw_impacto_produtivo": {
        "descricao": "View que detalha o impacto produtivo de cada animal, categorizado por tipo de descendência (filhos, netos, bisnetos).",
        "origem": "impacto_producao_genealogico JOIN bovinos"
    },

    "serie_historica_lactacao": {
        "descricao": "View que apresenta a produção anual de leite de cada vaca, permitindo análises temporais e séries históricas.",
        "origem": "bovinos JOIN fichalactacao"
    },

    "impacto_producao_completo": {
        "descricao": "View que consolida médias e totais de produção herdada até a 3ª geração de descendência, combinando genealogia e lactações.",
        "origem": "bovinos_genealogia JOIN fichalactacao"
    },

    "resumo_genealogico_produtivo": {
        "descricao": "View unificada que combina informações genealógicas com métricas produtivas médias, facilitando consultas por IA.",
        "origem": "bovinos_genealogia JOIN impacto_producao_genealogico"
    }
}
