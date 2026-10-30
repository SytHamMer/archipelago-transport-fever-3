# Transport Fever 3 x Archipelago

Joue Transport Fever 3 (PC, Steam) dans un multiworld [Archipelago](https://archipelago.gg), sans honor system : le jeu verrouille ce qui n'est pas reçu et envoie lui-même les checks.

Statut : tranche minimale (phase 1), testée en local. **Rien n'est proposé au dépôt officiel d'Archipelago** : tout est local tant que les tests ne sont pas terminés.

## Ce qu'il faut

- Transport Fever 3 (Steam) et Archipelago 0.6.x installés.
- Le monde `dist/transport_fever_3.apworld` (à construire : `python scripts/build_world.py`).
- Le mod `tf3_mod/archipelago_tf3_1`, installé avec `python scripts/install_mod.py` (jeu fermé). Le script écrit uniquement un nouveau dossier dans `...\3493540\local\mods\`.

## Installer et jouer

1. Dans le Launcher d'Archipelago : **Install APWorld**, choisis `transport_fever_3.apworld`, puis relance le Launcher.
2. **Generate Template Options**, copie le modèle « Transport Fever 3 » dans `Players`, règle-le (voir ci-dessous), puis **Generate**.
3. **Host Game** avec le zip généré, ou envoie-le à l'hébergeur de la partie.
4. Crée une **nouvelle partie libre** dans TF3 avec le mod « Archipelago for Transport Fever 3 » actif et une **année de départ de 2000 ou plus** (2020 est le maximum proposé). Sans cela, aucun item ne peut débloquer les véhicules plus récents que la partie.
5. Lance **Transport Fever 3 Client** depuis le Launcher, connecte-toi avec ton nom de slot.

Le client écrit et lit deux fichiers dans `...\3493540\local\towns_industries\` (le jeu n'autorise que ce dossier et `mod_presets` pour les mods). Variable `TF3_USERDATA_DIR` pour changer le dossier.

## Options YAML

| Option | Défaut | Rôle |
|---|---|---|
| `population_checks`, `population_first`, `population_last` | 4, 500, 5000 | paliers de population (nombre, premier, dernier) |
| `passengers_checks` / `_first` / `_last` | 3, 100, 2000 | passagers transportés au total |
| `cargo_checks` / `_first` / `_last` | 3, 100, 2000 | fret transporté au total |
| `company_level_checks` | 4 | niveaux d'entreprise 2, 3, 4… |
| `delivery_checks` | 1 | paliers de livraison par type de cargo (100, 500, 2 000, 10 000) |
| `first_line_checks` | oui | première ligne de chaque mode |
| `goal_population`, `goal_company_level`, `goal_passengers`, `goal_cargo` | 2500, 0, 0, 0 | goals ; 0 désactive ; la partie est gagnée quand **tous** les goals actifs sont atteints |

Exemple :

```yaml
name: MonNom
game: Transport Fever 3
Transport Fever 3:
  goal_population: 5000
  goal_passengers: 1000
  population_checks: 6
  population_last: 8000
```

Il faut au moins autant de checks que d'items de progression : sinon la génération s'arrête avec un message qui dit combien.

## Limites connues

- Les effets ponctuels (argent, pièges) sont liés au **seed**, pas à la sauvegarde : recharger une vieille sauvegarde ne rend pas l'argent déjà reçu.
- Les cargos sont ceux du climat tempéré.
- Le mode Air, le tram, l'eau, les checks de première ligne et de livraison, le piège « prêt forcé » et la tranche 3 des véhicules n'ont pas tous été vérifiés dans le jeu (voir `docs/superpowers/plans/e2e-checklist.md`).
- Pas de notification ni de panneau dans le jeu (idée pour la phase 2).

## Développement

```
venv\Scripts\python -m pytest                       # tests (monde, client, modules Lua via lupa)
venv\Scripts\python scripts\build_world.py          # dist/transport_fever_3.apworld
venv\Scripts\python scripts\install_mod.py --update # installe le mod (jeu fermé)
venv\Scripts\python scripts\dev_inbox.py --seed s1 "Rail Transport"   # simule le client
venv\Scripts\python scripts\e2e_headless.py out\AP_xxx.zip            # serveur + client + faux mod
```

`ap/` (clone d'Archipelago) et `m/` (template Manual) ne sont pas suivis par git. `tf3_ap/` est le prototype Manual, `tf3_probe/` les sondes qui ont servi à mesurer ce que le jeu permet.
