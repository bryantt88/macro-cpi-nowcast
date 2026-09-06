"""Expanding-window walk-forward training + scoring (Stage 4).

For each out-of-sample month we retrain on all prior months only, then predict that one
month — no look-ahead, no k-fold. Models: ridge (median-impute + standardize + in-window
RidgeCV alpha) and a shallow, regularized LightGBM (handles NaN natively). Both are
pre-registered: hyperparameters are fixed or tuned only inside the training window, never
on test scores. Everything is judged against the persistence baseline (cpi_mom_lag1).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from macro_nowcast import config

_MODELS = ("persistence", "ridge", "lgbm", "ensemble")


def _make_ridge() -> Pipeline:
    """Ridge with in-window median imputation, standardization, and GCV alpha selection."""
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", RidgeCV(alphas=np.logspace(-2, 3, 20))),  # tuned within train window only
        ]
    )


def _make_lgbm() -> LGBMRegressor:
    """Shallow, strongly-regularized LightGBM (fixed, pre-registered params)."""
    return LGBMRegressor(
        n_estimators=300,
        learning_rate=0.03,
        num_leaves=7,
        max_depth=3,
        min_child_samples=25,
        subsample=0.8,
        subsample_freq=1,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        random_state=0,
        verbose=-1,
    )


def _metrics(actual: np.ndarray, pred: np.ndarray, persist: np.ndarray) -> dict:
    """RMSE/MAE, plus direction (accel vs decel vs last print) and per-month hit-rate vs naive."""
    err = pred - actual
    rmse = float(np.sqrt(np.mean(err**2)))
    mae = float(np.mean(np.abs(err)))
    # Directional call = does the model correctly say inflation speeds up or slows vs last month?
    actual_dir = np.sign(actual - persist)
    pred_dir = np.sign(pred - persist)
    scored = actual_dir != 0  # months where there IS a direction to call
    dir_acc = float(np.mean(actual_dir[scored] == pred_dir[scored])) if scored.any() else float("nan")
    # Hit-rate = fraction of months the model's abs error beats persistence's.
    hit = float(np.mean(np.abs(err) < np.abs(persist - actual)))
    return {"rmse": rmse, "mae": mae, "dir_acc": dir_acc, "hit_rate": hit}


def walk_forward_eval(features: pd.DataFrame, min_train: int | None = None) -> dict:
    """Run expanding walk-forward; return OOS predictions + per-model metrics.

    Args:
        features: point-in-time matrix with a 'target' column and 'cpi_mom_lag1' (persistence).
        min_train: months before the first prediction (defaults to BacktestConfig.min_train_months).
    """
    min_train = min_train or config.BACKTEST.min_train_months
    df = features.dropna(subset=["target"]).copy()
    feat_cols = [c for c in df.columns if c != "target"]
    X, y = df[feat_cols], df["target"].to_numpy()
    persist = df["cpi_mom_lag1"].to_numpy()
    idx = df.index
    n = len(df)
    if n <= min_train:
        raise ValueError(f"only {n} rows but min_train={min_train}; nothing to score.")

    records = []
    for t in range(min_train, n):
        x_tr, y_tr, x_te = X.iloc[:t], y[:t], X.iloc[t : t + 1]
        ridge_pred = float(_make_ridge().fit(x_tr, y_tr).predict(x_te)[0])
        lgbm_pred = float(_make_lgbm().fit(x_tr, y_tr).predict(x_te)[0])
        records.append((idx[t], y[t], persist[t], ridge_pred, lgbm_pred))

    oos = pd.DataFrame(records, columns=["date", "actual", "persistence", "ridge", "lgbm"]).set_index("date")
    oos["ensemble"] = (oos["ridge"] + oos["lgbm"]) / 2.0

    # Score all models on the SAME months where the target and persistence are both defined
    # (a rare CPI first-print gap can leave persistence NaN); keeps the comparison fair.
    scored = oos.dropna(subset=["actual", "persistence"])
    actual, persist_oos = scored["actual"].to_numpy(), scored["persistence"].to_numpy()
    metrics = {m: _metrics(actual, scored[m].to_numpy(), persist_oos) for m in _MODELS}
    rmse_base = metrics["persistence"]["rmse"]
    for m in _MODELS:
        metrics[m]["rmse_skill"] = float(1 - metrics[m]["rmse"] / rmse_base)  # >0 beats naive

    return {"oos": scored, "metrics": metrics, "min_train": min_train, "n_oos": len(scored)}
