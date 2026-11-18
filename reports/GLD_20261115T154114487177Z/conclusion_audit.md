# D02 — Conclusion de l’audit de GLD

Le fichier `GLD_20261115T154114487177Z/GLD_daily.csv` a été relu localement.
La fenêtre demandée va du 01/01/2018 au 30/10/2026 inclus.
Le CSV correspond à l’empreinte enregistrée lors de la collecte.

| Indicateur | Résultat |
|---|---:|
| Observations lues dans le CSV | 2220 |
| Séances attendues selon le calendrier NYSE | 2220 |
| Séances attendues présentes au moins une fois | 2220 |
| Séances attendues absentes | 0 |
| Lignes distinctes à examiner | 0 |
| Signalements sur ces lignes | 0 |

La première séance attendue présente est celle du 02/01/2018 et la dernière celle du 30/10/2026.
Les contrôles de dates, de valeurs, de prix OHLC et de volume n’ont signalé aucune ligne du CSV.
Toutes les dates de séance attendues figurent dans le CSV.

Le snapshot brut a été conservé. La comparaison porte sur les dates d’ouverture du marché, y compris les séances écourtées. Une séance présente peut contenir un prix à vérifier.

Calendrier NYSE de pandas_market_calendars 5.6.1. Lecture avec pandas 2.3.3.
Empreinte SHA-256 du CSV examiné `252ced6250c58139a01ea8493eedba65a876be593fe21ba94f6d416ff53f70fa`.
