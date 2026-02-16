from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from database.db import get_conn, init_db, fetch_unpredicted, insert_prediction


# Paths robustos
ML_DIR = Path(__file__).resolve().parent
SPRINT3_DIR = ML_DIR.parent
ARTIFACTS_DIR = ML_DIR / "artifacts"
DB_PATH = SPRINT3_DIR / "database" / "totem.db"
MODEL_PATH = ARTIFACTS_DIR / "model.pkl"


def iso_now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_model_bundle(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Modelo não encontrado: {path}. Rode primeiro: python -m ml.train")
    bundle = joblib.load(path)
    if "model" not in bundle:
        raise ValueError("Arquivo model.pkl inválido: chave 'model' não encontrada.")
    return bundle


def rows_to_dataframe(rows) -> pd.DataFrame:
    """
    Converte sqlite3.Row list em DataFrame.
    """
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


def prepare_features(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """
    Garante que o DF tenha todas as colunas esperadas pelo modelo.
    Como estamos prevendo em cima de dados brutos, precisamos criar hour/weekday/is_peak_hour se faltarem.
    """
    # Se o modelo foi treinado com hour/weekday/is_peak_hour, mas fetch_unpredicted não traz,
    # a gente cria defaults simples (0). (Você pode evoluir depois pegando v_features na query)
    for col in features:
        if col not in df.columns:
            df[col] = 0

    # Normalizações defensivas
    for c in ["presence", "touch", "voice_detected", "is_peak_hour"]:
        if c in df.columns:
            df[c] = df[c].fillna(0).astype(int).clip(0, 1)

    if "duration_s" in df.columns:
        df["duration_s"] = df["duration_s"].fillna(0).astype(int).clip(0, 3600)

    if "hour" in df.columns:
        df["hour"] = df["hour"].fillna(0).astype(int).clip(0, 23)

    if "weekday" in df.columns:
        df["weekday"] = df["weekday"].fillna(0).astype(int).clip(0, 6)

    return df[features].copy()


def predict_batch(
    model_bundle: Dict[str, Any],
    rows,
) -> List[Tuple[int, str, Optional[float]]]:
    """
    Retorna lista de (interaction_id, label, proba)
    """
    model = model_bundle["model"]
    features = model_bundle.get("features") or ["presence", "touch", "voice_detected", "duration_s", "hour", "weekday", "is_peak_hour"]
    classes = model_bundle.get("classes")

    df = rows_to_dataframe(rows)
    if df.empty:
        return []

    X = prepare_features(df, features)

    # Predições
    y_pred = model.predict(X)

    # Probabilidade (se disponível)
    proba = None
    y_proba = None
    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X)

    results: List[Tuple[int, str, Optional[float]]] = []
    for idx, row in df.iterrows():
        interaction_id = int(row["id"])
        label = str(y_pred[idx])

        p: Optional[float] = None
        if y_proba is not None:
            # pega prob da classe prevista
            # classes_ é a ordem do predict_proba
            model_classes = list(model.classes_)
            class_index = model_classes.index(label) if label in model_classes else None
            if class_index is not None:
                p = float(y_proba[idx][class_index])

        results.append((interaction_id, label, p))

    return results


def main(limit: int = 500, model_version_override: Optional[str] = None) -> None:
    print("== Sprint 3 | ML Predict ==")
    print(f"DB: {DB_PATH}")
    print(f"Model: {MODEL_PATH}")

    model_bundle = load_model_bundle(MODEL_PATH)

    model_name = model_bundle.get("model_name", "RandomForestClassifier")
    model_version = model_bundle.get("model_version", "rf_v1")
    trained_at = model_bundle.get("trained_at")

    if model_version_override:
        model_version = model_version_override

    conn = get_conn(DB_PATH)
    try:
        init_db(conn)

        # Busca interações ainda não previstas para essa versão do modelo
        rows = fetch_unpredicted(conn, model_version=model_version, limit=limit, only_valid=True)

        if not rows:
            print("Nenhuma interação nova para prever (tudo em dia).")
            return

        print(f"Interações sem previsão encontradas: {len(rows)} (serão processadas agora)")

        preds = predict_batch(model_bundle, rows)

        inserted = 0
        for interaction_id, label, proba in preds:
            insert_prediction(
                conn,
                interaction_id=interaction_id,
                label=label,
                proba=proba,
                model_version=model_version,
                model_name=model_name,
                trained_at=trained_at,
                notes=None,
            )
            inserted += 1
            print(f"Predicted interaction_id={interaction_id} label={label} proba={proba}")

        print(f"\nPrevisões gravadas com sucesso: {inserted} ✅")

    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera previsões com o modelo treinado e grava em SQLite.")
    parser.add_argument("--limit", type=int, default=500, help="Máximo de interações a prever por execução")
    parser.add_argument("--model-version", type=str, default=None, help="Sobrescreve a versão do modelo ao gravar no DB")
    args = parser.parse_args()

    main(limit=args.limit, model_version_override=args.model_version)
