-- CREATE SCHEMA IF NOT EXISTS hackathon;
-- SET search_path TO hackathon;


-- ============================================================
CREATE TABLE bovinos (
    codigo TEXT PRIMARY KEY,                  -- Ex: 'FSC292177'
    nome TEXT NOT NULL,                       -- Ex: 'Vaca292177'
    sexo CHAR(1) CHECK (sexo IN ('M', 'F')),  -- Sexo do animal
    pais_origem TEXT,                         -- Ex: 'BR'
    data_nascimento DATE,                     -- Ex: '2018-03-17'
    raca_id TEXT,                             -- Ex: 'Raça 01'
    numerorgpai TEXT,                         -- Código do pai (Ex: 'FSC01153')
    numerorgmae TEXT                          -- Código da mãe (Ex: 'FSC105717')
);

CREATE INDEX idx_bovinos_pai ON bovinos(numerorgpai);
CREATE INDEX idx_bovinos_mae ON bovinos(numerorgmae);


-- ============================================================
CREATE TABLE fichalactacao (
    id SERIAL PRIMARY KEY,
    codigo_bovino TEXT NOT NULL REFERENCES bovinos(codigo) ON DELETE CASCADE,
    formacoleta TEXT, -- 'ordenhadeira'
    idademesesparto INTEGER, -- idade parto em meses
    numeroordenhas INTEGER, -- n° de ordenhas
    qtdediaslactacao INTEGER,
    qtdeleite305 NUMERIC(18,10),
    qtdegordura305 NUMERIC(18,10),
    qtdeproteina305 NUMERIC(18,10),
    dataencerramento DATE,
    ideventoparto INTEGER,
    ideventoseca INTEGER
);

CREATE INDEX idx_fichalactacao_codigo ON fichalactacao(codigo_bovino);
CREATE INDEX idx_fichalactacao_data ON fichalactacao(dataencerramento);


-- ============================================================
CREATE TABLE ocorrenciaEvento (
    id SERIAL PRIMARY KEY,
    idbovino INTEGER,
    codigo_bovino TEXT NOT NULL REFERENCES bovinos(codigo) ON DELETE CASCADE,
    dataocorrencia DATE,
    facilidade_parto TEXT,
    nro_crias INTEGER,
    qtde_litros NUMERIC(18,10),
    sexo_crias CHAR(1),
    tipo_evento INTEGER
);

CREATE INDEX idx_ocorrenciaEvento_codigo ON ocorrenciaEvento(codigo_bovino);
CREATE INDEX idx_ocorrenciaEvento_data ON ocorrenciaEvento(dataocorrencia);


-- ============================================================
CREATE TABLE bovinos_genealogia (
    codigo TEXT PRIMARY KEY,             -- Código do animal
    nome TEXT,
    sexo CHAR(1),

    -- Pais imediatos
    codigo_pai TEXT,
    nome_pai TEXT,
    codigo_mae TEXT,
    nome_mae TEXT,

    -- Avós paternos e maternos (2ª geração)
    codigo_avo_paterno TEXT,             -- Pai do pai
    nome_avo_paterno TEXT,
    codigo_avo_paterna TEXT,             -- Mãe do pai
    nome_avo_paterna TEXT,
    codigo_avo_materno TEXT,             -- Pai da mãe
    nome_avo_materno TEXT,
    codigo_avo_materna TEXT,             -- Mãe da mãe
    nome_avo_materna TEXT,

    -- Bisavós paternos e maternos (3ª geração)
    codigo_bisavo_paterno_paterno TEXT,  -- Pai do avô paterno
    nome_bisavo_paterno_paterno TEXT,
    codigo_bisavo_paterna_paterno TEXT,  -- Mãe do avô paterno
    nome_bisavo_paterna_paterno TEXT,

    codigo_bisavo_paterno_materno TEXT,  -- Pai da avó paterna
    nome_bisavo_paterno_materno TEXT,
    codigo_bisavo_paterna_materna TEXT,  -- Mãe da avó paterna
    nome_bisavo_paterna_materna TEXT,

    codigo_bisavo_materno_paterno TEXT,  -- Pai do avô materno
    nome_bisavo_materno_paterno TEXT,
    codigo_bisavo_materna_paterno TEXT,  -- Mãe do avô materno
    nome_bisavo_materna_paterno TEXT,

    codigo_bisavo_materno_materno TEXT,  -- Pai da avó materna
    nome_bisavo_materno_materno TEXT,
    codigo_bisavo_materna_materna TEXT,  -- Mãe da avó materna
    nome_bisavo_materna_materna TEXT
);

COMMENT ON TABLE bovinos_genealogia IS
'Tabela redundante que armazena a árvore genealógica até a 3ª geração (pais, avós e bisavós).
Usada para consultas rápidas e diretas, sem necessidade de JOINs.';

-- Índices úteis
CREATE INDEX idx_genealogia_pai ON bovinos_genealogia(codigo_pai);
CREATE INDEX idx_genealogia_mae ON bovinos_genealogia(codigo_mae);


-- ============================================================
CREATE TABLE impacto_producao_genealogico (
    codigo_ancestral TEXT,                -- Código do animal ancestral (touro ou vaca)
    nome_ancestral TEXT,
    sexo_ancestral CHAR(1),
    nivel_parentesco INTEGER,                -- '1 = filho', '2 = neto', '3 = bisneto'
    media_leite NUMERIC(18,10),
    producao_total NUMERIC(18,10),
    qtd_descendentes INTEGER,
    PRIMARY KEY (codigo_ancestral, nivel_parentesco)
);

COMMENT ON TABLE impacto_producao_genealogico IS
'Tabela pré-calculada com médias e totais de produção de leite por nível de descendência.
Permite consultas diretas sobre o impacto genético de cada indivíduo.';


-- ============================================================
-- VIEWS!!!

-- pega genealogia inteira até a 3° geração 
CREATE OR REPLACE VIEW vw_genealogia_completa AS
SELECT
    g.codigo AS codigo_animal,
    g.nome AS nome_animal,
    g.sexo,

    -- Pais
    g.codigo_pai, g.nome_pai,
    g.codigo_mae, g.nome_mae,

    -- Avós paternos e maternos
    g.codigo_avo_paterno, g.nome_avo_paterno as avô_paterno,
    g.codigo_avo_paterna, g.nome_avo_paterna as avó_paterna,
    g.codigo_avo_materno, g.nome_avo_materno as avô_materno,
    g.codigo_avo_materna, g.nome_avo_materna as avó_materna,

    -- Bisavós paternos e maternos
    g.codigo_bisavo_paterno_paterno, g.nome_bisavo_paterno_paterno as bisavô_paterno_paterno,
    g.codigo_bisavo_paterna_paterno, g.nome_bisavo_paterna_paterno as bisavó_paterna_paterna,
    g.codigo_bisavo_paterno_materno, g.nome_bisavo_paterno_materno as bisavô_paterno_materno,
    g.codigo_bisavo_paterna_materna, g.nome_bisavo_paterna_materna as bisavó_paterna_materna,
    g.codigo_bisavo_materno_paterno, g.nome_bisavo_materno_paterno as bisavô_materno_paterno,
    g.codigo_bisavo_materna_paterno, g.nome_bisavo_materna_paterno as bisavó_materna_paterno,
    g.codigo_bisavo_materno_materno, g.nome_bisavo_materno_materno as bisavô_materno_materno,
    g.codigo_bisavo_materna_materna, g.nome_bisavo_materna_materna as bisavó_materna_materna 

FROM bovinos_genealogia g;


-- View de média de produção por touro
CREATE OR REPLACE VIEW media_filhas_por_touro AS
SELECT 
    p.codigo AS codigo_touro,
    p.nome AS nome_touro,
    COUNT(DISTINCT f.codigo) AS qtd_filhas,
    AVG(fa.qtdeleite305) AS media_leite_filhas,
    SUM(fa.qtdeleite305) AS producao_total_filhas
FROM bovinos p
JOIN bovinos f ON f.numerorgpai = p.codigo         -- f = filha, p = pai (touro)
JOIN fichalactacao fa ON fa.codigo_bovino = f.codigo
WHERE p.sexo = 'M'
GROUP BY p.codigo, p.nome
ORDER BY media_leite_filhas DESC;

-- view de prod vitalicia
CREATE OR REPLACE VIEW producao_vitalicia AS
SELECT 
    b.codigo AS codigo_vaca,
    b.nome AS nome_vaca,
    COUNT(fa.codigo_bovino) AS qtd_lactacoes,
    SUM(fa.qtdeleite305) AS producao_total_leite,
    AVG(fa.qtdeleite305) AS media_por_lactacao,
    MAX(fa.dataencerramento) AS data_ultima_lactacao
FROM bovinos b
JOIN fichalactacao fa ON fa.codigo_bovino = b.codigo
WHERE b.sexo = 'F'
GROUP BY b.codigo, b.nome
ORDER BY producao_total_leite DESC;


-- producao por descendencia
CREATE OR REPLACE VIEW vw_producao_por_descendencia AS
SELECT
    i.codigo_ancestral,
    b.nome AS nome_ancestral,
    i.nivel_parentesco,
    i.qtd_descendentes,
    i.media_leite,
    i.producao_total
FROM impacto_producao_genealogico i
LEFT JOIN bovinos b ON b.codigo = i.codigo_ancestral;


CREATE OR REPLACE VIEW vw_eventos_completos AS
SELECT
    o.codigo_bovino,
    b.nome AS nome_bovino,
    o.dataocorrencia,
    o.tipo_evento,
    o.nro_crias,
    o.qtde_litros,
    o.facilidade_parto,
    COUNT(f.codigo_bovino) AS qtd_lactacoes,
    SUM(DISTINCT f.qtdeleite305) AS producao_vitalicia
FROM ocorrenciaEvento o
LEFT JOIN bovinos b ON b.codigo = o.codigo_bovino
LEFT JOIN fichalactacao f ON f.codigo_bovino = b.codigo
GROUP BY o.codigo_bovino, b.nome, o.dataocorrencia, o.tipo_evento, o.nro_crias, o.qtde_litros, o.facilidade_parto;


-- producao de cada boi
CREATE OR REPLACE VIEW vw_producao_por_bovino AS
SELECT
    b.codigo AS codigo_bovino,
    b.nome AS nome_bovino,
    COUNT(f.codigo_bovino) AS qtd_lactacoes,
    SUM(f.qtdeleite305) AS producao_total,
    AVG(f.qtdeleite305) AS producao_media,
    SUM(f.qtdegordura305) AS gordura_total,
    SUM(f.qtdeproteina305) AS proteina_total
FROM bovinos b
LEFT JOIN fichalactacao f ON f.codigo_bovino = b.codigo
GROUP BY b.codigo, b.nome;


-- view de impacto produtivo
CREATE OR REPLACE VIEW vw_impacto_produtivo AS
SELECT 
    i.codigo_ancestral,                          -- código do animal ancestral 
    b.nome AS nome_ancestral,                    -- nome do ancestral
    b.sexo AS sexo_ancestral,                    -- sexo (M ou F)
    i.nivel_parentesco,                          -- 1 = filhos, 2 = netos, 3 = bisnetos
    CASE 
        WHEN i.nivel_parentesco = 1 THEN 'Filhos'
        WHEN i.nivel_parentesco = 2 THEN 'Netos'
        WHEN i.nivel_parentesco = 3 THEN 'Bisnetos'
        ELSE 'Desconhecido'
    END AS descricao_parentesco,                 -- nome legível da geração
    i.qtd_descendentes,                          -- quantos descendentes foram considerados
    i.media_leite,                               -- média de produção dos descendentes
    i.producao_total                             -- produção total combinada dos descendentes
FROM impacto_producao_genealogico i
LEFT JOIN bovinos b ON b.codigo = i.codigo_ancestral
ORDER BY i.nivel_parentesco, i.media_leite DESC;

-- SERIE HISTORICA
CREATE OR REPLACE VIEW serie_historica_lactacao AS
SELECT
    b.codigo AS codigo_bovino,
    b.nome AS nome_bovino,
    EXTRACT(YEAR FROM f.dataencerramento) AS ano,
    COUNT(f.id) AS qtd_lactacoes,
    SUM(f.qtdeleite305) AS producao_anual_leite,
    AVG(f.qtdeleite305) AS media_anual_leite
FROM bovinos b
JOIN fichalactacao f ON b.codigo = f.codigo_bovino
GROUP BY b.codigo, b.nome, ano
ORDER BY b.codigo, ano;

-- IMPACTO PRODUTIVO DE ANIMAIS ATE 3 GERAÇÕES
CREATE OR REPLACE VIEW impacto_producao_completo AS
SELECT
    g.codigo_pai AS codigo_ancestral,
    '1'::INTEGER AS nivel_parentesco,
    AVG(f.qtdeleite305) AS media_leite,
    SUM(f.qtdeleite305) AS producao_total,
    COUNT(DISTINCT f.codigo_bovino) AS qtd_descendentes
FROM bovinos_genealogia g
JOIN fichalactacao f ON g.codigo = f.codigo_bovino
WHERE g.codigo_pai IS NOT NULL
GROUP BY g.codigo_pai

UNION ALL

SELECT
    g.codigo_avo_paterno AS codigo_ancestral,
    '2'::INTEGER AS nivel_parentesco,
    AVG(f.qtdeleite305),
    SUM(f.qtdeleite305),
    COUNT(DISTINCT f.codigo_bovino)
FROM bovinos_genealogia g
JOIN fichalactacao f ON g.codigo = f.codigo_bovino
WHERE g.codigo_avo_paterno IS NOT NULL
GROUP BY g.codigo_avo_paterno

UNION ALL

SELECT
    g.codigo_bisavo_paterno_paterno AS codigo_ancestral,
    '3'::INTEGER AS nivel_parentesco,
    AVG(f.qtdeleite305),
    SUM(f.qtdeleite305),
    COUNT(DISTINCT f.codigo_bovino)
FROM bovinos_genealogia g
JOIN fichalactacao f ON g.codigo = f.codigo_bovino
WHERE g.codigo_bisavo_paterno_paterno IS NOT NULL
GROUP BY g.codigo_bisavo_paterno_paterno;


-- essa view junta informações genealógicas (pais, avós) com métricas produtivas já calculadas. Isso reduz a 
-- necessidade de JOINs complexos e simplifica a vida da LLM na hora de gerar queries em linguagem natural
CREATE OR REPLACE VIEW resumo_genealogico_produtivo AS
SELECT 
    g.codigo,
    g.nome,

    g.codigo_pai,
    g.codigo_mae,
    g.codigo_avo_paterno,
    g.codigo_avo_materno,

    ip.media_leite,          -- media produção de leite herdada (dos descendentes)
    ip.qtd_descendentes,     -- qnt de descendentes considerados na conta
    ip.nivel_parentesco      -- parentesco usado na conta (1=filho, 2=neto, 3=bisneto)
FROM bovinos_genealogia g
LEFT JOIN impacto_producao_genealogico ip 
ON ip.codigo_ancestral = g.codigo;

