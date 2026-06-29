"""
Data loading, validation, and cleaning for the eco-monitoring dashboard.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Tuple

import pandas as pd

# Canonical OMSU name for each non-canonical normalized form.
# Keys are produced by _norm(); values are the display strings used throughout the app.
OMSU_SYNONYMS: dict[str, str] = {
    "городскойокругкстовскийрайон": "Кстовский муниципальный округ",
}

# Internal field name → list of normalized substrings to look for in column headers.
# Longer / more specific variants must come first to avoid false matches.
_FIELD_VARIANTS: dict[str, list[str]] = {
    "npp":      ["пп", "npp"],
    "date":     ["дата", "date"],
    "req_no":   ["номерзаявки", "номер", "reqno"],
    "time":     ["время", "time"],
    "category": ["категория", "category"],
    "mro":      ["мро", "mro"],
    "omsu":     ["омсу", "omsu"],
    "status":   ["статусзаявки", "статус", "status"],
}

REQUIRED_FIELDS = {"npp", "date", "req_no", "mro", "omsu", "status"}

_FIELD_LABELS = {
    "npp":    "№пп",
    "date":   "Дата",
    "req_no": "Номер заявки",
    "mro":    "МРО",
    "omsu":   "ОМСУ",
    "status": "Статус заявки",
}

_CANONICAL_STATUSES = {"выполнено", "в работе"}


def _norm(s: str) -> str:
    """Lowercase + strip all non-alphanumeric characters (Cyrillic/Latin)."""
    return re.sub(r"[^а-яёa-z0-9]", "", str(s).lower())


def _match_columns(raw_cols: list) -> dict[str, str]:
    """Return {internal_field: original_column_name} for as many fields as found."""
    normed = {_norm(c): c for c in raw_cols}
    result: dict[str, str] = {}
    for field, variants in _FIELD_VARIANTS.items():
        for v in variants:
            key = _norm(v)
            for nc, orig in normed.items():
                if nc == key or nc.startswith(key) or key in nc:
                    if field not in result:
                        result[field] = orig
            if field in result:
                break
    return result


def _normalize_omsu(val) -> str:
    if pd.isna(val):
        return "Не указано"
    key = _norm(str(val))
    return OMSU_SYNONYMS.get(key, str(val).strip())


def _normalize_status(val) -> str:
    if pd.isna(val):
        return "Не указано"
    s = str(val).strip().lower()
    if s == "выполнено":
        return "выполнено"
    if s in ("в работе", "вработе"):
        return "в работе"
    return "Не указано"


def _parse_time_series(series: pd.Series) -> pd.Series:
    """Convert a mixed-type time column to Timestamps (date part fixed to 2000-01-01)."""
    def _one(val):
        if pd.isna(val):
            return pd.NaT
        if isinstance(val, dt.time):
            return pd.Timestamp(2000, 1, 1, val.hour, val.minute, val.second)
        if isinstance(val, pd.Timedelta):
            return pd.Timestamp("2000-01-01") + val
        if isinstance(val, dt.timedelta):
            return pd.Timestamp("2000-01-01") + pd.Timedelta(val)
        try:
            return pd.to_datetime(str(val), format="%H:%M:%S")
        except Exception:
            try:
                return pd.to_datetime(val)
            except Exception:
                return pd.NaT

    return series.apply(_one)


def load_excel(path: str) -> Tuple[pd.DataFrame, dict]:
    """
    Load and clean an Excel file.

    Returns
    -------
    df_clean : pd.DataFrame
        Cleaned data with internal column names.
    report : dict
        Validation summary with row counts, duplicate info, and anomalies.

    Raises
    ------
    ValueError
        If a required column is missing.
    """
    raw = pd.read_excel(path)
    col_map = _match_columns(list(raw.columns))

    missing = REQUIRED_FIELDS - set(col_map.keys())
    if missing:
        labels = [_FIELD_LABELS.get(m, m) for m in sorted(missing)]
        raise ValueError(f"Не найдены обязательные колонки: {', '.join(labels)}")

    df = raw.rename(columns={v: k for k, v in col_map.items()})[list(col_map.keys())].copy()

    report: dict = {"total_rows": len(df)}

    # ── Deduplication ────────────────────────────────────────────────────
    dupes = df.duplicated(subset=["req_no"], keep="first")
    report["duplicates_removed"] = int(dupes.sum())
    df = df[~dupes].copy()

    # ── Date parsing ─────────────────────────────────────────────────────
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    report["unparseable_dates"] = int(df["date"].isna().sum())

    # ── Time parsing ─────────────────────────────────────────────────────
    if "time" in df.columns:
        df["time"] = _parse_time_series(df["time"])
    report["empty_time"] = int(df["time"].isna().sum()) if "time" in df.columns else 0

    # ── Category fill ────────────────────────────────────────────────────
    report["empty_category"] = int(df["category"].isna().sum()) if "category" in df.columns else 0
    if "category" in df.columns:
        df["category"] = df["category"].fillna("Не указано")

    # ── OMSU normalisation ───────────────────────────────────────────────
    df["omsu"] = df["omsu"].apply(_normalize_omsu)

    # ── Status normalisation ─────────────────────────────────────────────
    if "status" in df.columns:
        orig_status = df["status"].copy()
        df["status"] = df["status"].apply(_normalize_status)
        bad_mask = ~df["status"].isin(_CANONICAL_STATUSES)
        report["unknown_statuses"] = [
            s for s in orig_status[bad_mask].unique() if not pd.isna(s)
        ]
    else:
        report["unknown_statuses"] = []

    # ── Numeric coercion ─────────────────────────────────────────────────
    for col in ("npp", "req_no"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    report["empty_by_col"] = {c: int(df[c].isna().sum()) for c in df.columns}
    report["clean_rows"] = len(df)

    return df, report


def load_excel_with_report(path: str) -> Tuple[pd.DataFrame, dict]:
    """
    Загружает Excel и возвращает (df, report).
    Алиас для load_excel для совместимости.
    """
    return load_excel(path)