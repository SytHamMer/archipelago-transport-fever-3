# V2, chantier C, partie 1 : types de routes et de voies

Date : 2026-10-30. Branche : `v2`. Complète la spécification de la V1.

## Décision

Deux nouveaux items de progression, avec **deux exemplaires chacun**, comme les véhicules progressifs :

| Item | Effet |
|---|---|
| `Progressive Road Types` | Débloque par tranche d'année les types de routes : `country`, `town`, `highway` |
| `Progressive Rail Tracks` | Débloque par tranche d'année les types de voies ferrées : `simple`, `standard`, `high_speed` (avec et sans caténaire) |

- Tranches par première année, aux bornes des véhicules (`data.ERA_STARTS`) : avant 1920, de 1920 à 1960, après 1960. Mesures du jeu : routes de 0 à 1940 (autoroutes 1940), voies simple (0, caténaire 1921), standard (1930), grande vitesse (1980).
- Les types de voies sont verrouillés **avec le mode rail**, puis relâchés par tranche ; les types de routes suivent l'item dès le départ (la route est libre).
- Les voies de tram et les pistes d'aéroport sont verrouillées avec leur mode (tram, air), sans tranches.
- Ce sont les ressources `.street_template` : leur nom est l'étiquette du filtre de menu, le même mécanisme que les stations et les dépôts.
- Les ères ne sont pas un item séparé : les tranches par année les couvrent déjà.

## Mod

Le catalogue contient, par mode, `types` (étiquette et année, lue dans `availability.yearFrom` de chaque modèle de rue) et `type_item`. `ap_locks.compute_locks` verrouille un type si son mode est verrouillé ou si sa tranche dépasse le nombre d'items reçus.

## Vérification

Tests Lua des tranches et du verrouillage par mode ; tests Python des items et du contrat. En jeu : sans item, seules les routes anciennes et la voie simple ; avec un puis deux items, les types plus récents apparaissent.

## Ajouts après le premier essai en jeu (2026-10-30)

**Routes entièrement bloquées au départ.** Le rapport de diagnostic du mod a montré que les routes anciennes ont une année de départ à 0 mais aussi une **date de fin** (par exemple `country_old_small` : 0 à 1940) : en 2020 le jeu les masque, comme les véhicules. `ap_load.script.lua` retire donc aussi la date de fin des modèles de rues (`loadStreetTemplate`) et des constructions d'infrastructure seulement (`loadConstruction`, chemins `/infrastructure/` : ronds-points, échangeurs, signaux), jamais des bâtiments ni des industries.

**Ronds-points et échangeurs** (`/infrastructure/street_construction/`, six constructions) suivent les types de routes : ils sont répartis par tranche d'année avec le même item.

**Outils**, un item à un exemplaire chacun (`data.TOOLS`) :

| Item | Libère |
|---|---|
| `Tool: Bus Lanes` | `bus_lane_tool.res` |
| `Tool: Tram Tracks` | `tram_track_tool.res` |
| `Tool: Rail Signals` | les constructions de `/infrastructure/signal/` |
| `Tool: Electrification` | `rail_electrification_tool.res` |
| `Tool: Noise Barriers` | les décorations de bord `barrier_*.edge` (routes et voies) |

Un outil d'un mode verrouillé (tram, rail) reste fermé même avec son item.
