# V2, chantier E, partie 2 : missions du jeu comme checks

Date : 2026-10-30. Branche : `v2`.

## Constat

Les « missions » sont les offres du jeu (par exemple « Relier des villes »), appelées subventions. Elles vivent dans le script de jeu `::/game_mechanics/subventions/subventions.gs` : `state_native` contient les listes `proposedSubventions`, `activeSubventions`, `completedSubventions` et `failedSubventions`, chaque entrée ayant un `uid`. L'interface du jeu lit cet état de la même façon. Le jeu envoie aussi l'événement `Subvention/OnCompleted`, mais on ne le reçoit qu'après abonnement, et seulement dans une nouvelle partie : on ne s'appuie donc pas dessus.

## Décision

- Le mod relève à chaque passage (2 s) les `uid` de `completedSubventions` et les retient dans l'outbox (`missions`), chacun une seule fois : une mission qui quitte la liste du jeu reste comptée, et le décompte survit au rechargement.
- Nouvelle option `mission_checks` (0 à 30, 3 par défaut) : les checks `mission:1`, `mission:2`… sont « N missions accomplies », quel que soit le type de mission.
- Aucune condition d'accès : une offre se remplit avec les véhicules routiers de départ.
- Les ids de lieux `mission:N` sont ajoutés à la fin de la table, les ids existants ne bougent pas.
- La notification est celle des contrats : « Missions completed: N », avec la récompense.

## Vérification

Tests : évaluation des checks, fusion des `uid`, texte de notification, lieux et option, accès. En jeu : accepter puis accomplir une offre fait apparaître le contrat « Missions completed: 1 ». Si la lecture de `completedSubventions` échoue, le décompte reste à zéro et le problème est écrit dans le journal du mod.
