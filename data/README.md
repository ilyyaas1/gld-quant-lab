# GLD Quant Lab — D01, D02 et D03

## Présentation

Projet du module **Trading Intelligent** : développer une application **Streamlit** pour analyser GLD, prévoir son rendement et son risque, puis tester des stratégies en simulation avec **100 000 USD virtuels**. L’application permettra d’explorer les données, de comparer les modèles, de gérer le risque, de tester les stratégies sur le passé et de suivre des opérations fictives sur de nouvelles séances.

Les décisions seront prises **après clôture**, avec exécution **au plus tôt à l’ouverture suivante**, sans levier ni vente à découvert.

## Actif étudié

- **Ticker : GLD**, exposition à l’or.
- **Benchmark : SPY**, référence de comparaison.

## Question scientifique

**La gestion dynamique de l’exposition fondée sur GARCH protège-t-elle mieux le capital qu’une taille fixe ?**

Nous comparerons une proportion investie fixe à une proportion adaptée à la volatilité prévue par GARCH, avec les **mêmes signaux et les mêmes coûts**. Le D03 étudie la prévision du rendement ; la comparaison des expositions appartient aux étapes ultérieures du projet.

## Équipe et répartition proposée

| Membre | Rôle | Tâches |
|---|---|---|
| **ELBENNANI Ilyass** | Données et économétrie | Collecter GLD/SPY et contrôler la qualité des données ; calculer les rendements et préparer les variables ; séparer apprentissage, validation et test ; développer les références simples et ARIMA/SARIMA/SARIMAX ; comparer les prévisions et examiner les résidus ; réaliser **Market Data** et la partie économétrique du **Model Laboratory**. |
| **KIRAJ WALID** | Risque, stratégie et backtest | Tester les effets ARCH et prévoir la volatilité avec GARCH ; calculer et vérifier VaR/ES ; définir les décisions et les expositions fixe/dynamique ; développer le backtest avec frais et calendrier d’exécution ; analyser rendement, pertes et drawdown ; réaliser **Risk Management**, **Trading Strategy** et **Backtesting**. |
| **ALAOUI Rida** | ML/DL et intégration | Développer un modèle linéaire régularisé, un modèle arborescent et un MLP ; comparer les prévisions selon le protocole commun ; réaliser la partie ML/DL du **Model Laboratory** ; organiser la navigation Streamlit et intégrer les vues de chaque membre ; préparer le mode démonstration hors connexion. |
| **Toute l’équipe** | Travail commun | Réaliser le paper trading et le suivi du portefeuille ; définir les formats communs et vérifier l’absence de fuite d’information ; tester et documenter chaque module ; relire le code ; préparer le rapport et la soutenance. |

## Diagramme de l’application

![Diagramme de l’application](images/DiagrammeApplication.png)

---

## D02 — Collecte, reproductibilité et audit des données

### Objectif du livrable

D02 permet de montrer **comment nous avons obtenu les données de GLD**, comment les recharger à l’identique et comment retrouver chaque anomalie détectée. **SPY** reste le benchmark prévu pour les comparaisons du projet.

### Données et période d’étude

Nous récupérons auprès de **Yahoo Finance**, avec `yfinance`, une observation par séance de Bourse. Chaque ligne contient la date, les quatre prix ajustés en USD par part (ouverture, maximum, minimum, clôture) et le volume en parts échangées. La colonne `Date` désigne la séance de New York. La clôture et le volume total sont connus **après la fin de cette séance**.

| Usage prévu | Période fixée dans la configuration |
|---|---|
| **Apprentissage** | Du 01/01/2018 au 31/12/2022 |
| **Validation** | Du 01/01/2023 au 31/12/2024 |
| **Test final** | Du 01/01/2025 au 30/10/2026 inclus |

Ce découpage temporel est conservé dans D03 pour éviter les comparaisons biaisées.

### Fichiers de code, de configuration et de documentation

| Fichier | Rôle dans D02 |
|---|---|
| `configs/data_config.json` | Fixe le symbole GLD, la source, la fréquence journalière, les dates et l’ajustement des prix. La date de fin exclusive `2026-10-31` inclut la séance du 30 octobre. |
| `src/data.py` | Collecte les données, crée une copie datée, puis la relit avec `load_snapshot()`. La fonction `audit_data()` calcule les compteurs des premiers contrôles. |
| `src/audit_d02.py` | Relit le CSV et ses métadonnées, compare l’empreinte SHA-256, identifie les lignes à examiner, recherche les séances manquantes et écrit la conclusion. |
| `notebooks/02_data_audit.ipynb` | Explique la démarche en Markdown, appelle les fonctions des deux modules et affiche les contrôles, les graphiques et leur interprétation pour le snapshot choisi. |
| `data/README.md` | Donne la provenance, le dictionnaire des colonnes, les unités, la convention d’ajustement et le moment où les données deviennent observables. |
| `requirements.txt` | Liste les dépendances. La collecte utilise `yfinance`, les contrôles utilisent `pandas`, la figure utilise `matplotlib` et le calendrier de référence utilise `pandas_market_calendars==5.6.1`. |
| `.gitignore` | Exclut du dépôt les fichiers locaux tels que l’environnement virtuel, les caches Python et les checkpoints Jupyter. |
| `README.md` | Présente le projet et explique comment reproduire les livrables. |

### Données sauvegardées

Chaque collecte crée un dossier `data/raw/GLD_<horodatage>/`. L’horodatage indique **quand** nous avons téléchargé les données, en UTC. Les dates du CSV indiquent **quelles séances** nous avons reçues.

| Fichier dans ce dossier | Contenu |
|---|---|
| `GLD_daily.csv` | Copie des données telles que retournées par `yfinance` avant notre propre nettoyage. Les prix sont déjà ajustés avec `auto_adjust=True`. |
| `metadata.json` | Source, paramètres, période demandée, première et dernière dates reçues, date d’acquisition, unités, versions des bibliothèques et empreinte SHA-256 du CSV. |

### Contrôles et rapports

L’audit compare les dates du CSV au calendrier des séances du NYSE sur **toute la période demandée**. Selon le calendrier utilisé dans D02, du 1er janvier 2018 au 30 octobre 2026 inclus, il y a **2 220 séances attendues**. Il faut comparer les dates une à une, car un CSV de 2 220 lignes peut contenir deux fois la même date et omettre une autre séance.

L’audit recherche aussi les dates en désordre, les valeurs manquantes ou illisibles, les prix nuls ou négatifs et les incohérences entre les prix d’une même séance. Par exemple, si `High < Close`, la ligne est signalée avec ses valeurs d’origine. Un volume négatif est signalé comme anomalie. Un volume nul est signalé pour vérification.

| Fichier produit | Créé par | Ce qu’on y trouve |
|---|---|---|
| `reports/GLD_<horodatage>/quality_checks.csv` | `python -m src.data` | Les compteurs des premiers contrôles, par type de problème. |
| `reports/GLD_<horodatage>/anomalies.csv` | `audit_snapshot()` | Pour chaque signalement, le numéro de ligne du CSV, la date lue, le motif, le champ concerné, les valeurs d’origine et la vérification proposée. Une ligne peut avoir plusieurs motifs. |
| `reports/GLD_<horodatage>/seances_manquantes.csv` | `audit_snapshot()` | Les dates précises où la Bourse était ouverte et où le CSV ne contient aucune observation. |
| `reports/GLD_<horodatage>/conclusion_audit.md` | `audit_snapshot()` | Le résultat de la vérification d’empreinte, la couverture observée, le nombre de lignes à examiner et le bilan des contrôles sur ce fichier. |
| `reports/figures/GLD_<horodatage>/gld_price_volume.png` | Notebook | Le graphique de cohérence qui rapproche la clôture ajustée et le volume de chaque séance. |

### Reproduire D02

Depuis la racine du projet, installer les dépendances dans l’environnement Python utilisé par le notebook :

```powershell
python -m pip install -r requirements.txt
```

**Pour auditer un snapshot existant**, repérer son dossier dans `data/raw/` et remplacer `GLD_<horodatage>` par son nom exact :

```powershell
python -m src.audit_d02 "data/raw/GLD_<horodatage>/GLD_daily.csv"
```

Le module lit `GLD_daily.csv` et `metadata.json` du même dossier. Une fois les dépendances installées, cet audit fonctionne **hors connexion**.

**Pour créer un nouveau snapshot**, vérifier les paramètres dans `configs/data_config.json`, puis lancer la collecte :

```powershell
python -m src.data
```

Le script écrit les données, les métadonnées et le résumé des premiers contrôles. Le chemin affiché permet d’exécuter ensuite l’audit détaillé sur cette collecte.

**Pour présenter les résultats**, ouvrir `notebooks/02_data_audit.ipynb`, sélectionner le même snapshot dans la variable `SNAPSHOT` et exécuter les cellules dans l’ordre.

---

## D03 — Économétrie de la moyenne : prévision des rendements de GLD

### Objectif du livrable

D03 cherche à répondre à une question simple : **les rendements passés de GLD permettent-ils de prévoir le rendement de la séance suivante mieux qu’une méthode naïve ?**

Nous comparons **Naïf, ARIMA classique, Auto-ARIMA, SARIMA et SARIMAX**, avec la même série et les mêmes périodes. Ce livrable sert à **justifier un choix de modèle de prévision**. Il ne mesure pas encore la rentabilité d’une stratégie ni l’intérêt de GARCH pour ajuster l’exposition au risque.

### Données, cible et protocole

D03 réutilise le fichier `GLD_daily.csv` issu de D02. Nous calculons les **rendements logarithmiques journaliers en pourcentage** à partir de la clôture ajustée :

\[
r_t = 100 \times \ln\!\left(\frac{Close_t}{Close_{t-1}}\right)
\]

Pour SARIMAX, nous ajoutons la **variation du log-volume retardée d’une séance**. Ce décalage évite d’utiliser le volume du jour que l’on cherche à prévoir.

Nous conservons les périodes de D02 : **2018–2022 pour l’apprentissage**, **2023–2024 pour la validation** et **2025–30/10/2026 pour le test final**. Les paramètres des modèles sont estimés sur l’apprentissage ; le choix de la méthode se fait avec la MAE de validation. Le test final sert à évaluer le modèle sans modifier ce choix.

### Démarche de modélisation et justifications

| Étape | Méthode | Pourquoi ? |
|---|---|---|
| 1. **Stationnarité** | Test ADF sur les rendements du train | Déterminer si une différenciation (`d`) est nécessaire avant ARIMA. |
| 2. **Identification** | Graphiques ACF et PACF | Observer les dépendances temporelles pour proposer de petits ordres `p` et `q`. |
| 3. **ARIMA classique** | Comparer `(0,d,0)`, `(1,d,0)`, `(0,d,1)` et `(1,d,1)` selon l’AIC sur le train | Retenir un ordre simple avec un compromis entre ajustement et complexité. |
| 4. **Auto-ARIMA** | Recherche automatique limitée des ordres selon l’AIC | Vérifier si une sélection automatique donne un meilleur modèle que la démarche classique. |
| 5. **SARIMA** | Saisonnalité hypothétique de 5 séances | Tester si une structure hebdomadaire améliore les prévisions. |
| 6. **SARIMAX** | Ajouter le volume retardé | Tester si une information disponible la veille apporte une valeur prédictive. |
| 7. **Référence naïve** | Prévoir le rendement du jour à partir de celui de la veille | Vérifier si les modèles plus complexes améliorent réellement une règle simple. |

La saisonnalité de cinq séances est **une hypothèse à tester**, pas un fait supposé. Le modèle Auto-ARIMA complète la méthode Box–Jenkins traditionnelle : il ne remplace pas les graphiques ACF/PACF et leur interprétation.

### Prédictions et évaluation hors apprentissage

Pour chaque séance de validation et de test, le notebook calcule une **prévision à un pas**. Le modèle peut utiliser les observations passées déjà connues, mais **jamais le rendement qu’il cherche à prédire**. Les coefficients restent ceux estimés sur l’apprentissage.

Nous comparons deux métriques :

- **MAE (erreur absolue moyenne)** : mesure l’erreur moyenne, facile à lire ;
- **RMSE (racine de l’erreur quadratique moyenne)** : pénalise davantage les erreurs importantes.

Les deux sont exprimées en **points de pourcentage de rendement** ; une valeur plus faible est préférable. Le **modèle retenu est celui avec la MAE de validation la plus faible**, puis sa performance est observée sur le test final.

### Diagnostics et graphiques

Le notebook affiche les résumés statistiques de l’ARIMA classique et d’Auto-ARIMA (`summary()`) ainsi que le **test de Ljung–Box** sur les résidus, complété par l’**ACF des résidus ARIMA**. Ces contrôles permettent de vérifier s’il reste une autocorrélation inexpliquée ; ils ne prouvent pas à eux seuls la qualité des prévisions futures.

Les graphiques illustrent :

- l’évolution historique de la clôture ajustée de GLD ;
- l’ACF et la PACF utilisées pour identifier ARIMA ;
- la comparaison des MAE en validation et en test ;
- les rendements **réels vs prédits** sur les dernières séances des deux périodes ;
- les **cinq prévisions suivantes avec ARIMA classique**, accompagnées d’un intervalle estimé à **95 %**.

**Précision :** les dates de cette dernière illustration sont approximées par des jours ouvrés ; le notebook n’exclut pas automatiquement les jours fériés de la Bourse américaine. Cette illustration future utilise **ARIMA classique**, même si un autre modèle a la meilleure MAE en validation.

### Fichier du livrable D03

| Fichier | Rôle |
|---|---|
| `notebooks/D03_B06_GLD_ARIMA_classique_et_AutoARIMA.ipynb` | Notebook à placer dans `notebooks/`. Charge les données D02, réalise ADF et ACF/PACF, estime les cinq méthodes, affiche les diagnostics et graphiques, compare leurs erreurs et enregistre les prévisions. |

### Résultats enregistrés

À l’exécution du notebook, les fichiers suivants sont créés dans `reports/d03/` :

| Fichier | Contenu |
|---|---|
| `previsions_d03.csv` | Dates, rendements réels, prédictions de Naïf, ARIMA classique, Auto-ARIMA, SARIMA et SARIMAX, ainsi que la période (validation/test). |
| `comparaison_d03.csv` | MAE et RMSE de chaque méthode en validation et sur le test final. |
| `diagnostics_d03.csv` | Résultats du test de Ljung–Box pour les modèles estimés. |
| `previsions_futures_arima.csv` | Cinq prévisions futures de rendement avec ARIMA classique et bornes estimées de l’intervalle à 95 %. |

Ces fichiers sont **produits au lancement** du notebook : leur présence dans le dépôt n’est pas présumée. Les résultats chiffrés dépendent du snapshot GLD effectivement chargé.

### Reproduire D03

**1. Préparer les données :** disposer d’un snapshot D02 audité sous `data/raw/GLD_<horodatage>/GLD_daily.csv`. Le notebook sélectionne automatiquement le **dernier dossier selon son nom**, parmi ceux disponibles ; vérifier le chemin affiché avant d’interpréter les résultats.

**2. Installer les bibliothèques nécessaires**, depuis la racine du projet :

```powershell
python -m pip install -r requirements.txt
python -m pip install statsmodels pmdarima
```

**3. Ouvrir le notebook** `notebooks/D03_B06_GLD_ARIMA_classique_et_AutoARIMA.ipynb` avec Jupyter ou VS Code, puis exécuter toutes les cellules dans l’ordre. Il peut être lancé depuis la racine du dépôt ou depuis `notebooks/`.

**4. Vérifier les sorties** dans `reports/d03/` et commenter les scores obtenus sur les **vraies données**. Il n’est pas nécessaire de télécharger les données à nouveau si le snapshot existe.

### Conclusion attendue pour D03

Le choix final doit être appuyé par **la MAE sur la validation**, complétée par la RMSE, l’examen des résidus et la comparaison au naïf. Nous expliquerons si l’approche traditionnelle ou Auto-ARIMA obtient les meilleures prévisions et si la saisonnalité ou le volume retardé sont utiles. **Un modèle plus complexe n’est pas retenu automatiquement** : son intérêt doit être visible dans les résultats.

D03 constitue ainsi une **base de prévision de la moyenne des rendements** pour la suite du projet. L’étude de la volatilité et de la taille d’exposition dynamique avec **GARCH** sera menée dans les livrables consacrés au risque et aux stratégies.

---

## État des travaux et prochaines étapes

- **D01 :** cadrage du projet, question scientifique et répartition de l’équipe.
- **D02 :** collecte, sauvegarde reproductible et audit des données GLD.
- **D03 :** notebook de prévision de la moyenne avec identification ARIMA, comparaison de modèles, diagnostics et prévisions datées.
- **Étapes suivantes :** modélisation du risque par GARCH, stratégies à exposition fixe ou dynamique, backtest et intégration dans Streamlit.

Les valeurs de performance D03 ne sont **pas indiquées dans ce README avant l’exécution sur le snapshot réel**. Elles sont à lire dans `reports/d03/comparaison_d03.csv` et dans les conclusions du notebook.
