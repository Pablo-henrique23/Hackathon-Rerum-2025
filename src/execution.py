import pandas as pd
from operations import apply_plan


# Simula o DataFrame que veio do SELECT
df = pd.DataFrame([
    {"touro_nome": "Apollo", "vaca": "Nana", "numero_parto": 1, "litros_total": 4800},
    {"touro_nome": "Apollo", "vaca": "Mia",  "numero_parto": 1, "litros_total": 5200},
    {"touro_nome": "Zeus",   "vaca": "Luna", "numero_parto": 1, "litros_total": 6100},
    {"touro_nome": "Zeus",   "vaca": "Ella", "numero_parto": 2, "litros_total": 5900},
    {"touro_nome": "Thor",   "vaca": "Ana",  "numero_parto": 1, "litros_total": 5500},
])


# Plano de cálculo (whitelist de operações)
calc_plan = [
  {"id":"m1","op":"mean","on":"litros_total","by":["touro_nome"],"label":"media_litros_por_touro"},
  {"id":"m2","op":"topk","on":"litros_total","k":3,"label":"top3_lactacoes"},
  {"id":"m3","op":"percentile","on":"litros_total","q":0.9,"label":"p90_litros"},
  {"id":"m4","op":"ratio","numerator":"litros_total","denominator":2,"label":"litros_div_2"},
  {"id":"m5","op":"rate_per","numerator":"litros_total","denominator":"numero_parto","per":1000,"label":"taxa_por_1000"}
]


results = apply_plan(df, calc_plan)
print(results)

