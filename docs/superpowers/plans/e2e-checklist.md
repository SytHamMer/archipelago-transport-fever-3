# Vérification de bout en bout (à faire avec le vrai Launcher)

Fait automatiquement (`scripts/e2e_headless.py`) : serveur local, vrai client sans interface, faux mod. Passe (« completed all of their games »).

Fait en jeu avec l'utilisateur (2026-10-30) : verrous au départ, déverrouillage du rail en direct, argent une seule fois, nouveau seed, niveau accordé, perte d'argent, tranches de véhicules (rail, puis route à partir de 2020).

## Reste à faire en jeu, dans l'ordre

1. [ ] `python scripts/build_world.py`, puis **Install APWorld** dans le Launcher.
2. [ ] « Transport Fever 3 Client » apparaît dans le Launcher et s'ouvre avec son interface.
3. [ ] **Generate Template Options** montre les options du monde ; un YAML avec `goal_population: 2500` seul génère un seed.
4. [ ] Partie libre neuve, départ 2020, mod actif ; **Host Game** local ; le client se connecte et affiche « Game connected ».
5. [ ] Un check réel (première ligne de bus) part au serveur ; l'item reçu s'applique dans le jeu.
6. [ ] Les goals actifs atteints : le serveur affiche la partie terminée.
7. [ ] Non vérifiés jusqu'ici : tram, eau et air (menus), piège « prêt forcé », checks de première ligne par mode et de livraison, tranche de rail à 1960.
8. [ ] Retirer les restes de test : `towns_industries\archipelago_probe_*` (déjà fait), mods de test.
