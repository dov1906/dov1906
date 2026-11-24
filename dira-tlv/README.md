# Dira Tel Aviv

Tracker de recherche d'appartement à Tel Aviv (3 pièces, de 8 100 à 11 000 ₪).

## Deux façons de l'ouvrir
1. **Dans claude.ai (artefact)** : https://claude.ai/artifact/1EUHH9DjoTxyPys7XjcZY1
   - Liste partagée avec ta cousine.
   - Analyse d'annonce par Claude, brouillons Gmail.
   - Photos enregistrées dans le tracker.
2. **App installable (écran d'accueil)** : le dossier `app/`, servi par GitHub Pages.
   - WhatsApp fonctionne directement et les photos s'affichent.
   - Tes étapes et notes restent sur le téléphone.
   - Installation sur iPhone : ouvre le lien dans Safari, puis Partager, puis « Sur l'écran d'accueil ».
   - Installation sur Android : ouvre le lien dans Chrome, puis le menu ⋮, puis « Installer l'application ».

## Scan automatique
Une tâche planifiée tourne 3 fois par jour (7 h 47, 12 h 47 et 20 h 47, heure d'Israël). Elle suit `SCAN.md` :
1. Elle cherche les nouvelles annonces et récupère leurs photos.
2. Elle les ajoute au tracker.
3. Elle exporte `app/data/listings.json`.

## Fichiers
- `index.html` : la page (source de l'artefact et de l'app).
- `build.py` : génère `app/`, avec le manifest, le service worker et les icônes.
- `export_listings.py` : génère `app/data/listings.json` (données publiques uniquement : ni notes, ni étapes).
- `fetch_photos.py` : télécharge et réduit les photos d'annonces.
- `SCAN.md` : les instructions du scan.
