"""Audit D02 des séances de GLD. À placer dans src/audit_d02.py.

Dans le notebook déjà relié au projet, utiliser

    from src.audit_d02 import audit_snapshot
    anomalies, manquantes, rapport = audit_snapshot(csv_path, PROJECT_ROOT / "reports")

Le snapshot se compose de GLD_daily.csv et du metadata.json écrit par src/data.py.
"""

from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pandas_market_calendars as mcal


PRIX = ["Open", "High", "Low", "Close"]
OPERATIONS = ["Dividends", "Stock Splits", "Capital Gains"]


def relever_anomalies(brut, dates, attendues, debut, fin_exclue):
    """Conserver une ligne par signalement, avec les valeurs d'origine du CSV."""
    signalements = []
    entete = ["Ligne_CSV", "Date", "Motif", "Champ", "Suite_proposee"]
    autres_colonnes = [nom for nom in brut.columns if nom != "Date"]

    def signaler(masque, motif, champ, suite):
        if masque.any():
            lignes = brut.loc[masque].copy()
            # L'en-tête occupe la ligne 1. La première observation est en ligne 2.
            lignes["Ligne_CSV"] = lignes.index + 2
            lignes["Motif"] = motif
            lignes["Champ"] = champ
            lignes["Suite_proposee"] = suite
            signalements.append(lignes[entete + autres_colonnes])

    # 1. Vérifier les dates dans l'ordre du CSV, avant tout tri.
    valide = dates.notna()
    dans_periode = dates.ge(debut) & dates.lt(fin_exclue)
    recul = dates.dropna().diff().lt(pd.Timedelta(0)).reindex(brut.index, fill_value=False)
    signaler(~valide, "Date absente ou illisible", "Date", "Retrouver la date dans la source.")
    signaler(valide & dates.duplicated(keep=False), "Date dupliquée", "Date",
             "Comparer toutes les lignes de cette séance avant de choisir celle à retenir.")
    signaler(recul, "Date antérieure à la précédente", "Date",
             "Vérifier la date puis trier une copie avant le calcul des rendements.")
    signaler(valide & ~dans_periode, "Date hors période demandée", "Date",
             "Vérifier les bornes de collecte.")
    signaler(dans_periode & ~dates.isin(attendues), "Date hors calendrier de séance", "Date",
             "Vérifier la date de marché et la ligne dans la source.")

    # 2. Lire les nombres dans une copie. Les valeurs affichées restent celles du CSV.
    champs = PRIX + ["Volume"] + [c for c in OPERATIONS if c in brut]
    nombres = brut[champs].apply(pd.to_numeric, errors="coerce")
    nombres = nombres.replace([float("inf"), float("-inf")], float("nan"))
    for champ in champs:
        manque = brut[champ].str.strip().str.lower().isin(["", "na", "n/a", "nan", "null", "none", "<na>"])
        signaler(manque, "Valeur manquante", champ, "Consulter la valeur publiée pour cette séance.")
        signaler(nombres[champ].isna() & ~manque, "Valeur non numérique ou infinie", champ,
                 "Vérifier la valeur et son format dans la source.")
    for champ in PRIX:
        signaler(nombres[champ].le(0), "Prix nul ou négatif", champ,
                 "Contrôler le prix ajusté auprès de la source.")

    # 3. High et Low doivent encadrer les autres prix de la même séance.
    high_invalide = nombres.High.lt(nombres[["Open", "Close", "Low"]].max(axis=1))
    low_invalide = nombres.Low.gt(nombres[["Open", "Close", "High"]].min(axis=1))
    signaler(high_invalide, "High incohérent", "High", "Comparer les quatre prix de la séance.")
    signaler(low_invalide, "Low incohérent", "Low", "Comparer les quatre prix de la séance.")
    signaler(nombres.Volume.lt(0), "Volume négatif", "Volume", "Vérifier le volume publié.")
    signaler(nombres.Volume.eq(0), "Volume nul à examiner", "Volume",
             "Conserver l'observation et vérifier l'activité de cette séance.")

    if not signalements:
        return pd.DataFrame(columns=entete + autres_colonnes)
    return pd.concat(signalements, ignore_index=True).sort_values(
        ["Ligne_CSV", "Motif", "Champ"], ignore_index=True
    )


def audit_snapshot(csv_path, reports_root):
    """Relire le CSV et ses métadonnées. Renvoyer les signalements, les lacunes et le rapport."""
    csv_path = Path(csv_path)
    meta = json.loads(csv_path.with_name("metadata.json").read_text(encoding="utf-8-sig"))
    if meta["symbol"] != "GLD" or meta["interval"] != "1d":
        raise ValueError("Cet audit utilise les séances journalières de GLD.")

    debut = pd.Timestamp(meta["requested_start_inclusive"])
    fin_exclue = pd.Timestamp(meta["requested_end_exclusive"])
    if pd.isna(debut) or pd.isna(fin_exclue) or debut >= fin_exclue:
        raise ValueError("Vérifier les bornes de la période dans metadata.json.")
    dernier_jour = fin_exclue - pd.Timedelta(days=1)

    contenu = csv_path.read_bytes()
    brut = pd.read_csv(BytesIO(contenu), dtype=str, keep_default_na=False,
                       skip_blank_lines=False, encoding="utf-8-sig")
    obligatoires = {"Date", "Volume", *PRIX}
    absentes = sorted(obligatoires.difference(brut.columns))
    if absentes:
        raise ValueError(f"Colonnes absentes du CSV : {', '.join(absentes)}")

    # Une date du CSV représente la séance à New York. Les deux séries sont
    # comparées comme dates civiles, sans convertir un minuit UTC en veille locale.
    dates = pd.to_datetime(brut["Date"].str.strip(), format="%Y-%m-%d", errors="coerce")
    calendrier = mcal.get_calendar("NYSE")
    attendues = calendrier.valid_days(debut, dernier_jour, tz=None)
    observees = pd.DatetimeIndex(dates.dropna().unique())
    presentes = attendues.intersection(observees)
    lacunes = attendues.difference(observees)
    manquantes = pd.DataFrame({"Date": lacunes.strftime("%Y-%m-%d")})
    anomalies = relever_anomalies(brut, dates, attendues, debut, fin_exclue)

    # Une même ligne peut avoir plusieurs motifs. Une date absente n'a pas de ligne CSV.
    nb_lignes_signalees = anomalies["Ligne_CSV"].nunique()
    empreinte = sha256(contenu).hexdigest()
    reference = meta.get("sha256")
    if not reference:
        integrite = "Empreinte de collecte absente des métadonnées."
    elif empreinte == reference:
        integrite = "Le CSV correspond à l’empreinte enregistrée lors de la collecte."
    else:
        integrite = "**Le contenu du CSV diffère de l’empreinte de collecte. Vérifier sa version.**"

    lignes = [
        "# D02 — Conclusion de l’audit de GLD",
        "",
        f"Le fichier `{csv_path.parent.name}/{csv_path.name}` a été relu localement.",
        f"La fenêtre demandée va du {debut:%d/%m/%Y} au {dernier_jour:%d/%m/%Y} inclus.",
        integrite,
        "",
        "| Indicateur | Résultat |",
        "|---|---:|",
        f"| Observations lues dans le CSV | {len(brut)} |",
        f"| Séances attendues selon le calendrier NYSE | {len(attendues)} |",
        f"| Séances attendues présentes au moins une fois | {len(presentes)} |",
        f"| Séances attendues absentes | {len(manquantes)} |",
        f"| Lignes distinctes à examiner | {nb_lignes_signalees} |",
        f"| Signalements sur ces lignes | {len(anomalies)} |",
        "",
    ]
    if len(presentes):
        lignes.append(f"La première séance attendue présente est celle du {presentes.min():%d/%m/%Y} "
                      f"et la dernière celle du {presentes.max():%d/%m/%Y}.")
    if anomalies.empty:
        lignes.append("Les contrôles de dates, de valeurs, de prix OHLC et de volume "
                      "n’ont signalé aucune ligne du CSV.")
    else:
        lignes.extend(["", "| Motif relevé | Lignes distinctes concernées |", "|---|---:|"])
        for motif, nombre in anomalies.groupby("Motif")["Ligne_CSV"].nunique().items():
            lignes.append(f"| {motif} | {nombre} |")
        lignes.extend(["", "Chaque signalement figure dans `anomalies.csv` avec la date lue, "
                       "le numéro de ligne, les valeurs d’origine et la vérification proposée."])
    if manquantes.empty:
        lignes.append("Toutes les dates de séance attendues figurent dans le CSV.")
    else:
        lignes.append("Les dates de séance absentes figurent dans `seances_manquantes.csv`. "
                      "Vérifier ces dates auprès de la source avant de calculer des rendements entre séances.")
    lignes.extend([
        "", "Le snapshot brut a été conservé. La comparaison porte sur les dates d’ouverture "
        "du marché, y compris les séances écourtées. Une séance présente peut contenir un prix à vérifier.",
        "", f"Calendrier NYSE de pandas_market_calendars {mcal.__version__}. "
        f"Lecture avec pandas {pd.__version__}.",
        f"Empreinte SHA-256 du CSV examiné `{empreinte}`.", ""
    ])

    dossier = Path(reports_root) / csv_path.parent.name
    dossier.mkdir(parents=True, exist_ok=True)
    rapport = dossier / "conclusion_audit.md"
    # Préparer tous les résultats avant de remplacer les exports de ce snapshot.
    with TemporaryDirectory(dir=dossier) as temporaire:
        staging = Path(temporaire)
        anomalies.to_csv(staging / "anomalies.csv", index=False, encoding="utf-8-sig")
        manquantes.to_csv(staging / "seances_manquantes.csv", index=False, encoding="utf-8-sig")
        (staging / rapport.name).write_text("\n".join(lignes), encoding="utf-8")
        for nom in ("anomalies.csv", "seances_manquantes.csv", rapport.name):
            (staging / nom).replace(dossier / nom)
    return anomalies, manquantes, rapport


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Auditer un snapshot GLD local avec son calendrier de séances.")
    parser.add_argument("csv", type=Path, help="Chemin du GLD_daily.csv à auditer")
    parser.add_argument("--rapports", type=Path, default=Path(__file__).resolve().parents[1] / "reports",
                        help="Dossier racine des rapports du projet")
    args = parser.parse_args()
    _, _, rapport = audit_snapshot(args.csv, args.rapports)
    print(rapport.read_text(encoding="utf-8"))
    print(f"Rapport enregistré dans {rapport}")
