import pandas as pd
from typing import Any, Dict, List, Union

AllowedScalar = Union[int, float, str]

def _apply_where(df: pd.DataFrame, where: Dict[str, AllowedScalar] | None) -> pd.DataFrame:
    """Aplica filtros simples de igualdade. Ignora colunas inexistentes."""
    if not where:
        return df
    out = df.copy()
    for col, val in where.items():
        if col in out.columns:
            out = out[out[col] == val]
    return out


def _ensure_list(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x]
    return [str(x)]


def apply_plan(df: pd.DataFrame, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Executa um plano de cálculos determinísticos (whitelist) sobre um DataFrame.

    Operações suportadas (em step["op"]):
      - "sum", "mean", "median", "min", "max", "std", "var", "count", "nunique"
      - "topk" (k), "percentile" (q em 0..1), "ratio" (numerator/denominator), "rate_per" (per), "cumsum"
    Campos opcionais:
      - "by": lista de colunas para agrupar
      - "where": filtros simples (igualdade)
      - "label": rótulo do resultado dessa etapa (chave no dict final)
    """
    results: Dict[str, Any] = {}

    for step in plan or []:
        sid = str(step.get("id", f"step_{len(results)+1}"))
        op = str(step.get("op", "")).lower()
        on = _ensure_list(step.get("on"))
        by = _ensure_list(step.get("by"))
        where = step.get("where")
        k = step.get("k")
        q = step.get("q")
        numerator = step.get("numerator")
        denominator = step.get("denominator")
        per = step.get("per", None)
        label = step.get("label", sid)

        data = _apply_where(df, where)

        # valida colunas
        on_cols = [c for c in on if c in data.columns]
        if numerator and numerator not in data.columns:
            numerator = None

        # normaliza denominador (pode ser coluna ou constante)
        den = denominator
        if isinstance(den, str) and den not in data.columns:
            try:
                den = float(den)
            except Exception:
                den = None

        # agrupamento opcional
        g = data.groupby(by, dropna=False) if by and all(b in data.columns for b in by) else None

        result_obj: Any = None

        if op in {"sum", "mean", "median", "min", "max", "std", "var", "count", "nunique"}:
            if op == "count" and not on_cols:
                # count total/grupo
                if g is not None:
                    res = g.size().reset_index(name="count")
                else:
                    res = pd.DataFrame([{"count": int(len(data))}])
            else:
                agg_map = {c: op for c in on_cols} if on_cols else None
                if g is not None and agg_map:
                    res = g.agg(agg_map).reset_index()
                elif agg_map:
                    res = data[on_cols].agg(op).to_frame().T
                else:
                    res = pd.DataFrame()
            result_obj = res.to_dict(orient="records")

        elif op == "topk":
            col = on_cols[0] if on_cols else None
            kk = int(k or 5)
            if col is None:
                result_obj = []
            else:
                if g is not None:
                    res = g.apply(lambda x: x.nlargest(kk, columns=col)).reset_index(drop=True)
                else:
                    res = data.nlargest(kk, columns=col)
                result_obj = res.to_dict(orient="records")

        elif op == "percentile":
            col = on_cols[0] if on_cols else None
            if col is None:
                result_obj = []
            else:
                qq = float(q or 0.5)
                if g is not None:
                    res = g[col].quantile(qq).reset_index(name=f"p{int(qq*100)}_{col}")
                else:
                    res = pd.DataFrame([{f"p{int(qq*100)}_{col}": float(data[col].quantile(qq))}])
                result_obj = res.to_dict(orient="records")

        elif op == "ratio":
            if numerator is None or den is None:
                result_obj = []
            else:
                if g is not None:
                    if isinstance(den, (int, float)):
                        s = g[numerator].sum() / float(den)
                        res = s.reset_index(name=f"ratio_{numerator}_const")
                    else:
                        res = (g[numerator].sum() / g[den].sum()).reset_index(
                            name=f"ratio_{numerator}_by_{den}"
                        )
                else:
                    num_sum = data[numerator].sum()
                    den_sum = float(den) if isinstance(den, (int, float)) else data[den].sum()
                    val = float(num_sum) / (den_sum if den_sum else 1.0)
                    res = pd.DataFrame([{"ratio": val}])
                result_obj = res.to_dict(orient="records")

        elif op == "rate_per":
            if numerator is None or den is None:
                result_obj = []
            else:
                base = float(per or 1.0)
                if g is not None:
                    if isinstance(den, (int, float)):
                        s = (g[numerator].sum() / float(den)) * base
                        res = s.reset_index(name=f"rate_per_{int(base)}")
                    else:
                        res = (g[numerator].sum() / g[den].sum() * base).reset_index(
                            name=f"rate_per_{int(base)}"
                        )
                else:
                    num_sum = data[numerator].sum()
                    den_sum = float(den) if isinstance(den, (int, float)) else data[den].sum()
                    val = float(num_sum) / (den_sum if den_sum else 1.0) * base
                    res = pd.DataFrame([{"rate": val}])
                result_obj = res.to_dict(orient="records")

        elif op == "cumsum":
            col = on_cols[0] if on_cols else None
            if col is None:
                result_obj = []
            else:
                if g is not None:
                    res = g[col].cumsum().reset_index(name=f"cumsum_{col}")
                else:
                    res = pd.DataFrame({f"cumsum_{col}": data[col].cumsum()})
                result_obj = res.to_dict(orient="records")

        else:
            result_obj = {"warning": f"operação não suportada: {op}"}

        results[label] = result_obj

    return results
