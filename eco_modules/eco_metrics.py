"""
All metric calculations live here.
Both the dashboard UI and the report exporter call ONLY these functions.
All functions accept an already-filtered DataFrame.
"""
from __future__ import annotations

from typing import Literal, Tuple

import pandas as pd


# ─── KPI ────────────────────────────────────────────────────────────────────

def get_kpi(df: pd.DataFrame) -> dict:
    """Return a dict of scalar KPI values for the given (filtered) DataFrame."""
    total = len(df)
    done = int((df["status"] == "выполнено").sum())
    in_progress = int((df["status"] == "в работе").sum())
    pct = f"{done / total * 100:.1f}%" if total > 0 else "—"

    omsu_count = int(df["omsu"].nunique())
    category_count = int(
        df.loc[df["category"] != "Не указано", "category"].nunique()
        if "category" in df.columns else 0
    )

    valid_dates = df["date"].dropna() if "date" in df.columns else pd.Series(dtype="datetime64[ns]")
    if len(valid_dates) > 0:
        date_min = valid_dates.min().strftime("%d.%m.%Y")
        date_max = valid_dates.max().strftime("%d.%m.%Y")
        period = f"{date_min} – {date_max}"
    else:
        date_min = date_max = "—"
        period = "—"

    return {
        "total": total,
        "done": done,
        "in_progress": in_progress,
        "pct_done": pct,
        "omsu_count": omsu_count,
        "category_count": category_count,
        "period": period,
        "date_min": date_min,
        "date_max": date_max,
    }


# ─── Cross-sections ──────────────────────────────────────────────────────────

def get_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Count, share, and status breakdown per category, sorted by count desc."""
    if len(df) == 0:
        return pd.DataFrame(columns=["Категория", "Всего", "Доля %", "Выполнено", "В работе"])

    total = len(df)
    counts = df.groupby("category", observed=True).size().rename("Всего")
    done   = df[df["status"] == "выполнено"].groupby("category", observed=True).size().rename("Выполнено")
    in_p   = df[df["status"] == "в работе"].groupby("category", observed=True).size().rename("В работе")

    out = (
        pd.concat([counts, done, in_p], axis=1)
        .fillna(0)
        .astype({"Всего": int, "Выполнено": int, "В работе": int})
        .reset_index()
    )
    out.columns = ["Категория", "Всего", "Выполнено", "В работе"]
    out["Доля %"] = (out["Всего"] / total * 100).round(1)
    out = out.sort_values("Всего", ascending=False).reset_index(drop=True)
    return out[["Категория", "Всего", "Доля %", "Выполнено", "В работе"]]


def get_by_omsu(df: pd.DataFrame) -> pd.DataFrame:
    """Count, share, backlog % per OMSU, sorted by count desc."""
    if len(df) == 0:
        return pd.DataFrame(columns=["ОМСУ", "Всего", "Доля %", "Выполнено", "В работе", "Бэклог %"])

    total = len(df)
    counts = df.groupby("omsu", observed=True).size().rename("Всего")
    done   = df[df["status"] == "выполнено"].groupby("omsu", observed=True).size().rename("Выполнено")
    in_p   = df[df["status"] == "в работе"].groupby("omsu", observed=True).size().rename("В работе")

    out = (
        pd.concat([counts, done, in_p], axis=1)
        .fillna(0)
        .astype({"Всего": int, "Выполнено": int, "В работе": int})
        .reset_index()
    )
    out.columns = ["ОМСУ", "Всего", "Выполнено", "В работе"]
    out["Доля %"]   = (out["Всего"] / total * 100).round(1)
    out["Бэклог %"] = (out["В работе"] / out["Всего"].replace(0, pd.NA) * 100).round(1).fillna(0.0)
    out = out.sort_values("Всего", ascending=False).reset_index(drop=True)
    return out[["ОМСУ", "Всего", "Доля %", "Выполнено", "В работе", "Бэклог %"]]


def get_by_mro(df: pd.DataFrame) -> pd.DataFrame:
    """Count, share, and status breakdown per MRO, sorted by count desc."""
    if len(df) == 0:
        return pd.DataFrame(columns=["МРО", "Всего", "Доля %", "Выполнено", "В работе"])

    total = len(df)
    counts = df.groupby("mro", observed=True).size().rename("Всего")
    done   = df[df["status"] == "выполнено"].groupby("mro", observed=True).size().rename("Выполнено")
    in_p   = df[df["status"] == "в работе"].groupby("mro", observed=True).size().rename("В работе")

    out = (
        pd.concat([counts, done, in_p], axis=1)
        .fillna(0)
        .astype({"Всего": int, "Выполнено": int, "В работе": int})
        .reset_index()
    )
    out.columns = ["МРО", "Всего", "Выполнено", "В работе"]
    out["Доля %"] = (out["Всего"] / total * 100).round(1)
    out = out.sort_values("Всего", ascending=False).reset_index(drop=True)
    return out[["МРО", "Всего", "Доля %", "Выполнено", "В работе"]]


# ─── Time series ─────────────────────────────────────────────────────────────

def get_time_series(df: pd.DataFrame, freq: Literal["D", "W"] = "D") -> pd.DataFrame:
    """
    Return daily or weekly counts split by status.

    Columns: Дата | Выполнено | В работе
    """
    if len(df) == 0 or "date" not in df.columns:
        return pd.DataFrame(columns=["Дата", "Выполнено", "В работе"])

    valid = df.dropna(subset=["date"]).copy()
    if len(valid) == 0:
        return pd.DataFrame(columns=["Дата", "Выполнено", "В работе"])

    period_freq = "W-MON" if freq == "W" else "D"
    ts = (
        valid.groupby([pd.Grouper(key="date", freq=period_freq), "status"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    ts.columns.name = None
    ts = ts.rename(columns={"date": "Дата", "выполнено": "Выполнено", "в работе": "В работе"})
    for col in ("Выполнено", "В работе"):
        if col not in ts.columns:
            ts[col] = 0
    return ts[["Дата", "Выполнено", "В работе"]]


# ─── Trash analytics ─────────────────────────────────────────────────────────

def get_trash_analysis(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filter rows where category matches 'мусор/свалки/стоки' and compute OMSU stats.

    Returns
    -------
    top_by_count   : OMSU sorted by total appeals desc
    top_by_backlog : OMSU sorted by backlog % desc
    """
    _empty = pd.DataFrame(columns=["ОМСУ", "Всего", "Выполнено", "В работе", "Доля %", "Бэклог %"])

    if len(df) == 0 or "category" not in df.columns:
        return _empty, _empty

    mask = df["category"].str.lower().str.contains("мусор|свалк|стоки", na=False, regex=True)
    trash = df[mask].copy()

    if len(trash) == 0:
        return _empty, _empty

    total = len(trash)
    counts = trash.groupby("omsu", observed=True).size().rename("Всего")
    done   = trash[trash["status"] == "выполнено"].groupby("omsu", observed=True).size().rename("Выполнено")
    in_p   = trash[trash["status"] == "в работе"].groupby("omsu", observed=True).size().rename("В работе")

    out = (
        pd.concat([counts, done, in_p], axis=1)
        .fillna(0)
        .astype({"Всего": int, "Выполнено": int, "В работе": int})
        .reset_index()
    )
    out.columns = ["ОМСУ", "Всего", "Выполнено", "В работе"]
    out["Доля %"]   = (out["Всего"] / total * 100).round(1)
    out["Бэклог %"] = (out["В работе"] / out["Всего"].replace(0, pd.NA) * 100).round(1).fillna(0.0)

    top_count   = out.sort_values("Всего",    ascending=False).reset_index(drop=True)
    top_backlog = out.sort_values("Бэклог %", ascending=False).reset_index(drop=True)

    return (
        top_count[["ОМСУ", "Всего", "Выполнено", "В работе", "Доля %", "Бэклог %"]],
        top_backlog[["ОМСУ", "Всего", "Выполнено", "В работе", "Доля %", "Бэклог %"]],
    )