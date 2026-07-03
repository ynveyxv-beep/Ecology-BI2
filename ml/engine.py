# ml/engine.py
"""
Классические ML-алгоритмы на чистом numpy/pandas.
Никаких тяжёлых зависимостей — только то, что уже в проекте.

Публичный API:
    forecast_linear(series, n_periods)  → ForecastResult
    detect_anomalies(series, method)    → AnomalyResult
    cluster_kmeans(df, columns, k)      → ClusterResult
    correlate(df, columns)              → CorrResult
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Типы результатов
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ForecastResult:
    """Результат линейного прогноза."""
    # Исходный ряд
    x_hist: np.ndarray          # индексы (0…n-1)
    y_hist: np.ndarray          # фактические значения
    # Линия тренда по историческим данным
    y_trend: np.ndarray         # len == len(x_hist)
    # Прогноз
    x_fore: np.ndarray          # индексы будущих точек
    y_fore: np.ndarray          # прогнозные значения
    y_fore_lo: np.ndarray       # нижняя граница (±1.5σ)
    y_fore_hi: np.ndarray       # верхняя граница (±1.5σ)
    # Метрики
    r2: float                   # R²
    slope: float                # наклон (ед./период)
    intercept: float


@dataclass
class AnomalyResult:
    """Результат детекции аномалий."""
    x: np.ndarray               # индексы точек
    y: np.ndarray               # значения
    is_anomaly: np.ndarray      # bool-маска
    scores: np.ndarray          # |z-score| или IQR-score
    threshold: float            # порог, при котором точка — аномалия
    method: str                 # 'zscore' | 'iqr'
    n_anomalies: int


@dataclass
class ClusterResult:
    """Результат K-Means кластеризации."""
    labels: np.ndarray          # метка кластера для каждой строки
    centroids: np.ndarray       # (k, n_features)
    inertia: float              # сумма квадратов расстояний до центроидов
    x: np.ndarray               # первая фича (для 2D-plot)
    y: np.ndarray               # вторая фича
    col_names: List[str]        # имена колонок, которые использовались
    k: int


@dataclass
class CorrResult:
    """Результат корреляционного анализа."""
    matrix: pd.DataFrame        # pandas корреляционная матрица
    columns: List[str]
    top_pairs: List[tuple]      # [(col_a, col_b, corr_value), …] топ-5 по |corr|


# ─────────────────────────────────────────────────────────────────────────────
# Вспомогательные функции
# ─────────────────────────────────────────────────────────────────────────────

def _to_float_array(series: pd.Series) -> np.ndarray:
    """Приводит серию к float64, убирая NaN-ы интерполяцией."""
    arr = pd.to_numeric(series, errors='coerce').astype(float)
    arr = pd.Series(arr).interpolate(method='linear').ffill().bfill().to_numpy()
    return arr


def _r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 1. Линейное прогнозирование
# ─────────────────────────────────────────────────────────────────────────────

def forecast_linear(
    series: pd.Series,
    n_periods: int = 6,
) -> ForecastResult:
    """
    Линейный тренд + прогноз на n_periods точек вперёд.
    Использует numpy.polyfit(deg=1).
    Доверительный интервал — ±1.5 стандартных отклонения остатков.
    """
    y = _to_float_array(series)
    n = len(y)
    if n < 2:
        raise ValueError("Нужно не менее 2 точек для прогноза.")

    x = np.arange(n, dtype=float)

    # Линейная регрессия
    slope, intercept = np.polyfit(x, y, 1)
    y_trend = slope * x + intercept

    # Остатки → σ
    residuals = y - y_trend
    sigma = np.std(residuals, ddof=1) if n > 1 else 0.0

    r2 = _r2_score(y, y_trend)

    # Прогноз
    x_fore = np.arange(n, n + n_periods, dtype=float)
    y_fore = slope * x_fore + intercept
    margin  = 1.5 * sigma
    y_fore_lo = y_fore - margin
    y_fore_hi = y_fore + margin

    return ForecastResult(
        x_hist=x, y_hist=y,
        y_trend=y_trend,
        x_fore=x_fore, y_fore=y_fore,
        y_fore_lo=y_fore_lo, y_fore_hi=y_fore_hi,
        r2=r2, slope=slope, intercept=intercept,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Детекция аномалий
# ─────────────────────────────────────────────────────────────────────────────

def detect_anomalies(
    series: pd.Series,
    method: str = 'zscore',
    threshold: Optional[float] = None,
) -> AnomalyResult:
    """
    Детекция аномалий в одномерном ряду.

    method='zscore': аномалия если |z| > threshold (по умолч. 2.5)
    method='iqr':    аномалия если значение выходит за [Q1-k*IQR, Q3+k*IQR]
                     threshold — коэффициент k (по умолч. 1.5)
    """
    y = _to_float_array(series)
    n = len(y)
    x = np.arange(n, dtype=float)

    if method == 'zscore':
        thr = threshold if threshold is not None else 2.5
        mean, std = np.mean(y), np.std(y, ddof=1)
        scores = np.abs((y - mean) / std) if std > 0 else np.zeros(n)
        is_anomaly = scores > thr

    elif method == 'iqr':
        thr = threshold if threshold is not None else 1.5
        q1, q3 = np.percentile(y, 25), np.percentile(y, 75)
        iqr = q3 - q1
        lo, hi = q1 - thr * iqr, q3 + thr * iqr
        # score = расстояние до ближайшей границы (0 если внутри)
        scores = np.maximum(lo - y, y - hi, np.zeros(n))
        if iqr > 0:
            scores = scores / iqr
        is_anomaly = (y < lo) | (y > hi)

    else:
        raise ValueError(f"Неизвестный метод: {method!r}. Используйте 'zscore' или 'iqr'.")

    return AnomalyResult(
        x=x, y=y,
        is_anomaly=is_anomaly,
        scores=scores,
        threshold=thr,
        method=method,
        n_anomalies=int(np.sum(is_anomaly)),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. K-Means кластеризация (numpy)
# ─────────────────────────────────────────────────────────────────────────────

def _kmeans_plusplus_init(X: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    """K-Means++ инициализация центроидов."""
    n = X.shape[0]
    idx = rng.integers(0, n)
    centers = [X[idx]]
    for _ in range(k - 1):
        dists = np.array([min(np.sum((x - c) ** 2) for c in centers) for x in X])
        probs = dists / dists.sum()
        idx = rng.choice(n, p=probs)
        centers.append(X[idx])
    return np.array(centers)


def cluster_kmeans(
    df: pd.DataFrame,
    columns: List[str],
    k: int = 3,
    max_iter: int = 100,
    n_init: int = 5,
    random_state: int = 42,
) -> ClusterResult:
    """
    K-Means кластеризация. Реализован на чистом numpy (K-Means++).
    Запускается n_init раз, возвращает лучший результат (мин. инертность).
    """
    sub = df[columns].copy()
    # Убираем строки с NaN
    sub = sub.dropna()
    if len(sub) < k:
        raise ValueError(f"Недостаточно строк ({len(sub)}) для {k} кластеров.")

    X = sub.to_numpy(dtype=float)

    # Нормализация (min-max по каждой фиче)
    x_min = X.min(axis=0)
    x_max = X.max(axis=0)
    rng_vals = np.where(x_max - x_min > 0, x_max - x_min, 1.0)
    X_norm = (X - x_min) / rng_vals

    rng = np.random.default_rng(random_state)

    best_labels, best_centroids, best_inertia = None, None, np.inf

    for _ in range(n_init):
        centroids = _kmeans_plusplus_init(X_norm, k, rng)

        for _iter in range(max_iter):
            # Присваивание точек к ближайшему центроиду
            dists = np.linalg.norm(X_norm[:, None, :] - centroids[None, :, :], axis=2)
            labels = np.argmin(dists, axis=1)

            # Обновление центроидов
            new_centroids = np.array([
                X_norm[labels == j].mean(axis=0) if np.any(labels == j) else centroids[j]
                for j in range(k)
            ])

            if np.allclose(centroids, new_centroids, atol=1e-6):
                break
            centroids = new_centroids

        # Инертность
        inertia = sum(
            np.sum((X_norm[labels == j] - centroids[j]) ** 2)
            for j in range(k)
        )
        if inertia < best_inertia:
            best_inertia = inertia
            best_labels = labels.copy()
            best_centroids = centroids.copy()

    # Центроиды обратно в исходное пространство
    best_centroids_orig = best_centroids * rng_vals + x_min

    return ClusterResult(
        labels=best_labels,
        centroids=best_centroids_orig,
        inertia=float(best_inertia),
        x=X[:, 0],
        y=X[:, 1] if X.shape[1] > 1 else np.zeros(len(X)),
        col_names=list(columns),
        k=k,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Корреляционный анализ
# ─────────────────────────────────────────────────────────────────────────────

def correlate(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
) -> CorrResult:
    """
    Матрица корреляции Пирсона (pandas .corr()).
    Если columns=None — берём все числовые колонки.
    """
    if columns is None:
        columns = list(df.select_dtypes(include='number').columns)
    if len(columns) < 2:
        raise ValueError("Нужно не менее 2 числовых колонок для корреляции.")

    sub = df[columns].apply(pd.to_numeric, errors='coerce')
    matrix = sub.corr(method='pearson')

    # Топ-5 пар по |corr| (исключая диагональ)
    pairs = []
    cols = matrix.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = matrix.iloc[i, j]
            if pd.notna(val):
                pairs.append((cols[i], cols[j], round(float(val), 4)))
    pairs.sort(key=lambda t: abs(t[2]), reverse=True)

    return CorrResult(
        matrix=matrix,
        columns=cols,
        top_pairs=pairs[:5],
    )
