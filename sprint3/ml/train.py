from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

import joblib
import numpy as np
import pandas as pd
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
MODEL_VERSION = "rf_v1"
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
    classes: list[str]
    baseline_accuracy: float
    baseline_f1_macro: float
    rf_accuracy: float
    rf_f1_macro: float
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
    """
    Para treinar 3 classes com split, precisamos de um mínimo razoável.
    Para nota máxima, o ideal é 300+ (como você já planejou),
    mas aqui travamos num mínimo técnico para evitar treino inválido.
    """
    if len(df) < min_rows:
        raise RuntimeError(
            f"Poucos dados para treinar com segurança (rows={len(df)}). "
            f"Rode o simulador até ter pelo menos {min_rows} (ideal 300+)."
        )


def prepare_xy(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Cria features (X) e target (y).
    """
    # Target
    y = df["duration_s"].astype(int).apply(build_target)

    # Features
    X = df[["presence", "touch", "voice_detected", "duration_s", "hour", "weekday", "is_peak_hour"]].copy()

    # Normalização defensiva de 0/1
    for col in ["presence", "touch", "voice_detected", "is_peak_hour"]:
        X[col] = X[col].astype(int).clip(0, 1)

    # duration_s sempre >=0
    X["duration_s"] = X["duration_s"].astype(int).clip(0, 3600)

    # hour/weekday limites
    X["hour"] = X["hour"].astype(int).clip(0, 23)
    X["weekday"] = X["weekday"].astype(int).clip(0, 6)

    return X, y


def save_confusion_matrix_png(cm: np.ndarray, labels: list[str], out_path: Path) -> None:
    """
    Salva confusion matrix como PNG.
    """
    fig = plt.figure()
    plt.imshow(cm)
    plt.title("Confusion Matrix (RandomForest)")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.xticks(range(len(labels)), labels, rotation=45, ha="right")
    plt.yticks(range(len(labels)), labels)

    # números nas células
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, str(cm[i, j]), ha="center", va="center")

    plt.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    print("== Sprint 3 | ML Train ==")
    print(f"DB: {DB_PATH}")
    print(f"Artifacts: {ARTIFACTS_DIR}")

    df = load_dataset()
    rows_total = len(df)
    print(f"Rows loaded: {rows_total}")

    # remove possíveis nulos
    df = df.dropna(subset=["presence", "touch", "voice_detected", "duration_s"])
    rows_used = len(df)

    ensure_min_rows(df, min_rows=60)

    X, y = prepare_xy(df)
    classes = sorted(y.unique().tolist())

    # Split estratificado para manter proporção das classes
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=SEED,
        stratify=y,
    )

    # -------------------------
    # Baseline
    # -------------------------
    baseline = DummyClassifier(strategy="most_frequent", random_state=SEED)
    baseline.fit(X_train, y_train)
    y_pred_base = baseline.predict(X_test)

    baseline_acc = float(accuracy_score(y_test, y_pred_base))
    baseline_f1 = float(f1_score(y_test, y_pred_base, average="macro"))

    print("\n--- Baseline (DummyClassifier: most_frequent) ---")
    print(f"Accuracy: {baseline_acc:.4f}")
    print(f"F1 macro:  {baseline_f1:.4f}")

    # -------------------------
    # Modelo principal: RF
    # -------------------------
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

    rf_acc = float(accuracy_score(y_test, y_pred))
    rf_f1 = float(f1_score(y_test, y_pred, average="macro"))

    print("\n--- RandomForestClassifier ---")
    print(f"Accuracy: {rf_acc:.4f}")
    print(f"F1 macro:  {rf_f1:.4f}")

    print("\nClassification report:")
    print(classification_report(y_test, y_pred, digits=4))

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=classes)
    cm_path = ARTIFACTS_DIR / "confusion_matrix.png"
    save_confusion_matrix_png(cm, classes, cm_path)

    # Salvando modelo
    model_path = ARTIFACTS_DIR / "model.pkl"
    joblib.dump(
        {
            "model": rf,
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "trained_at": iso_now_utc(),
            "features": list(X.columns),
            "classes": classes,
            "seed": SEED,
        },
        model_path,
    )

    # Salvando métricas
    outputs = TrainOutputs(
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        trained_at=iso_now_utc(),
        rows_total=rows_total,
        rows_used=rows_used,
        classes=classes,
        baseline_accuracy=baseline_acc,
        baseline_f1_macro=baseline_f1,
        rf_accuracy=rf_acc,
        rf_f1_macro=rf_f1,
        notes=(
            "Target derivado por regra de duration_s em 3 classes (quick/normal/engaged). "
            "Dados são simulados; métricas podem variar com o volume e distribuição."
        ),
    )

    metrics_path = ARTIFACTS_DIR / "metrics.json"
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(asdict(outputs), f, ensure_ascii=False, indent=2)

    print("\n== Artifacts gerados ==")
    print(f"- {model_path}")
    print(f"- {metrics_path}")
    print(f"- {cm_path}")
    print("\nTreino concluído com sucesso ✅")


if __name__ == "__main__":
    main()
