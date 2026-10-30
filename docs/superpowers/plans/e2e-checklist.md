# Vérification de bout en bout (à faire avec le vrai Launcher)

Fait automatiquement (`scripts/e2e_headless.py`) : serveur local, vrai client sans interface, faux mod. Passe (« completed all of their games »).

Fait en jeu avec l'utilisateur (2026-10-30) : verrous au départ, déverrouillage du rail en direct, argent une seule fois, nouveau seed, niveau accordé, perte d'argent, tranches de véhicules (rail, puis route à partir de 2020).

Fait avec le vrai Launcher (2026-10-30, Archipelago 0.6.8) : le client apparaît et s'ouvre avec son interface, connexion à un serveur local, le goal (600 habitants) atteint est envoyé, le serveur libère le reste des items, et le mod déverrouille les menus de rail, tram, eau et air tout seul. Le client affiche « Sent N new checks » puis « Goal reached ».

## Reste à faire en jeu, dans l'ordre

1. [x] `python scripts/build_world.py`, puis **Install APWorld** dans le Launcher.
2. [x] « Transport Fever 3 Client » apparaît dans le Launcher et s'ouvre avec son interface.
3. [x] **Generate Template Options** montre les options du monde ; un YAML avec `goal_population: 2500` seul génère un seed.
4. [x] Partie libre neuve, départ 2020, mod actif ; **Host Game** local ; le client se connecte et affiche « Game connected ».
5. [x] Un check réel (première ligne de bus) part au serveur ; l'item reçu s'applique dans le jeu.
6. [x] Les goals actifs atteints : le serveur affiche la partie terminée.
7. [ ] Non vérifiés jusqu'ici : tram, eau et air (menus), checks de première ligne par mode et de livraison, tranche de rail à 1960.
8. [ ] Retirer les restes de test : `towns_industries\archipelago_probe_*` (déjà fait), mods de test.

9. [ ] Refaire un essai avec un goal plus haut (par exemple `goal_population: 5000`) pour voir la progression check par check, avant la libération automatique du serveur à la fin de la partie.
