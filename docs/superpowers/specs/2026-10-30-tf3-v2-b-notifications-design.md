# V2, chantier B : notifications dans le jeu

Date : 2026-10-30. Branche : `v2`. Complète la spécification de la V1.

## Décision

Chaque **item reçu** et chaque **check envoyé** est annoncé par une notification du jeu, avec le logo d'Archipelago.

- Une notification est faite d'une **ressource** (`ap_notification.res.lua`, type `notification`, style « Info ») et d'un **script** (`ap_notification.script.lua`) qui renvoie titre, texte et icône. Elle s'envoie avec `api.cmd.sendCommand(api.cmd.makeScriptingSendEventCmd("", "Notifications", "add", {type = "archipelago_tf3_1::/ap_notification.script", params = {title, text}, autoDismissDuration = 8000}))`.
- L'icône (`assets/archipelago_icon.png`, le logo fourni par l'utilisateur) est convertie par `scripts/make_icon.py` en `ap_icon@2x.tga` (TGA 32 bits de 64 pixels, couleurs et transparence conservées). Le jeu charge `nom.tga` depuis le fichier `nom@2x.tga`.
- Les messages sont calculés par le module pur `ap_notify.lua` (testé sans le jeu) à partir de ce qui a changé depuis le tour précédent :
  - item reçu : `Rail Transport from Alice (Alice's chest)` ; pour un check de ce joueur-ci, le texte lisible du check : `Rail Transport (Population reached 2,500)` ;
  - check envoyé : `Population reached 2,500`, `First rail line built`, `Delivered 100 iron ore`… ;
  - **le premier tour d'un seed ne notifie rien** (base silencieuse) : recharger une partie ne rejoue pas ce qui est déjà reçu ;
  - au plus **5 notifications par tour**, la dernière résume le reste (`and 3 more`).
- Pour nommer l'émetteur, l'`inbox` porte un `log` ordonné `{item, from | own, where}` fabriqué par le client à partir de ce que le serveur envoie (joueur et emplacement de chaque item reçu). Sans `log` (ancien client), le mod retombe sur les décomptes d'items.

## Vérifié en jeu

Check de population (en haut de l'écran, logo en couleurs) et item « Rail Transport » (en haut de l'écran et dans l'onglet des notifications). Un premier essai où l'item n'est allé que dans l'onglet n'a pas été reproduit ; cause probable : un menu ouvert à ce moment-là.
