# Transport Fever 3 x Archipelago

Joue Transport Fever 3 (PC, Steam) dans un multiworld [Archipelago](https://archipelago.gg), sans honor system : le jeu verrouille ce qui n'est pas reçu et envoie lui-même les checks.

Statut : version 2, testée en local. **Rien n'est proposé au dépôt officiel d'Archipelago** : tout est local tant que les tests ne sont pas terminés.

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

## Contenu

- **Items** : un item par mode de transport (tram, rail, eau, air ; la route est libre), des véhicules par tranche d'année pour chaque mode, des types de routes et de voies, cinq outils (voies de bus, voies de tram, signaux, électrification, murs antibruit), quatre classes de cargo (vrac, plateau, marchandises, liquide), des niveaux d'entreprise, de l'argent et des pièges (pertes d'argent).
- **Checks** : population, niveaux d'entreprise, passagers et fret transportés, première ligne de chaque mode, livraisons par cargo et missions du jeu accomplies. Chaque check est un **contrat** : la récompense (item et joueur destinataire) est affichée dans la notification, et la commande `/contracts` du client liste les contrats ouverts.
- **Goals** : population, niveau d'entreprise, passagers ou fret ; la partie est gagnée quand tous les goals actifs sont atteints.

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
| `mission_checks` | 3 | nombre de checks « N missions du jeu accomplies » (0 à 30) |
| `money_scale` | 100 | pourcentage appliqué à tous les gains et pertes d'argent (10 à 1000) |
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

Les montants d'argent de base (gains 50 000 / 250 000 / 1 000 000, pertes 50 000 / 250 000) sont multipliés par `money_scale`.

Il faut au moins autant de checks que d'items de progression : sinon la génération s'arrête avec un message qui dit combien.

## Limites connues

- Les effets ponctuels (argent, pièges) sont liés au **seed**, pas à la sauvegarde : recharger une vieille sauvegarde ne rend pas l'argent déjà reçu.
- Les cargos sont ceux du climat tempéré.
- Le mode Air, le tram, l'eau, les checks de première ligne et de livraison, la tranche 3 des véhicules n'ont pas tous été vérifiés dans le jeu (voir `docs/superpowers/plans/e2e-checklist.md`).
- Les missions du jeu comptent une fois accomplies, quel que soit leur type ; le mod les relève toutes les 2 secondes.
- Pas de panneau dans le jeu : les items reçus et les checks envoyés sont annoncés par des notifications (avec le logo d'Archipelago), mais il n'y a pas de fenêtre de suivi.

## Développement

```
venv\Scripts\python -m pytest                       # tests (monde, client, modules Lua via lupa)
venv\Scripts\python scripts\build_world.py          # dist/transport_fever_3.apworld
venv\Scripts\python scripts\install_mod.py --update # installe le mod (jeu fermé)
venv\Scripts\python scripts\dev_inbox.py --seed s1 "Rail Transport"   # simule le client (--contracts : faux contrats)
venv\Scripts\python scripts\e2e_headless.py out\AP_xxx.zip            # serveur + client + faux mod
```

`ap/` (clone d'Archipelago) et `m/` (template Manual) ne sont pas suivis par git. `tf3_ap/` est le prototype Manual, `tf3_probe/` les sondes qui ont servi à mesurer ce que le jeu permet.
