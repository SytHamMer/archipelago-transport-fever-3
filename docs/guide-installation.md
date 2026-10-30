# Guide d'installation et de jeu : Transport Fever 3 x Archipelago

Ce guide s'adresse à un joueur qui n'a jamais vu le projet. Il décrit comment tout est installé, ce que chaque morceau fait, comment choisir l'année de départ, et quoi faire quand ça ne marche pas.

> Statut : tranche minimale, testée en local sur Windows 11 avec Archipelago 0.6.8 et Transport Fever 3 (Steam). Ce n'est pas proposé au dépôt officiel d'Archipelago.

## 1. Comment ça marche

```
Serveur Archipelago  <->  Client (dans le Launcher)  <->  deux fichiers  <->  Mod dans Transport Fever 3
```

- Le **monde** (`transport_fever_3.apworld`) dit à Archipelago quels items et quels checks existent.
- Le **client** se connecte au serveur et écrit dans un fichier `inbox` l'état voulu (items reçus, options). Il lit un fichier `outbox` pour envoyer les checks.
- Le **mod** tourne dans le jeu. Toutes les 2 secondes, il lit l'`inbox`, verrouille ou déverrouille les modes et les véhicules, applique l'argent et les pièges, puis écrit l'`outbox` (checks atteints, année du jeu, battement).

Le jeu ne laisse pas les mods lire ou écrire des fichiers librement : ils n'ont accès qu'à un dossier fixe, `towns_industries`, dans les données utilisateur de TF3. C'est le dossier d'échange.

## 2. Ce qu'il faut

- Transport Fever 3 (Steam), version avec les outils de mod (c'est le cas de la version normale).
- Archipelago 0.6.x, installé selon la [documentation officielle](https://archipelago.gg/tutorial/Archipelago/setup/en).
- Les deux livrables du projet :
  - `dist/transport_fever_3.apworld` (le monde) ;
  - `tf3_mod/archipelago_tf3_1/` (le mod).

Pour reconstruire le monde : `python scripts/build_world.py`.

## 3. Installer le monde

Ajouter un `.apworld` à Archipelago est décrit dans la [documentation officielle](https://archipelago.gg/tutorial/Archipelago/setup/en) (Launcher, **Install APWorld**, puis redémarrage du Launcher). Ici, le fichier est `dist/transport_fever_3.apworld`, et l'outil à repérer ensuite dans le Launcher s'appelle **Transport Fever 3 Client**.

## 4. Installer le mod dans le jeu

**Ferme Transport Fever 3 avant.** Le mod s'installe comme un **nouveau dossier** dans le dossier des mods utilisateur ; ni l'installation du jeu ni tes sauvegardes ne sont touchées.

Avec le script (recommandé) :

```
python scripts/install_mod.py          # première installation
python scripts/install_mod.py --update # mise à jour d'une copie déjà installée
```

Le script refuse de s'exécuter si le jeu tourne, et ne copie qu'un dossier. Il détecte le dossier des mods ; sinon passe `--mods-dir`.

À la main : copie le dossier `tf3_mod/archipelago_tf3_1` dans

```
C:\Program Files (x86)\Steam\userdata\<ton id Steam>\3493540\local\mods\
```

Le dossier de ce mod doit s'appeler exactement `archipelago_tf3_1`. Le dossier `save`, juste à côté, ne doit jamais être modifié.

Au lancement de TF3, le mod « Archipelago for Transport Fever 3 » apparaît dans le gestionnaire de mods ; il doit être **activé à la création de la partie**.

Pour le retirer : supprime ce dossier de `mods` (jeu fermé).

## 5. Créer la partie dans Transport Fever 3

Une partie Archipelago est une **partie dédiée** : un slot, un seed. On ne branche pas le mod sur une sauvegarde existante.

1. Nouvelle partie libre (bac à sable), avec le mod activé.
2. **Année de départ : le plus tard possible, 2000 ou plus.** Le maximum proposé est 2020.

### Pourquoi l'année de départ compte

Le jeu cache de lui-même les véhicules (et les stations, voies…) dont l'année de sortie n'est pas arrivée. Les filtres du mod ne peuvent que **cacher** davantage : ils ne peuvent pas montrer un véhicule que le jeu cache déjà. Dans une partie qui démarre en 1890, un train de 1950 serait inatteignable pour un item, et attendre que les années passent contredit l'idée d'une partie plus rapide.

En démarrant en 2020, tout est disponible par la date, et ce sont les items du multiworld qui verrouillent. Le mod retire aussi les dates de fin des véhicules (comme le mod officiel « véhicules sans année de fin »), pour que les vieux véhicules restent en vente.

Si l'année est inférieure à 2000, le client affiche un avertissement dans sa fenêtre : recrée la partie avec une année plus tardive. Le mod ne règle jamais la date lui-même.

## 6. Régler les options (YAML)

Le fonctionnement des YAML (modèle du Launcher, dossier `Players`, poids et valeurs aléatoires) est décrit dans la [documentation officielle des réglages](https://archipelago.gg/tutorial/Archipelago/advanced_settings/en). Ce monde n'ajoute que ses propres options, listées ci-dessous.

Principales options (voir le README pour la liste complète et un exemple) :

- **Goals** : `goal_population`, `goal_company_level`, `goal_passengers`, `goal_cargo`. 0 désactive un goal. La partie est gagnée quand **tous** les goals actifs sont atteints. Au moins un doit rester actif.
- **Checks** : paliers de population, de passagers et de fret (nombre, première et dernière valeur), niveaux d'entreprise, livraisons par cargo, première ligne de chaque mode.
- Il faut au moins autant de checks que d'items de progression, sinon la génération s'arrête avec un message qui donne le nombre.

Les mesures du jeu : la **population** est lue par l'expérience de la compagnie (égale à la population totale), les passagers et le fret par les totaux historiques de la barre du jeu.

## 7. Générer, héberger, se connecter

Ces étapes sont celles d'Archipelago en général : voir la [documentation officielle](https://archipelago.gg/tutorial/Archipelago/setup/en). Deux points propres à ce client :

- L'outil à lancer est **Transport Fever 3 Client**. Dans son champ d'adresse, **efface tout** le texte par défaut avant de taper l'adresse du serveur, sans quoi la connexion échoue.
- Il affiche « Game connected » dès que le mod répond. Archipelago libère automatiquement les items restants quand un joueur termine son goal : c'est normal, tout se déverrouille alors dans le jeu.

## 8. Dans le jeu

- Sans item reçu : la **route** est libre, le **tram, le rail, l'eau et l'air** sont verrouillés, et seuls les véhicules les plus anciens (avant 1920) sont en vente.
- Les items de **mode** déverrouillent les menus (stations, dépôts, voies, signaux) et les véhicules de ce mode. Les items « véhicules progressifs » ajoutent deux tranches : 1920 à 1960, puis après 1960.
- Les items « **niveau d'entreprise +1** » accordent un niveau, avec les avantages du jeu.
- L'**argent** arrive en écritures comptables ; les pièges retirent de l'argent (perte de 50 000 ou de 250 000).
- Les effets d'argent sont appliqués **une seule fois**, mais ils sont liés au seed, pas à la sauvegarde : si tu recharges une vieille sauvegarde, l'argent déjà reçu ne revient pas.
- Chaque item reçu et chaque check envoyé est annoncé par une **notification** du jeu avec le logo d'Archipelago (en haut de l'écran, puis dans l'onglet des notifications) : « Rail Transport from Alice (son check) », « Population reached 2,500 »… Au chargement d'une partie, rien n'est annoncé de ce qui était déjà reçu. Les items et checks apparaissent aussi dans la fenêtre du client.

## 9. Quand ça ne marche pas

| Symptôme | Cause probable | Que faire |
|---|---|---|
| Le client n'apparaît pas dans le Launcher | Monde non installé ou Launcher pas redémarré | Refaire **Install APWorld**, relancer le Launcher |
| Erreur de connexion avec `archipelago.gg:...` dans le champ | Texte par défaut non effacé | Effacer tout le champ, retaper l'adresse |
| La génération s'arrête sur « only give N checks » | Pas assez de checks pour les items | Augmenter les options de checks |
| La génération s'arrête sur « no goal is active » | Les quatre goals sont à 0 | Mettre un goal au-dessus de 0 |
| « Waiting for the game mod » | Le mod n'a pas écrit l'`outbox` de ce seed | Vérifier que le mod est actif et que la partie est lancée |
| « The game mod is not answering » | Le jeu est fermé ou en pause longue | Relancer le jeu |
| « user data not found » | Dossier de données de TF3 introuvable (Steam installé ailleurs) | Dans le client, taper `/folder <chemin du dossier towns_industries>` |
| Avertissement sur l'année du jeu | Partie créée avant 2000 | Recréer la partie, année de départ la plus tardive |
| Le jeu refuse de démarrer : « essayez de retirer le mod » | Erreur dans un script de mod | Lire `...\3493540\local\crash_dump\error.json` et retirer le mod en attendant |
| Aucun véhicule récent malgré les items | Partie d'avant 2000 | Voir « Année de départ » ci-dessus |

Fichiers utiles :
- le journal du jeu : `...\3493540\local\crash_dump\stdout.txt` (les lignes du mod commencent par `ARCHIPELAGO`) ;
- les fichiers d'échange : `...\3493540\local\towns_industries\archipelago_tf3_inbox.lua` et `archipelago_tf3_outbox_<seed>.lua` (un fichier par seed), lisibles dans un éditeur de texte.

## 10. Limites actuelles

- Cargos du climat tempéré uniquement.
- Le tram, l'eau et l'air n'ont pas tous été vérifiés dans les menus ; voir `docs/superpowers/plans/e2e-checklist.md`.
- Pas de fenêtre de suivi dans le jeu (seulement des notifications).
- Plateforme : PC Windows uniquement.
