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

# Vérification V2 (branche `v2`)

Fait automatiquement (2026-10-30) : 243 tests, monde construit (`dist/transport_fever_3.apworld`), multiworld à deux joueurs (Mathys et Alice, `players/*.yaml`) généré, `scripts/e2e_headless.py` passe (le goal de Mathys est reçu, des items partent chez Alice, la table `contracts` arrive dans l'inbox).

Fait en jeu avec l'utilisateur : pièges d'argent, notifications (items et checks, expéditeur), types de routes et de voies par tranche, outils, échangeurs par année, classes de cargo (aucune classe : seuls les véhicules universels, passagers et locomotives ; chaque item libère sa classe), contrat avec récompense dans la notification, mission du jeu comptée (`mission:1`).

## Reste à faire avec le vrai Launcher et le vrai jeu

1. [ ] Installer `dist/transport_fever_3.apworld` (Launcher, **Install APWorld**) ; le client s'ouvre.
2. [ ] **Host Game** avec `out/AP_*.zip` ; deux clients (Mathys, Alice) ou un seul client Mathys.
3. [ ] Partie libre neuve en 2020, mod actif ; le client affiche « Game connected ».
4. [ ] `/contracts` dans le client : « Contracts: 0/N done », puis les contrats ouverts avec leur récompense.
5. [ ] Un check réel de Mathys : la notification du jeu indique la récompense (item et joueur) ; `/contracts` descend d'un contrat.
6. [ ] Une récompense pour Alice (autre joueur) apparaît avec « for Alice ».
7. [ ] Un item de classe de cargo reçu libère les véhicules de sa classe.
8. [ ] Une mission du jeu accomplie compte pour `mission:N` (notification « Missions completed »).
9. [ ] Un piège (perte d'argent) et un gain, avec `money_scale` : montants divisés par deux pour Alice.
10. [ ] Fermer et rouvrir la partie : aucune notification rejouée, checks conservés.
11. [ ] Reconnexion du client : les contrats reviennent, aucun check perdu.
