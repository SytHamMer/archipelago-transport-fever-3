# Transport Fever 3 x Archipelago

Joue Transport Fever 3 (PC, Steam) dans un multiworld [Archipelago](https://archipelago.gg), sans honor system : le jeu verrouille ce qui n'est pas reçu et envoie lui-même les checks.

Statut : tranche minimale (phase 1), testée en local. **Rien n'est proposé au dépôt officiel d'Archipelago** : tout est local tant que les tests ne sont pas terminés.

## Ce qu'il faut

- Transport Fever 3 (Steam) et Archipelago 0.6.x installés.
- Les deux livrables de ce projet, décrits plus bas : le monde (`.apworld`) et le mod.

## Installer et jouer

L'installation d'Archipelago, l'ajout d'un monde, la génération, l'hébergement et la connexion d'un client sont décrits dans la [documentation officielle d'Archipelago](https://archipelago.gg/tutorial/Archipelago/setup/en) : on ne les répète pas ici. Ce qui est propre à ce monde :

- Le monde à installer est `dist/transport_fever_3.apworld` (`python scripts/build_world.py`). Le client s'appelle **Transport Fever 3 Client** dans le Launcher.
- Le mod `tf3_mod/archipelago_tf3_1` s'installe avec `python scripts/install_mod.py` (jeu fermé). Le script écrit uniquement un nouveau dossier dans `...\3493540\local\mods\`.
- Crée une **nouvelle partie libre** avec le mod « Archipelago for Transport Fever 3 » actif et une **année de départ de 2000 ou plus** (2020 est le maximum proposé). Sans cela, aucun item ne peut débloquer les véhicules plus récents que la partie.

Le client et le mod échangent deux fichiers dans `...\3493540\local\towns_industries\` (le jeu n'autorise que ce dossier et `mod_presets` pour les mods). Variable `TF3_USERDATA_DIR` pour changer le dossier.

Le détail pas à pas, le choix de l'année et le dépannage sont dans [docs/guide-installation.md](docs/guide-installation.md).

## Options YAML

Le format d'un YAML, les poids et les options aléatoires sont expliqués dans la [documentation officielle des réglages](https://archipelago.gg/tutorial/Archipelago/advanced_settings/en). Voici les options de ce monde :

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
