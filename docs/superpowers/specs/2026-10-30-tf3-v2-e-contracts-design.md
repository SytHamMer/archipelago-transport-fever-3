# V2, chantier E : checks présentés comme des « contrats »

Date : 2026-10-30. Branche : `v2`.

## Constat

Le système de subventions du jeu est natif : `base/tealdef/game_mechanics/subventions/*.d.tl` ne contient que des définitions de types, la configuration passe par `advancedOptions.subventionMode` et des scripts empaquetés, et aucun point d'entrée ne permet à un mod d'ajouter ses propres cartes d'offre. La mission de campagne 06 ne fait que régler ce mode. Les contrats sont donc présentés par nos propres moyens : notifications et console du client.

## Décision

Les checks ne changent pas pour les règles du monde. Chacun est présenté comme un **contrat** : sans date de fin, sans pénalité, avec sa récompense visible avant de l'accomplir.

- **Scouting.** À la connexion, le client envoie `LocationScouts` (sans création de hint) pour tous les checks du joueur. Il en tire pour chacun l'item de la récompense et le joueur destinataire.
- **Inbox.** Une table `contracts`, indexée par l'identifiant du check, ajoutée à l'inbox : `{item, to, own}` (`own` : la récompense est pour nous). Sans réponse du scouting, la table est vide et les notifications restent celles d'aujourd'hui.
- **Notifications.** Un check rempli annonce « Archipelago : contrat rempli », avec le texte du contrat et la récompense. Exemple : « Population de 5 000 atteinte, récompense : Progressive Rail Vehicles pour Alice ». Les notifications d'items reçus gardent l'expéditeur et le contrat d'origine.
- **Console.** `/contracts` liste les contrats ouverts avec leur récompense, et le nombre de contrats remplis sur le total.

## Hors périmètre

Pas de fenêtre en jeu, pas de vraies subventions natives, pas de missions du jeu comme source de checks (plus tard).

## Vérification

Tests Python (conversion du scouting vers la table, inbox, `/contracts`), tests Lua (formulation avec et sans récompense connue), extension du test de bout en bout headless (la table `contracts` arrive dans l'inbox). En jeu : un contrat rempli affiche le texte et la récompense en notification.
