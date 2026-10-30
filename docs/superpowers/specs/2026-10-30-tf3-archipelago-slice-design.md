# Transport Fever 3 x Archipelago : tranche minimale de bout en bout

Date : 2026-10-30. Statut : brouillon à relire. Phase 1 sur 3 (voir « Phasage »).

## 1. Objectif

Jouer Transport Fever 3 (PC, Steam) dans un multiworld Archipelago, **sans honor system** : le jeu verrouille réellement ce qui n'est pas reçu et envoie lui-même les checks.

La tranche prouve la boucle complète avec un vrai serveur Archipelago : items reçus qui déverrouillent le jeu, checks détectés qui partent au serveur, goal combiné qui termine la partie.

### Phasage

1. **Cette tranche** : modes, véhicules progressifs, niveau d'entreprise, argent, pièges (perte d'argent, prêt forcé), checks et goals réglables.
2. **Contenu complet** : cargos, ères, autres pièges, notifications en jeu avec le logo Archipelago, familles de checks supplémentaires.
3. **Missions du jeu** comme source de checks, leurs récompenses redirigées vers le multiworld.

Chaque phase a sa spécification, son plan et son code.

### Décisions déjà prises

- Une partie Archipelago est une **partie dédiée**, créée avec le mod actif. Pas d'activation sur une sauvegarde existante.
- Le jeu reste **silencieux** : il verrouille et déverrouille. Items reçus et checks s'affichent dans la fenêtre du client.
- Le monde est un **vrai monde Python** (`.apworld`), pas le Manual (le Manual a servi à valider le design, voir `tf3_ap/`).
- Le goal est gagné quand **tous les goals actifs** sont atteints.
- Plateforme : PC uniquement. Aucune modification de l'installation du jeu ni des sauvegardes.

## 2. Architecture

```
Serveur Archipelago <-> Client Python (Launcher) <-> fichiers d'échange <-> Mod TF3 (script GUI)
```

| Composant | Rôle |
|---|---|
| Monde Archipelago (Python, `.apworld`) | Items, locations, options YAML, logique, goals, `slot_data`. |
| Client Python | Composant du Launcher sur le client standard d'Archipelago. Connexion, écriture de l'`inbox`, lecture de l'`outbox`, envoi des checks, affichage. |
| Mod `archipelago_tf3` | Un script GUI qui, toutes les 2 secondes, applique l'état reçu et évalue les checks. |

**Règle de conception : des états, pas des événements.** L'`inbox` contient l'état complet voulu, l'`outbox` l'ensemble des checks atteints (qui ne fait que grandir). Recharger une sauvegarde ou reconnecter le client ne perd rien.

## 3. Ce que TF3 permet (mesuré)

Toutes ces mesures viennent de sondes jetables sur l'installation de l'auteur, contrôlées à l'écran. Notes détaillées dans la mémoire du projet (`tf3-runtime-lock-findings`).

- **Pas de fichier ni de réseau** dans les scripts de mod. `os` ne contient que `clock`, `date`, `difftime`, `getenv`, `time`. `debugPrint` écrit en direct dans `crash_dump/stdout.txt`.
- **Canal client vers jeu** : `app.loadUserdata` / `app.saveUserdata(dossier, nom)` depuis le script GUI (`guiUpdate`), relu à chaque appel, mais **uniquement** pour les dossiers `towns_industries` et `mod_presets`. Les fichiers sont du Lua : `function data() return {...} end`.
- **Verrous en direct, sans recharger** : `api.gui.fireReactEvent("setVehicleFilter", {enabledVehicles = {}, disabledVehicles = {...}})` et `("setMenuFilter", {enabledItems = {}, disabledItems = {...}, disabledParams = {}})`. C'est le mécanisme des missions de campagne. Chaque appel **remplace** tout le filtre précédent.
  - Véhicules : chemins de `modelRep.forEachModelWithMetadata("transportVehicle", ...)`, au format `::/vehicle/bus/aboag/aboag.mdl`.
  - Éléments de menu : au format des missions, par exemple `::/depots/road/tram_depot/tram_depot.con@0` (le suffixe `@N` est requis), stations en `.mdl` ou `.con@N`, ports en `.metacon`, voies en `.street_template`.
  - Vérifié : rail, eau, dépôt de tramway, voies ferrées et véhicules associés bloqués puis débloqués en direct, routes et dépôt de bus intacts.
- **Argent** : `api.cmd.sendCommand(api.cmd.makeJournalBookAssetCmd(joueur, entrée, Vec3f.new(0,0,0)))` avec une `JournalEntry` (montant, `time = -1`, catégorie INCOME ou OTHER). Vérifié : +50 000 et -20 000.
- **Prêt forcé** : `api.cmd.makeScriptingSendEventCmd("", "Loan", "Obtain", {loan, loan})` avec `loan = ug_require("::/game_mechanics/finance/loan_util.tl").createSmallLoan()`. Vérifié : solde +4 000 000.
- **Niveau d'entreprise** : la ressource générique `::/game_mechanics/company/company_growth_config.res` accepte `getAsTable` / `setAsTable` avec `data.enforcedLevel = N` depuis le contexte GUI. Le titre de la compagnie change en direct, l'expérience réelle reste intacte. `setData` n'existe pas dans le contexte GUI.
- **Lectures pour les checks** (contexte GUI) :
  - lignes : `api.engine.system.lineSystem.getLinesForPlayer(player)` et `getComponent(ligne, LINE).vehicleInfo.transportModes`, indexé par l'énumération `TransportMode` (PERSON 0, CARGO 1, CAR 2, BUS 3, TRUCK 4, TRAM 5, ELECTRIC_TRAM 6, TRAIN 7, ELECTRIC_TRAIN 8, AIRCRAFT 9, SHIP 10, SMALL_AIRCRAFT 11, SMALL_SHIP 12, HELICOPTER 13) ;
  - totaux historiques : `api.engine.util.headquarters.getTransportedData()` (passagers et fret, identiques aux deux chiffres de la barre du jeu) ;
  - par cargo : `api.engine.util.logbook.getLogValueMostRecent(joueur, "itemsTransported" .. idCargo)` ;
  - population : `getCompanyProgressionState(joueur).experience`, égale à la population totale vue à l'écran (921 dans le test) ;
  - niveau gagné : `company_progression_util.getLevelAndFraction(company_util.getBasePopulation(), experience)`, indépendant de `enforcedLevel` ;
  - valeur de l'entreprise : `api.engine.util.headquarters.getCompaniesValue()` (champs `totalScore`, `railVehicles`, `trams`, `roadVehicles`, `aircrafts`, `ships`, `suppliedTowns`, lus par leur nom).
- **Pas de commande de panne de véhicule** : ce piège est abandonné.
- **Modifier les données des modèles en direct** (`setAsTable`, `setVisible`) n'atteint **pas** la boutique de véhicules (liste construite une fois). Ne pas utiliser pour les déblocages.

## 4. Le monde Archipelago

### Items

| Type | Contenu |
|---|---|
| Progression | **Mode** : Tram, Rail, Eau, Air (la route est disponible au départ). **Véhicules progressifs** : un item par mode, déverrouille la tranche d'années suivante. **Niveau d'entreprise +1**. |
| Filler | **Argent** en trois montants (petit, moyen, grand). |
| Pièges | **Perte d'argent**, **prêt forcé**. |

Tranches d'années des véhicules : alignées sur les trois époques du jeu (A, B, C, vues dans les noms de stations). Bornes exactes à fixer à l'implémentation.

### Checks

Familles à paliers, configurables (0 = famille désactivée) :
population totale, niveau d'entreprise gagné, passagers transportés, fret transporté. Familles activables : première ligne de chaque mode, livraisons par type de cargo.

Pour chaque famille à paliers, le joueur donne **le nombre de paliers, la première valeur et la dernière** ; le monde répartit les paliers entre les deux.

Identifiants stables de locations, par exemple `population:3`, `line:rail`, `delivered:grain:2`.

### Goals

Quatre goals réglables : population, niveau d'entreprise, passagers, fret, chacun avec sa valeur (0 = désactivé). Au moins un actif. Partie gagnée quand **tous les goals actifs** sont atteints.

### Logique

Une première ligne exige l'item de son mode. Les seuils élevés exigent davantage de modes et de véhicules. Le détail est fixé à l'implémentation et validé par des tests de génération.

### Validation des options

Si les options donnent moins de checks que d'items de progression, la génération s'arrête avec un message d'erreur clair (même principe que le Manual).

## 5. Le mod `archipelago_tf3`

Un script GUI, enregistré par un fichier `*.gs.lua` (`guiUpdateScript`), activé à la création de la partie. Découpé en modules : lecture de l'`inbox`, verrous, effets, checks, écriture de l'`outbox`. Si le chargement de modules propres au mod par `ug_require` ne marche pas, repli sur un fichier unique.

Boucle, **toutes les 2 secondes** :
1. Lire l'`inbox`.
2. Calculer les listes d'éléments de menu et de véhicules à interdire ; envoyer les deux filtres **seulement si elles ont changé**.
3. Régler `enforcedLevel` au niveau accordé par les items, sans jamais descendre sous le niveau gagné.
4. Appliquer **une seule fois** chaque effet ponctuel (argent, perte d'argent, prêt), d'après son numéro ; mémoriser le dernier numéro appliqué dans l'`outbox`.
5. Lire les données de check, écrire dans l'`outbox` l'ensemble des checks et goals atteints.
6. Écrire un battement (heure de la dernière boucle).

Sûreté : toute lecture est protégée (`pcall`) ; les erreurs vont dans le log avec le préfixe `ARCHIPELAGO` ; le mod ne modifie que les filtres, le niveau accordé et les écritures comptables, jamais les sauvegardes.

## 6. Contrats des fichiers

Dossier de données utilisateur de TF3 : `Steam/userdata/<id>/3493540/local/towns_industries/`. Format Lua `function data() return {...} end` que le client sait écrire et lire.

**`inbox`** (client vers mod) : `version`, `seed`, `config` (options du joueur, goals, seuils des checks), `items` (nom vers quantité), `effects` (liste ordonnée de `{id, kind, amount}`).

**`outbox`** (mod vers client) : `version`, `seed`, `checks` (identifiants stables), `goals` (état par goal), `applied` (dernier effet appliqué), `heartbeat`.

Si le `seed` de l'`inbox` et celui de l'`outbox` diffèrent, le mod ignore l'`outbox` et le client prévient le joueur.

## 7. Le client Python

Composant du Launcher, client standard d'Archipelago avec interface Kivy, comme le Manual Client.

- Détecte le dossier de données de TF3 et laisse le joueur le corriger.
- À la connexion : lit les options, écrit l'`inbox` complète, envoie les checks déjà présents dans l'`outbox` (checks faits hors ligne).
- Chaque item reçu met l'`inbox` à jour ; les effets ponctuels portent l'indice de l'item comme numéro.
- Surveille l'`outbox` chaque seconde, envoie la différence au serveur ; envoie le statut « goal terminé » quand tous les goals actifs sont atteints.
- Affiche items reçus, checks envoyés, état de connexion, « jeu connecté » d'après le battement.
- Gère clairement fichier absent, version ancienne, mod pas lancé, jeu fermé : affichage et nouvel essai, sans erreur ni donnée fausse.

## 8. Tests

1. **Monde Python** : génération avec options valides, options qui mènent à trop peu de checks, goals combinés, jeu atteignable pour toutes les combinaisons de goals.
2. **Client** contre un faux mod qui lit l'`inbox` et écrit une `outbox` simulée, avec un vrai serveur local.
3. **Mod** dans le jeu, sur une partie jetable, avec des opérations de lecture et de verrou (les sondes de `tf3_probe/` servent de base).
4. **Bout en bout** : un seed solo, un serveur local, une partie libre avec le mod, des goals bas, jusqu'à la victoire.

## 9. Hors périmètre de la tranche

Notifications et panneau dans le jeu, missions, cargos et ères comme items, autres pièges, activation sur une sauvegarde existante, plateformes console.

## 10. Points ouverts

- **Sans `inbox` (client non lancé)** : tout verrouiller (recommandé, on ne joue pas avant la connexion) ou ne rien verrouiller ? À trancher avant l'implémentation du mod.
- **Les effets sont liés au seed, pas à la sauvegarde** : recharger une vieille sauvegarde ne rend pas l'argent déjà reçu. À documenter dans le mode d'emploi.
- **Compteurs cumulatifs** : le compteur par cargo et le total transporté semblent cumulatifs (somme cohérente, valeur identique à la barre du jeu) ; la croissance monotone sur une longue partie reste à confirmer.
- **Population** : l'expérience égale la population à l'écran dans un test à 921 habitants ; à confirmer à plus grande échelle. Ma lecture par somme des villes a échoué (structure mal interprétée) et n'est pas nécessaire.
- **Permis de rang 4** (marketing, industrie supplémentaire) : le niveau accordé change le titre, mais l'ouverture effective de ces permis n'est pas vérifiée.
- **Prêt forcé** : le solde monte, mais l'apparition du prêt dans la fenêtre des finances n'est pas vérifiée.
- **Menus de construction** : les noms de stations ferroviaires, d'aérodromes et de voies ont été trouvés par recherche de fragments de chemin ; l'exhaustivité par mode est à contrôler (liste officielle à construire à l'implémentation). Le mode Air n'a pas pu être jugé visuellement (avions indisponibles à la date de départ).
- **Fragilité des canaux** : le canal par fichiers utilise des dossiers prévus pour l'éditeur de cartes et les presets de mods ; une mise à jour du jeu peut les changer. Les verrous passent par des événements du jeu utilisés par la campagne.
- **Montants et bornes** : montants d'argent et du prêt, tranches d'années exactes, plafond de niveau d'entreprise, valeurs par défaut des options.
- **Mod de test** `archipelago_probe_1` à retirer du dossier des mods du jeu une fois la tranche en développement.

## 11. Année de départ tardive (décision du 2026-10-30, option A)

**Constat.** Les filtres du mod ne font que cacher. Un véhicule (ou une station, une voie) dont l'année de sortie n'est pas arrivée est caché par le jeu lui-même : aucun item ne peut le montrer. Vérifié en jeu : un train de 1950 est inatteignable dans une partie de 1890. Cela contredit le but d'une partie plus rapide que le jeu de base.

**Décision.**
- Une partie Archipelago démarre à une **année tardive** (`MIN_START_YEAR = 2000` ou plus), choisie par le joueur à la création de la carte. Tout le contenu dont l'année est passée est alors disponible par la date, et ce sont nos items et nos filtres qui verrouillent.
- Le mod retire la **date de fin** des véhicules au chargement (`ap_load.script.lua`, `addModifier("loadModel", ...)`, comme le mod officiel `urbangames_vehicles_no_end_year`) : les anciens véhicules restent en vente. La **première année** n'est pas modifiée, les tranches s'appuient dessus.
- L'`outbox` contient `year` (année du jeu). Le client affiche un avertissement si elle est inférieure à `MIN_START_YEAR`.
- **Option B différée** (phase 2) : imposer l'année par la commande de réglage de date du jeu au premier tour. Ses effets sur les villes et les prix ne sont pas vérifiés.

**À vérifier en jeu** : l'année maximale proposée à la création d'une partie, les prix et coûts à partir de 2020, les bâtiments, et le verrouillage de tout le contenu moderne à l'état de départ.
