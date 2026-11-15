"""Collecte et sauvegarde des données historiques pour D02."""

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

import pandas as pd
import yfinance as yf


# Racine du projet, indépendamment du dossier depuis lequel on lance Python.
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_config():
    """Lire les paramètres du fichier JSON."""

    config_path = PROJECT_ROOT / "configs" / "data_config.json"

    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    if pd.Timestamp(config["start"]) >= pd.Timestamp(config["end_exclusive"]):
        raise ValueError("La date de début doit précéder la date de fin.")

    return config


def download_data(config):
    """Télécharger les données sans nettoyage automatique des anomalies."""

    df = yf.download(
        tickers=config["symbol"],
        start=config["start"],
        end=config["end_exclusive"],
        interval=config["interval"],
        auto_adjust=config["auto_adjust"],
        actions=True,
        keepna=True,
        repair=False,
        ignore_tz=True,
        multi_level_index=False,
        progress=False,
        threads=False,
        timeout=30
    )

    # Le fournisseur peut renvoyer un tableau vide en cas d'échec.
    if df is None or df.empty:
        raise RuntimeError(
            "Aucune donnée reçue. Vérifie la connexion, "
            "le symbole et la disponibilité de Yahoo Finance."
        )

    required_columns = {"Open", "High", "Low", "Close", "Volume"}

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Colonnes obligatoires absentes : {sorted(missing_columns)}"
        )

    # L'index contient les dates des séances.
    # On en fait une colonne pour faciliter la sauvegarde et la relecture.
    df = df.rename_axis("Date").reset_index()

    return df


def save_snapshot(df, config):
    """Conserver un CSV daté et les informations de provenance."""

    acquisition_time = datetime.now(timezone.utc)
    folder_name = acquisition_time.strftime("%Y%m%dT%H%M%S%fZ")

    folder = (
        PROJECT_ROOT
        / "data"
        / "raw"
        / f"{config['symbol']}_{folder_name}"
    )

    # Chaque exécution crée un nouveau dossier.
    folder.mkdir(parents=True, exist_ok=False)

    csv_path = folder / f"{config['symbol']}_daily.csv"

    df.to_csv(
        csv_path,
        index=False,
        date_format="%Y-%m-%d",
        encoding="utf-8"
    )

    # Empreinte du fichier : permet de détecter une modification ultérieure.
    checksum = hashlib.sha256(csv_path.read_bytes()).hexdigest()

    metadata = {
        "source": config["source"],
        "symbol": config["symbol"],
        "interval": config["interval"],
        "requested_start_inclusive": config["start"],
        "requested_end_exclusive": config["end_exclusive"],
        "observed_first_date": df["Date"].min().strftime("%Y-%m-%d"),
        "observed_last_date": df["Date"].max().strftime("%Y-%m-%d"),
        "acquired_at_utc": acquisition_time.isoformat(),
        "rows": len(df),
        "columns": df.columns.tolist(),
        "currency": "USD",
        "volume_unit": "Parts de GLD échangées",
        "market_timezone": "America/New_York",
        "date_convention": (
            "Date de séance sans heure ni fuseau dans le CSV ; "
            "ne représente pas un instant de disponibilité."
        ),
        "auto_adjust": config["auto_adjust"],
        "adjustment_convention": (
            "OHLC ajustés par yfinance"
            if config["auto_adjust"]
            else "OHLC sans ajustement automatique"
        ),
        "actions_requested": True,
        "keepna": True,
        "repair": False,
        "quality_audit_status": "À réaliser",
        "config": config,
        "versions": {
            "pandas": pd.__version__,
            "yfinance": yf.__version__
        },
        "csv_file": csv_path.name,
        "sha256": checksum
    }

    metadata_path = folder / "metadata.json"

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, ensure_ascii=False)

    return csv_path


def load_snapshot(csv_path):
    """Recharger les données sauvegardées, sans accès à Internet."""

    return pd.read_csv(csv_path, parse_dates=["Date"])


def main():
    config = load_config()

    print(f"Téléchargement de {config['symbol']}...")
    df = download_data(config)

    csv_path = save_snapshot(df, config)

    # Vérifier que le fichier sauvegardé peut être relu.
    reloaded_df = load_snapshot(csv_path)

    if len(reloaded_df) != len(df):
        raise RuntimeError("Le nombre de lignes a changé après sauvegarde.")

    print("\nPremières observations :")
    print(reloaded_df.head())

    print(f"\nNombre de lignes : {len(reloaded_df)}")
    print(f"Première séance : {reloaded_df['Date'].min().date()}")
    print(f"Dernière séance : {reloaded_df['Date'].max().date()}")
    print(f"\nFichier sauvegardé : {csv_path}")

        # Réaliser les premiers contrôles qualité.
    quality_report = audit_data(reloaded_df)

    print("\nContrôles qualité :")
    print(quality_report.to_string(index=False))

    # Un sous-dossier par snapshot permet de relier audit et données.
    report_folder = PROJECT_ROOT / "reports" / csv_path.parent.name
    report_folder.mkdir(parents=True, exist_ok=True)

    report_path = report_folder / "quality_checks.csv"

    quality_report.to_csv(
        report_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\nRapport sauvegardé : {report_path}")


def audit_data(df):
    """Vérifier les données sans les modifier."""

    prices = df[["Open", "High", "Low", "Close"]]

    # Un maximum doit être supérieur ou égal aux autres prix.
    invalid_high = (
        (df["High"] < df["Open"])
        | (df["High"] < df["Close"])
        | (df["High"] < df["Low"])
    )

    # Un minimum doit être inférieur ou égal aux autres prix.
    invalid_low = (
        (df["Low"] > df["Open"])
        | (df["Low"] > df["Close"])
        | (df["Low"] > df["High"])
    )

    checks = {
        "Lignes avec au moins une valeur manquante":
            int(df.isna().any(axis=1).sum()),

        "Dates dupliquées supplémentaires":
            int(df["Date"].duplicated().sum()),

        "Ordre chronologique incorrect":
            int(not df["Date"].is_monotonic_increasing),

        "Lignes avec un prix nul ou négatif":
            int((prices <= 0).any(axis=1).sum()),

        "Lignes avec un High incohérent":
            int(invalid_high.sum()),

        "Lignes avec un Low incohérent":
            int(invalid_low.sum()),

        "Lignes avec un volume négatif":
            int((df["Volume"] < 0).sum()),

        "Lignes avec un volume nul — à examiner":
            int((df["Volume"] == 0).sum())
    }

    report = pd.DataFrame(
        checks.items(),
        columns=["Controle", "Nombre"]
    )

    return report

if __name__ == "__main__":
    main()