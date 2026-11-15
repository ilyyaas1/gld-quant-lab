# GLD Quant Lab — D01

## Présentation

Projet du module Trading Intelligent : développer une application Streamlit pour analyser GLD, prévoir son rendement et son risque, puis tester des stratégies en simulation avec 100 000 USD virtuels. L’application permettra d’explorer les données, comparer les modèles, gérer le risque, tester les stratégies sur le passé et suivre des opérations fictives sur de nouvelles séances.

Les décisions seront prises après clôture, avec exécution au plus tôt à l’ouverture suivante, sans levier ni vente à découvert.

## Actif étudié

- **Ticker : GLD**, exposition à l’or.
- **Benchmark : SPY**, référence de comparaison.

## Question scientifique

La gestion dynamique de l’exposition fondée sur GARCH protège-t-elle mieux le capital qu’une taille fixe ?

Nous comparerons une proportion investie fixe à une proportion adaptée à la volatilité prévue par GARCH, avec les mêmes signaux et les mêmes coûts.

## Équipe et répartition proposée

| Membre | Rôle | Tâches |
|---|---|---|
| ELBENNANI Ilyass | Données et économétrie | Collecter GLD/SPY et contrôler la qualité des données ; calculer les rendements et préparer les variables ; séparer apprentissage, validation et test ; développer les références simples et ARIMA/SARIMA/SARIMAX ; comparer les prévisions et examiner les résidus ; réaliser Market Data et la partie économétrique du Model Laboratory. |
| KIRAJ WALID | Risque, stratégie et backtest | Tester les effets ARCH et prévoir la volatilité avec GARCH ; calculer et vérifier VaR/ES ; définir les décisions et les expositions fixe/dynamique ; développer le backtest avec frais et calendrier d’exécution ; analyser rendement, pertes et drawdown ; réaliser Risk Management, Trading Strategy et Backtesting. |
| ALAOUI Rida | ML/DL et intégration | Développer un modèle linéaire régularisé, un modèle arborescent et un MLP ; comparer les prévisions selon le protocole commun ; réaliser la partie ML/DL du Model Laboratory ; organiser la navigation Streamlit et intégrer les vues de chaque membre ; préparer le mode démonstration hors connexion. |
| Toute l’équipe | Travail commun | Réaliser le paper trading et le suivi du portefeuille ; définir les formats communs et vérifier l’absence de fuite d’information ; tester et documenter chaque module ; relire le code ; préparer le rapport et la soutenance. |

## Diagramme de l’application

![Diagramme de l’application](images/DiagrammeApplication.png)


## Organisation du livrable D02

D02 prépare les données nécessaires aux futures étapes du projet :
collecte, conservation, documentation et contrôle de qualité.

### Fichiers de code et de configuration

| Fichier | Rôle | Contenu |
|---|---|---|
| `src/data.py` | Regroupe les fonctions réutilisables de gestion des données | Lecture de la configuration, téléchargement de GLD, sauvegarde, rechargement et premiers contrôles qualité |
| `configs/data_config.json` | Centralise les paramètres de l’étude | Symbole GLD, source, fréquence, dates, convention d’ajustement et frontières des périodes train/validation/test |
| `requirements.txt` | Liste les bibliothèques nécessaires à l’exécution | Notamment pandas, yfinance et matplotlib, ainsi que les dépendances du notebook selon l’environnement |
| `.gitignore` | Indique à Git les fichiers locaux à ne pas versionner | Environnement virtuel, caches Python et checkpoints Jupyter |

Les dates train/validation/test sont définies à l’avance dans la configuration.
Aucun modèle n’est entraîné dans D02.

### Notebook d’analyse

| Fichier | Rôle | Contenu |
|---|---|---|
| `notebooks/02_data_audit.ipynb` | Présente la démarche étape par étape | Explications Markdown, chargement d’un snapshot précis, provenance, contrôles, graphiques et interprétation |

Le notebook appelle les fonctions de `src/data.py`.
Il ne contient pas une deuxième copie de leur implémentation.

Cette séparation permet de réutiliser ensuite les mêmes fonctions
dans l’application Streamlit.

### Données sauvegardées

Chaque collecte crée un nouveau dossier :
`data/raw/GLD_<horodatage>/`.

L’horodatage correspond à la date et à l’heure UTC d’acquisition.
Il ne représente pas la période couverte par les données.

| Fichier | Rôle | Contenu |
|---|---|---|
| `data/raw/GLD_<horodatage>/GLD_daily.csv` | Conserve le snapshot utilisé pour l’analyse | Une ligne par séance reçue, avec Date, OHLCV et les colonnes d’opérations sur le fonds disponibles |
| `data/raw/GLD_<horodatage>/metadata.json` | Documente précisément ce snapshot | Source, symbole, période demandée, période observée, date d’acquisition, unités, ajustement, paramètres, versions et empreinte SHA-256 |

Le dossier `raw` contient ici les données retournées par yfinance
avant notre propre nettoyage. Les prix sont déjà ajustés lorsque
`auto_adjust=True`.

Le CSV permet de refaire l’analyse sans connexion à Yahoo Finance.

L’empreinte SHA-256 permet de vérifier si le fichier CSV a été modifié.
Elle ne garantit pas que les données économiques sont exactes.
La vérification de cette empreinte doit être exécutée explicitement :
sa présence dans les métadonnées ne suffit pas.

### Rapports et figures

| Fichier | Rôle | Contenu |
|---|---|---|
| `reports/GLD_<horodatage>/quality_checks.csv` | Conserve le résumé des premiers contrôles qualité | Nom de chaque contrôle et nombre de cas détectés |
| `reports/figures/GLD_<horodatage>/gld_price_volume.png` | Conserve le graphique de cohérence | Évolution de la clôture ajustée et des volumes échangés |

Le nom du sous-dossier permet de relier chaque résultat
au snapshot correspondant.

`quality_checks.csv` contient des compteurs. Il ne contient pas encore
le détail de chaque ligne problématique.

Le graphique permet une inspection visuelle. Il ne remplace pas
les contrôles numériques ni la vérification des séances manquantes.

Avec le code actuel, le rapport CSV est créé lorsque `main()` s’exécute
dans `src/data.py`. L’appel à `audit_data(df)` dans le notebook affiche
le rapport, mais ne le sauvegarde pas automatiquement.

### Documentation

| Fichier | Rôle | Contenu |
|---|---|---|
| `README.md` | Guide principal du projet | Présentation, organisation des fichiers, installation et commandes de lancement |
| `data/README.md` | Documentation spécifique aux données | Provenance, dictionnaire des colonnes, unités, convention d’ajustement, disponibilité temporelle et limites |

Le README principal explique comment utiliser le projet.
Le README du dossier data explique comment comprendre les données.

### Ordre d’utilisation

1. Installer les dépendances avec `python -m pip install -r requirements.txt`.
2. Vérifier les paramètres dans `configs/data_config.json`.
3. Exécuter `python -m src.data` pour collecter, sauvegarder et auditer.
4. Ouvrir `notebooks/02_data_audit.ipynb`.
5. Choisir explicitement le snapshot à analyser.
6. Exécuter les cellules dans l’ordre.
7. Examiner les contrôles et les graphiques.
8. Rédiger une interprétation fondée sur les résultats obtenus.

### Éléments restant à compléter

Les premiers contrôles sont implémentés, mais l’audit doit encore être
complété, notamment par :
- La vérification des séances manquantes avec un calendrier boursier adapté.
- L’identification détaillée des lignes problématiques.
- La justification des éventuels traitements appliqués.

Les modules de modèles, de risque, de stratégie, de backtest et de
paper trading seront développés dans les livrables suivants.
