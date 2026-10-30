# V2, chantier A : pièges en perte d'argent

Date : 2026-10-30. Branche : `v2`. Complète la spécification de la V1 (`2026-10-30-tf3-archipelago-slice-design.md`).

## Décision

Le prêt forcé n'est pas le meilleur piège (décision de l'utilisateur) : les pièges sont des **pertes d'argent**.

| Piège | Montant |
|---|---|
| `Money Loss (small)` | -50 000 |
| `Money Loss (medium)` | -250 000 |

- Dans le remplissage du monde, un piège tombe dans environ 15 % des cases libres ; le petit est tiré trois fois sur quatre (`data.TRAP_WEIGHTS = (3, 1)`).
- Pas de grande perte : 1 000 000 peut mettre une compagnie débutante en faillite.
- Un piège est un effet `money_loss` du fichier d'échange, appliqué une seule fois comme tout effet ponctuel.
- Le **prêt forcé disparaît** du monde, du fichier d'échange (le genre d'effet `loan`) et du mod.
- Les seeds de la V1 ne sont plus compatibles (noms d'items changés) : la V1 n'a pas d'utilisateur, aucune migration.

## Vérification

Tests : traps en effets `money_loss` avec leurs montants, plus d'item « Forced Loan », tirage du remplissage (environ 15 %, petit plus fréquent que moyen, jamais de prêt), classification `trap`, le mod ne mentionne plus le prêt. En jeu : un item `Money Loss (medium)` retire 250 000 de la compagnie.
