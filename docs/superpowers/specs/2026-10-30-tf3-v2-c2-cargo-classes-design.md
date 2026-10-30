# V2, chantier C, partie 2 : classes de cargo

Date : 2026-10-30. Branche : `v2`. Complète la spécification de la V1.

## Constat (fichiers du jeu)

Les véhicules de fret déclarent des **classes de cargo** : `BULK`, `FLATBED`, `GOODS`, `LIQUID` et `UNIVERSAL` (tout cargo), plus `PASSENGERS`. Sur 306 véhicules, les camions sont 12 universels, 10 liquides, 10 marchandises, 9 vrac et 7 plateau ; les wagons 6 marchandises, 6 liquides, 5 vrac, 5 plateau, 5 universels. Chacun de nos 28 cargos appartient à une seule classe spécialisée, plus Universal : vrac (clay, coal, grain, iron_ore, sand, stone), plateau (logs, machines, planks, sheet_metal, steel, vehicles), marchandises (douze cargos), liquides (chemicals, crude_oil, dyes, fuel).

## Décision

- **Quatre items à un exemplaire** : `Cargo Class: Bulk`, `Cargo Class: Flatbed`, `Cargo Class: Goods`, `Cargo Class: Liquid`. Classés « utiles » (pas de la logique).
- Les véhicules **universels** et ceux qui transportent des **passagers**, ainsi que les véhicules sans cargo (locomotives), ne sont **jamais** verrouillés par classe. Un véhicule routier universel de la première tranche existe (petit chariot de 1885, chariot moyen de 1893, camion à vapeur de 1905, avec les dates de fin retirées par le mod) : **tout cargo peut être transporté par route dès le départ**, les checks de livraison et le goal « fret » restent accessibles sans item de classe.
- Un véhicule de fret spécialisé est caché tant que le joueur n'a pas l'item d'**au moins une** de ses classes (un navire vrac, plateau et marchandises est libéré par n'importe laquelle des trois). Cela s'ajoute au verrou du mode et à celui de la tranche d'année : un item de classe ne les contourne jamais.
- Le mod lit les classes d'un modèle dans `metadata.transportVehicle.compartments[].loadConfigs[].cargoEntry.cargoTypeSet.cargoClassesIncluded`.

## Vérification

Tests : verrou par classe (une classe, plusieurs, universel, passagers, sans cargo), non contournement du mode et de la tranche, items et classification, accessibilité des livraisons. En jeu : le journal du mod liste la répartition des classes par mode, puis un camion spécialisé n'apparaît qu'avec l'item de sa classe.
