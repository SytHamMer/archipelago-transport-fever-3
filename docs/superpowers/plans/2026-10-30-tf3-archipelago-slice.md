# TF3 x Archipelago, tranche minimale : plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un monde Archipelago Python, un client Launcher et un mod TF3 qui jouent une partie dédiée de bout en bout, avec verrous en direct, checks réglables et goals combinés.

**Architecture:** Le monde Python décrit items, checks et goals, et envoie les options (`slot_data`). Le client écrit un fichier `inbox` (état voulu) et lit un fichier `outbox` (checks atteints) dans `towns_industries/`. Le mod, un script GUI qui boucle toutes les 2 s, applique l'état et évalue les checks. Un fichier `contract/constants.json` fixe les noms partagés.

**Tech Stack:** Python 3.13, Archipelago 0.6.x (`CommonClient`, Kivy), pytest, `lupa` (tests Lua), Lua 5.x du mod TF3.

**Spec:** `docs/superpowers/specs/2026-10-30-tf3-archipelago-slice-design.md`

## Global Constraints

- PC uniquement (Steam). **Aucune modification de l'installation du jeu ni des sauvegardes** (`...\3493540\local\save`). Le mod s'installe uniquement comme dossier neuf dans `...\3493540\local\mods\`.
- Scripts de mod : pas d'`io`, pas de réseau ; échange par `app.loadUserdata` / `saveUserdata` dans les seuls dossiers `towns_industries` et `mod_presets` (on utilise `towns_industries`). Fichiers au format `function data() return {...} end`.
- Boucle du mod : **toutes les 2 secondes**, dans `guiUpdate`. Chaque lecture sous `pcall` ; erreurs dans le log avec le préfixe `ARCHIPELAGO`.
- Verrous : `api.gui.fireReactEvent("setVehicleFilter", ...)` et `("setMenuFilter", ...)`, envoyés **seulement quand la liste change** ; chaque appel remplace tout le filtre. Étiquettes de menu au format `::/depots/road/tram_depot/tram_depot.con@0` (suffixe `@0`..`@11` ajouté).
- Argent : `makeJournalBookAssetCmd` (`time = -1`, INCOME si positif, OTHER sinon). Niveau : `genericRep` `::/game_mechanics/company/company_growth_config.res`, `setAsTable` avec `data.enforcedLevel`, **jamais en dessous du niveau gagné**.
- Les listes de `outbox.checks` ne font que grandir. L'`inbox` est un état complet, idempotent. Effets ponctuels appliqués **une fois**, par numéro unique (indice de l'item reçu).
- Parties dédiées : le mod est actif dès la création de la partie. La route est disponible au départ.
- Goal : gagné quand **tous les goals actifs** sont atteints ; au moins un actif ; 0 désactive.
- Erreur de génération claire si moins de checks que d'items de progression.
- Jeu silencieux : pas de notification ni de panneau en jeu dans cette tranche.

## Review Focus

1. Aucun goal actif (tous à 0) : la génération échoue avec un message clair (Task 4).
2. Palier unique ou bornes inversées (`count=1`, `first > last`) : `spread` ne plante pas et reste strictement croissante (Task 3).
3. `outbox` lue pendant que le mod l'écrit (fichier tronqué ou vide) : le client réessaie, n'envoie rien de faux (Task 8).
4. Reconnexion ou rechargement : mêmes items renvoyés, aucun effet réappliqué, aucun check perdu (Tasks 7 et 12).
5. `seed` différent entre `inbox` et `outbox` : l'ancienne `outbox` est ignorée et le joueur est prévenu (Tasks 8 et 12).

## Structure des fichiers

```
contract/constants.json            noms partagés (modes, items, familles, goals, ids de checks)
tf3_world/transport_fever_3/        monde Archipelago (apworld)
  __init__.py  data.py  Options.py  Items.py  Locations.py  Rules.py
  client/luafile.py  client/bridge.py  client/tf3_client.py
tf3_mod/archipelago_tf3/            mod TF3
  mod.json  _content.json  _metadata/modinfo.json
  content/ap.gs.lua  ap_main.script.lua  ap_locks.lua  ap_checks.lua  ap_effects.lua
tests/                              pytest (monde, client) et tests Lua (lupa)
scripts/                            dev_link.py, build_world.py, install_mod.py
```

Le dossier `tf3_probe/` (sondes) et `tf3_ap/` (Manual) restent comme référence, hors du livrable.

---

### Task 1: Dépôt git et environnement de test

**Files:**
- Create: `.gitignore`, `pytest.ini`, `tests/conftest.py`, `scripts/dev_link.py`, `contract/constants.json`
- Test: `tests/test_smoke.py`

**Interfaces:**
- Produces: dépôt git ; `tests/conftest.py` met `ap/` dans `sys.path` ; `scripts/dev_link.py` crée la jonction `ap/worlds/transport_fever_3` vers `tf3_world/transport_fever_3` ; `contract/constants.json` avec les clés `modes`, `goals`, `families`, `items` (voir Task 3).

- [ ] **Step 1:** `git init` dans le projet ; `.gitignore` exclut `ap/`, `m/`, `venv/`, `out/`, `players/`, `tf3_world/**/__pycache__`. Ne pas suivre `ap/` ni `m/` (clones externes).
- [ ] **Step 2:** Écrire `tests/test_smoke.py::test_archipelago_importable` : `import BaseClasses` réussit grâce à `conftest.py`. Le lancer : doit échouer avant `conftest.py`, passer après (`venv/Scripts/python -m pytest tests/test_smoke.py -v`).
- [ ] **Step 3:** Installer dans le venv `pytest` et `lupa` (demander l'autorisation à l'utilisateur pour `pip install`).
- [ ] **Step 4:** Commit : `chore: scaffold repo and test environment`.

### Task 2: Codec des fichiers Lua d'échange

**Files:**
- Create: `tf3_world/transport_fever_3/client/luafile.py`
- Test: `tests/test_luafile.py`

**Interfaces:**
- Produces: `dumps(value: dict) -> str` (écrit `function data()\nreturn {...}\nend\n`) ; `loads(text: str) -> dict` ; `class LuaFormatError(ValueError)`. Types gérés : dict (clés str), list, str, int, float, bool.

- [ ] **Step 1:** Tests : `test_roundtrip_nested` (dict avec listes, chaînes à guillemets et `\n`, entiers, booléens) ; `test_loads_game_written_sample` avec le fichier réel écrit par le jeu (`function data()\nreturn { \n\t\tcounter = 1,\n\t\tmsg = "created by game",\n\t}\nend`) donne `{"counter": 1, "msg": "created by game"}` ; `test_loads_truncated_raises` (texte coupé en plein milieu) lève `LuaFormatError` ; `test_loads_empty_raises`.
- [ ] **Step 2:** Lancer : échec attendu (module absent).
- [ ] **Step 3:** Implémenter un analyseur du sous-ensemble Lua ci-dessus (pas de `eval`/`exec` ; jamais d'exécution du texte).
- [ ] **Step 4:** Lancer : tous passent. Commit : `feat: lua data file codec`.

### Task 3: Données partagées et paliers

**Files:**
- Create: `tf3_world/transport_fever_3/data.py`, `contract/constants.json`
- Test: `tests/test_data.py`

**Interfaces:**
- Produces dans `data.py` : `MODES = ("Tram", "Rail", "Water", "Air")` ; `ITEM_MODE(mode) -> str` donne `f"{mode} Transport"` ; `ITEM_VEHICLES(mode) -> str` donne `f"Progressive {mode} Vehicles"` (et `"Progressive Road Vehicles"` pour la route) ; `ITEM_LEVEL = "Company Level +1"` ; `MONEY_ITEMS = {"Money Grant (small)": 50_000, "Money Grant (medium)": 250_000, "Money Grant (large)": 1_000_000}` ; `TRAPS = {"Money Loss": 100_000, "Forced Loan": 0}` ; `CARGOS: tuple[str, ...]` (les 28 noms du tempéré, identifiants de fichiers du jeu, par exemple `grain`) ; `DELIVERY_AMOUNTS = (100, 500, 2000, 10000)` ; `spread(count: int, first: int, last: int) -> list[int]` ; `location_id(family: str, *parts) -> str` (par exemple `population:3`, `line:rail`, `delivered:grain:2`).
- `contract/constants.json` reprend ces noms ; `tests/test_data.py::test_constants_match_contract` vérifie l'égalité.

- [ ] **Step 1:** Tests : `spread(8, 500, 20000)` croissante stricte de longueur 8, premier 500, dernier 20000 ; `spread(1, 500, 20000) == [500]` ; `spread(3, 100, 100)` ne plante pas et reste strictement croissante (adapter : l'écart minimal 1) ; `spread(0, 1, 2) == []` ; `test_constants_match_contract`.
- [ ] **Step 2:** Lancer : échec. **Step 3:** Implémenter (espacement géométrique arrondi, dédoublonné par incrément minimal de 1). **Step 4:** Passe. Commit : `feat: shared data tables and threshold spread`.

### Task 4: Options YAML

**Files:**
- Create: `tf3_world/transport_fever_3/Options.py`
- Test: `tests/test_options.py`

**Interfaces:**
- Produces : `class TF3Options(PerGameCommonOptions)` avec des `Range` : `population_checks` (0-30, défaut 4), `population_first` (défaut 500), `population_last` (défaut 5000), `company_level_checks` (0-14, défaut 4), `passengers_checks` (défaut 3), `passengers_first` (défaut 100), `passengers_last` (défaut 2000), `cargo_checks` (défaut 3), `cargo_first` (défaut 100), `cargo_last` (défaut 2000), `delivery_checks` (0-4, défaut 1) ; `Toggle` : `first_line_checks` (défaut vrai) ; goals `Range` : `goal_population` (défaut 2500), `goal_company_level`, `goal_passengers`, `goal_cargo` (défaut 0) ; plus `death_link` non utilisé. `validate_goals(options) -> None` lève `OptionError` si les quatre goals valent 0.

- [ ] **Step 1:** Tests : `test_default_options_have_one_goal` ; `test_no_active_goal_raises` (les quatre à 0, `OptionError` avec message contenant `goal`) ; `test_option_names_unique`.
- [ ] **Steps 2-4:** échec, implémentation, passe. Commit : `feat: world options and goal validation`.

### Task 5: Items et locations

**Files:**
- Create: `tf3_world/transport_fever_3/Items.py`, `Locations.py`
- Test: `tests/test_items_locations.py`

**Interfaces:**
- Consumes : `data.py` (Task 3), `TF3Options` (Task 4).
- Produces : `item_table: dict[str, int]` (nom vers identifiant stable, base 7_300_000) ; `item_counts(options) -> dict[str, int]` (4 modes ×1 ; 5 `Progressive … Vehicles` ×2 chacun ; `Company Level +1` × `options.company_level_checks` ; filler et pièges laissés au monde) ; `location_table: dict[str, int]` ; `active_locations(options) -> list[str]` (identifiants `population:1..N`, `company_level:2..`, `passengers:i`, `cargo:i`, `line:<mode>` pour les 5 modes route/tram/rail/eau/air si `first_line_checks`, `delivered:<cargo>:<tier>` si `delivery_checks`).

- [ ] **Step 1:** Tests : avec les options par défaut, `item_counts` contient `"Rail Transport": 1` et `"Progressive Road Vehicles": 2` ; `active_locations` contient `population:1` et pas `population:5` ; `first_line_checks=False` supprime les `line:*` ; ids uniques et stables entre deux appels.
- [ ] **Steps 2-4:** échec, implémentation, passe. Commit : `feat: items and locations from options`.

### Task 6: Classe du monde, logique, goal, slot_data

**Files:**
- Create: `tf3_world/transport_fever_3/__init__.py`, `Rules.py`, `archipelago.json`
- Test: `tests/test_world.py` (base `test.bases.WorldTestBase` d'Archipelago)

**Interfaces:**
- Consumes : tâches 3 à 5.
- Produces : `class TF3World(World)` (`game = "Transport Fever 3"`) ; `fill_slot_data(self) -> dict` retournant `{"version": 1, "seed": <multiworld.seed_name>, "goals": {"population": int, "company_level": int, "passengers": int, "cargo": int}, "checks": {"population": [..], "company_level": [..], "passengers": [..], "cargo": [..], "first_line": bool, "delivery": [..]}}` ; goal `completion_condition` = tous les événements des goals actifs ; `before_generate`/`generate_early` lève `OptionError` si `len(active_locations) < nombre d'items de progression` (message qui nomme le déficit et les options à relever).

- [ ] **Step 1:** Tests : `test_default_seed_is_beatable` (`all_state` atteint le goal) ; `test_line_check_requires_mode_item` (`line:rail` inaccessible sans `Rail Transport`) ; `test_too_few_checks_raises` (tout à 0 sauf un goal, `OptionError` mentionnant le nombre de checks et d'items) ; `test_slot_data_shape` (les clés ci-dessus).
- [ ] **Steps 2-4:** échec, implémentation, passe. La logique : un check de mode exige son item ; population/passagers/fret élevés exigent davantage de modes et de véhicules progressifs (seuil par tranche des paliers, détail dans `Rules.py`). Commit : `feat: TF3 world with rules, goals and slot_data`.

### Task 7: Pont client (état vers inbox, outbox vers checks)

**Files:**
- Create: `tf3_world/transport_fever_3/client/bridge.py`
- Test: `tests/test_bridge.py`

**Interfaces:**
- Consumes : `luafile` (Task 2), forme de `slot_data` (Task 6).
- Produces : `class Bridge(userdata_dir: Path)` avec `write_inbox(slot_data: dict, received: list[str]) -> None` (construit `{"version", "seed", "config", "items": {nom: quantité}, "effects": [{"id": indice_1, "kind": "money"|"money_loss"|"loan", "amount": int}...]}` ; l'`id` d'un effet est l'indice de l'item dans `received`, base 1) ; `read_outbox() -> Outbox | None` avec `Outbox(seed: str, checks: set[str], goals: dict[str, bool], applied: int, heartbeat: int)` ; `new_checks(sent: set[str]) -> set[str]` ; `seed_matches(slot_seed: str) -> bool`. Fichiers : `archipelago_tf3_inbox.lua`, `archipelago_tf3_outbox.lua`.

- [ ] **Step 1:** Tests : `test_inbox_counts_items_and_numbers_effects` (reçus `["Rail Transport", "Money Grant (small)", "Money Grant (small)"]` donne `items["Rail Transport"] == 1` et deux effets d'ids 2 et 3) ; `test_resend_same_items_same_inbox` (idempotent) ; `test_read_outbox_truncated_returns_none` (fichier coupé en deux, pas d'exception) ; `test_read_outbox_missing_returns_none` ; `test_new_checks_diff` ; `test_seed_mismatch_detected`.
- [ ] **Steps 2-4:** échec, implémentation (écriture atomique de l'`inbox` : fichier temporaire puis remplacement), passe. Commit : `feat: client bridge for inbox and outbox`.

### Task 8: Client Launcher

**Files:**
- Create: `tf3_world/transport_fever_3/client/tf3_client.py`
- Modify: `tf3_world/transport_fever_3/__init__.py` (enregistrer le composant `Component("Transport Fever 3 Client", func=launch_client, ...)`)
- Test: `tests/test_client_logic.py`

**Interfaces:**
- Consumes : `Bridge` (Task 7).
- Produces : `class TF3Context(CommonContext)` (`game = "Transport Fever 3"`) ; `find_userdata_dir() -> Path | None` (cherche `Steam/userdata/*/3493540/local/towns_industries`, accepte une valeur de configuration) ; `async poll_outbox(self)` toutes les secondes : envoie `LocationChecks` pour `new_checks`, puis `StatusUpdate` `CLIENT_GOAL` quand tous les goals actifs sont vrais ; sur `ReceivedItems` et `Connected`, `Bridge.write_inbox`. Messages d'état : `jeu connecté` d'après le battement (moins de 10 s), `seed différent`, `dossier introuvable`.

- [ ] **Step 1:** Tests de la logique sans réseau : `test_goal_sent_only_when_all_active_goals_true` (goals `{"population": True, "cargo": False}` avec cargo actif : pas de statut ; les deux vrais : statut) ; `test_inactive_goal_ignored` ; `test_corrupt_outbox_sends_nothing`.
- [ ] **Steps 2-4:** échec, implémentation, passe. Commit : `feat: Launcher client for TF3`.

### Task 9: Mod, module des verrous

**Files:**
- Create: `tf3_mod/archipelago_tf3/content/ap_locks.lua`
- Test: `tests/lua/test_ap_locks.py` (lupa)

**Interfaces:**
- Produces : `compute_locks(items: table, catalog: table) -> {menu = {string}, vehicles = {string}}` où `items` est `inbox.items`, `catalog` décrit pour chaque mode ses fragments de chemin et ses types de véhicules ; la route démarre déverrouillée. Règle : un mode sans son item `X Transport` verrouille tout (menu et véhicules) ; avec l'item, seules les tranches de véhicules au-delà de `1 + count("Progressive X Vehicles")` restent verrouillées (tranche par `yearFrom` : A avant 1920, B avant 1960, C ensuite ; bornes dans `catalog`).
- Produit aussi `deep_equal(a, b) -> boolean` pour ne renvoyer un filtre que s'il a changé.

- [ ] **Step 1:** Tests Python/lupa : `test_unreceived_mode_locks_menu_and_vehicles` ; `test_received_mode_unlocks_menu` ; `test_vehicle_tiers_follow_progressive_count` (0, 1, 2 items) ; `test_road_unlocked_at_start` ; `test_lists_have_no_duplicates` ; `test_unknown_item_ignored`.
- [ ] **Steps 2-4:** échec, implémentation, passe. Commit : `feat(mod): lock computation`.

### Task 10: Mod, module des checks

**Files:**
- Create: `tf3_mod/archipelago_tf3/content/ap_checks.lua`
- Test: `tests/lua/test_ap_checks.py`

**Interfaces:**
- Produces : `evaluate(config: table, readings: table) -> {checks = {string}, goals = {population = boolean, ...}}` où `readings = {experience, earned_level, passengers, cargo, line_modes = {[mode_index] = true}, delivered = {[cargo_name] = n}}` et `config` est le `config` de l'`inbox`. Les identifiants sont ceux de `data.location_id`. Index de modes : BUS 3, TRUCK 4, TRAM 5 ou 6, TRAIN 7 ou 8, AIRCRAFT/SMALL_AIRCRAFT/HELICOPTER 9, 11, 13, SHIP/SMALL_SHIP 10, 12. `line:road` pour 2, 3, 4.
- Produit aussi `merge_monotonic(previous: {string}, current: {string}) -> {string}` (jamais de retrait).

- [ ] **Step 1:** Tests : `test_population_thresholds` (palier atteint à 500, pas à 499) ; `test_line_modes_map` ; `test_goal_all_active_required` (population 2500 actif et passagers 0 : seul population compte) ; `test_checks_never_shrink` (`merge_monotonic`, expérience qui redescend) ; `test_missing_readings_safe` (lecture nil, pas d'erreur).
- [ ] **Steps 2-4:** échec, implémentation, passe. Commit : `feat(mod): check evaluation`.

### Task 11: Mod, module des effets

**Files:**
- Create: `tf3_mod/archipelago_tf3/content/ap_effects.lua`
- Test: `tests/lua/test_ap_effects.py`

**Interfaces:**
- Produces : `pending(effects: {table}, applied: integer) -> {table}` (effets dont `id > applied`, triés) ; `granted_level(items: table, earned_level: integer) -> integer` (`max(earned, 1 + count("Company Level +1"))`, plafond `MAX_LEVEL = 15`).

- [ ] **Step 1:** Tests : `test_pending_skips_applied` ; `test_pending_order` ; `test_replay_same_inbox_applies_nothing_new` ; `test_granted_level_never_below_earned` ; `test_granted_level_capped`.
- [ ] **Steps 2-4:** échec, implémentation, passe. Commit : `feat(mod): effects bookkeeping`.

### Task 12: Mod, script principal et installation

**Files:**
- Create: `tf3_mod/archipelago_tf3/mod.json`, `_content.json`, `_metadata/modinfo.json`, `content/ap.gs.lua`, `content/ap_main.script.lua`, `scripts/install_mod.py`
- Test: `tests/test_install_mod.py` ; vérification en jeu (voir étapes)

**Interfaces:**
- Consumes : `ap_locks`, `ap_checks`, `ap_effects`, `Bridge` (formats).
- Produces : `step()` dans `guiUpdate` : lit l'`inbox`, calcule et envoie les filtres si changés, règle `enforcedLevel`, applique les effets en attente (argent, perte d'argent, prêt) puis écrit `applied`, évalue les checks, écrit l'`outbox` `{version, seed, checks, goals, applied, heartbeat}`. **Sans `inbox`** : applique les verrous de l'état de départ (tout verrouillé sauf la route). **Seed différent** de l'`outbox` existante : on ignore l'ancienne `outbox`. `scripts/install_mod.py` : copie le dossier du mod comme **nouveau** dossier ; refuse si `TransportFever3.exe` tourne ou si le dossier cible existe déjà sans option `--update`.

- [ ] **Step 1:** Tests Python : `test_install_refuses_when_game_running` (processus simulé) ; `test_install_creates_new_folder_only` (le dossier `save` n'est jamais touché, vérifié sur un faux arbre).
- [ ] **Step 2:** Écrire le script principal en réutilisant les opérations déjà éprouvées dans `tf3_probe/archipelago_probe_1/content/probe.script.lua` (`lock`, `money`, `level`, `loan`, `reads`). Chaque appel au jeu sous `pcall`.
- [ ] **Step 3:** Vérifier en jeu avec l'utilisateur, sur une partie libre neuve, jeu fermé avant l'installation : (a) sans `inbox`, modes verrouillés, route libre ; (b) après un `inbox` écrit à la main avec `Rail Transport`, le rail se déverrouille en direct ; (c) un effet `money` d'id 1 donne l'argent une seule fois, même après avoir rechargé l'`inbox` ; (d) l'`outbox` contient les checks attendus et un `heartbeat` qui avance ; (e) un `inbox` avec un autre `seed` fait ignorer l'ancienne `outbox`.
- [ ] **Step 4:** Commit : `feat(mod): main script and installer`.

### Task 13: Empaquetage du monde

**Files:**
- Create: `scripts/build_world.py`
- Test: `tests/test_build_world.py`

**Interfaces:**
- Produces : `build() -> Path` crée `dist/transport_fever_3.apworld` (zip dont la racine est `transport_fever_3/`, avec `archipelago.json`, sans `__pycache__`).

- [ ] **Step 1:** Tests : l'archive contient `transport_fever_3/__init__.py` et `archipelago.json` ; ne contient aucun `.pyc`. **Step 2-4:** échec, implémentation, passe. Commit : `build: apworld packaging`.

### Task 14: Bout en bout et nettoyage

**Files:**
- Create: `docs/superpowers/plans/e2e-checklist.md`
- Modify: `README.md` (installation, YAML d'exemple, limites connues)

- [ ] **Step 1:** Avec l'utilisateur : installer le `.apworld` et le mod ; générer un seed solo avec `goal_population: 2500` seul ; héberger en local ; lancer « Transport Fever 3 Client » ; partie dédiée avec le mod ; atteindre un check de première ligne ; recevoir un item de mode ; terminer le goal. Résultat attendu : le serveur affiche le goal comme terminé, le client le montre, aucune sauvegarde existante n'a changé.
- [ ] **Step 2:** Retirer le mod de test `archipelago_probe_1` du dossier des mods ; supprimer `towns_industries` s'il est vide.
- [ ] **Step 3:** Mettre à jour la mémoire du projet et fermer les points ouverts de la spécification qui ont été tranchés. Commit : `docs: e2e checklist and readme`.
