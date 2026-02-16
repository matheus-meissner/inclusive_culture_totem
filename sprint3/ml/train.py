from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple, List

import joblib
import numpy as np
import pandas as pd

# ✅ FIX DEFINITIVO: força backend headless (sem Tkinter)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split

from database.db import get_conn, init_db


# ============================================================
# Config
# ============================================================
SEED = 42
MODEL_VERSION = "rf_v2"  # inclui sanity check sem duration_s
MODEL_NAME = "RandomForestClassifier"

# Paths robustos (não quebram se rodar de qualquer lugar)
ML_DIR = Path(__file__).resolve().parent
SPRINT3_DIR = ML_DIR.parent
ARTIFACTS_DIR = ML_DIR / "artifacts"
DB_PATH = SPRINT3_DIR / "database" / "totem.db"


@dataclass
class TrainOutputs:
    model_name: str
    model_version: str
    trained_at: str
    rows_total: int
    rows_used: int
    classes_order: list[str]

    # baseline (comparação)
    baseline_accuracy: float
    baseline_f1_macro: float

    # RF FULL (modelo principal)
    rf_full_accuracy: float
    rf_full_f1_macro: float

    # RF NO DURATION (sanity check)
    rf_no_duration_accuracy: float
    rf_no_duration_f1_macro: float

    # features
    features_full: list[str]
    features_no_duration: list[str]

    notes: str


def iso_now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def build_target(duration_s: int) -> str:
    """
    Target em 3 classes:
    - quick:  <= 5s
    - normal: 6–20s
    - engaged: >= 21s
    """
    if duration_s <= 5:
        return "quick"
    if 6 <= duration_s <= 20:
        return "normal"
    return "engaged"


def load_dataset() -> pd.DataFrame:
    """
    Lê dados do SQLite e retorna DataFrame com colunas necessárias.
    Usa a view v_features (se existir), senão cai para interactions.
    """
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)

        # Tenta usar a view de features (melhor para ML)
        try:
            df = pd.read_sql_query(
                """
                SELECT
                    interaction_id,
                    presence,
                    touch,
                    voice_detected,
                    duration_s,
                    hour,
                    weekday,
                    is_peak_hour
                FROM v_features
                """,
                conn,
            )
            df.rename(columns={"interaction_id": "id"}, inplace=True)
        except Exception:
            # Fallback: tabela crua (sem hour/weekday)
            df = pd.read_sql_query(
                """
                SELECT
                    id,
                    presence,
                    touch,
                    voice_detected,
                    duration_s
                FROM interactions
                WHERE is_valid = 1
                """,
                conn,
            )
            # cria features simples para não quebrar
            df["hour"] = 0
            df["weekday"] = 0
            df["is_peak_hour"] = 0

        return df
    finally:
        conn.close()


def ensure_min_rows(df: pd.DataFrame, min_rows: int = 60) -> None:
    if len(df) < min_rows:
        raise RuntimeError(
            f"Poucos dados para treinar com segurança (rows={len(df)}). "
            f"Rode o simulador até ter pelo menos {min_rows} (ideal 300+)."
        )


def prepare_xy(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    FULL: inclui duration_s
    """
    y = df["duration_s"].astype(int).apply(build_target)

    X = df[["presence", "touch", "voice_detected", "duration_s", "hour", "weekday", "is_peak_hour"]].copy()

    for col in ["presence", "touch", "voice_detected", "is_peak_hour"]:
        X[col] = X[col].astype(int).clip(0, 1)

    X["duration_s"] = X["duration_s"].astype(int).clip(0, 3600)
    X["hour"] = X["hour"].astype(int).clip(0, 23)
    X["weekday"] = X["weekday"].astype(int).clip(0, 6)

    return X, y


def prepare_xy_no_duration(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Sanity check: remove duration_s
    """
    y = df["duration_s"].astype(int).apply(build_target)

    X = df[["presence", "touch", "voice_detected", "hour", "weekday", "is_peak_hour"]].copy()

    for col in ["presence", "touch", "voice_detected", "is_peak_hour"]:
        X[col] = X[col].astype(int).clip(0, 1)

    X["hour"] = X["hour"].astype(int).clip(0, 23)
    X["weekday"] = X["weekday"].astype(int).clip(0, 6)

    return X, y


def save_confusion_matrix_png(cm: np.ndarray, labels: list[str], out_path: Path, title: str) -> None:
    fig = plt.figure()
    plt.imshow(cm)
    plt.title(title)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.xticks(range(len(labels)), labels, rotation=45, ha="right")
    plt.yticks(range(len(labels)), labels)

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, str(cm[i, j]), ha="center", va="center")

    plt.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def train_and_eval_rf(
    X: pd.DataFrame,
    y: pd.Series,
    classes_order: List[str],
    *,
    label: str,
) -> Dict[str, Any]:
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=SEED,
        stratify=y,
    )

    rf = RandomForestClassifier(
        n_estimators=250,
        random_state=SEED,
        max_depth=None,
        min_samples_split=4,
        min_samples_leaf=2,
        n_jobs=-1,
    )

    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    f1m = float(f1_score(y_test, y_pred, average="macro"))
    rep = classification_report(y_test, y_pred, digits=4, zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=classes_order)

    return {
        "label": label,
        "model": rf,
        "accuracy": acc,
        "f1_macro": f1m,
        "report": rep,
        "cm": cm,
        "test_size": int(len(y_test)),
    }


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    print("== Sprint 3 | ML Train ==")
    print(f"DB: {DB_PATH}")
    print(f"Artifacts: {ARTIFACTS_DIR}")

    df = load_dataset()
    rows_total = len(df)
    print(f"Rows loaded: {rows_total}")

    df = df.dropna(subset=["presence", "touch", "voice_detected", "duration_s"])
    rows_used = len(df)

    ensure_min_rows(df, min_rows=60)

    X_full, y_full = prepare_xy(df)

    classes_order = ["engaged", "normal", "quick"]

    # Baseline
    X_train_b, X_test_b, y_train_b, y_test_b = train_test_split(
        X_full,
        y_full,
        test_size=0.20,
        random_state=SEED,
        stratify=y_full,
    )

    baseline = DummyClassifier(strategy="most_frequent", random_state=SEED)
    baseline.fit(X_train_b, y_train_b)
    y_pred_base = baseline.predict(X_test_b)

    baseline_acc = float(accuracy_score(y_test_b, y_pred_base))
    baseline_f1 = float(f1_score(y_test_b, y_pred_base, average="macro"))

    print("\n--- Baseline (DummyClassifier: most_frequent) ---")
    print(f"Accuracy: {baseline_acc:.4f}")
    print(f"F1 macro:  {baseline_f1:.4f}")

    # RF FULL
    res_full = train_and_eval_rf(X_full, y_full, classes_order, label="rf_full")

    print("\n--- RandomForestClassifier (FULL: com duration_s) ---")
    print(f"Accuracy: {res_full['accuracy']:.4f}")
    print(f"F1 macro:  {res_full['f1_macro']:.4f}")
    print("\nClassification report (FULL):")
    print(res_full["report"])

    cm_full_path = ARTIFACTS_DIR / "confusion_matrix.png"
    save_confusion_matrix_png(res_full["cm"], classes_order, cm_full_path, title="Confusion Matrix (RF FULL)")

    # RF NO DURATION
    X_nd, y_nd = prepare_xy_no_duration(df)
    res_nd = train_and_eval_rf(X_nd, y_nd, classes_order, label="rf_no_duration")

    print("\n--- RandomForestClassifier (NO duration_s) [Sanity Check] ---")
    print(f"Accuracy: {res_nd['accuracy']:.4f}")
    print(f"F1 macro:  {res_nd['f1_macro']:.4f}")
    print("\nClassification report (NO duration_s):")
    print(res_nd["report"])

    cm_nd_path = ARTIFACTS_DIR / "confusion_matrix_no_duration.png"
    save_confusion_matrix_png(res_nd["cm"], classes_order, cm_nd_path, title="Confusion Matrix (RF NO duration_s)")

    # Save model principal (FULL)
    model_path = ARTIFACTS_DIR / "model.pkl"
    joblib.dump(
        {
            "model": res_full["model"],
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "trained_at": iso_now_utc(),
            "features": list(X_full.columns),
            "classes": classes_order,
            "seed": SEED,
        },
        model_path,
    )

    outputs = TrainOutputs(
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        trained_at=iso_now_utc(),
        rows_total=rows_total,
        rows_used=rows_used,
        classes_order=classes_order,
        baseline_accuracy=baseline_acc,
        baseline_f1_macro=baseline_f1,
        rf_full_accuracy=float(res_full["accuracy"]),
        rf_full_f1_macro=float(res_full["f1_macro"]),
        rf_no_duration_accuracy=float(res_nd["accuracy"]),
        rf_no_duration_f1_macro=float(res_nd["f1_macro"]),
        features_full=list(X_full.columns),
        features_no_duration=list(X_nd.columns),
        notes=(
            "Sanity check incluído: treino adicional removendo duration_s para avaliar robustez "
            "quando a feature mais determinística do target não está presente. "
            "Em dados simulados, duration_s tende a dominar a separação das classes."
        ),
    )

    metrics_path = ARTIFACTS_DIR / "metrics.json"
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(asdict(outputs), f, ensure_ascii=False, indent=2)

    print("\n== Artifacts gerados ==")
    print(f"- {model_path}")
    print(f"- {metrics_path}")
    print(f"- {cm_full_path}")
    print(f"- {cm_nd_path}")
    print("\nTreino concluído com sucesso ✅")


if __name__ == "__main__":
    main()
