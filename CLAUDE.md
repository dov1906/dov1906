# Contexte pour Claude : projet Dira Tel Aviv

Dov fait son alyah (France → Israël). Il cherche un appartement à Tel Aviv avec sa cousine. Ce repo contient le tracker qu'on a construit ensemble (dossier `dira-tlv/`). Réponds à Dov en français, sur un ton direct et décontracté.

## Règles de recherche (validées par Dov)
- 3 pièces israéliennes (salon + 2 chambres). Le nombre de salles de bain est indifférent.
- **Loyer minimum : 8 100 ₪** (« pas d'appartement miteux »).
- **Budget maximum : 10 500 ₪ par mois TOUT COMPRIS** (loyer + arnona + vaad bayit), soit un loyer d'environ 8 100 à 10 000 ₪.
- Tout Tel Aviv, avec la priorité au centre (Lev Ha'ir, Vieux et Nouveau Nord, Florentin, Neve Tzedek, Kerem HaTeimanim, Rothschild, Bavli). **Pas de Yafo, pas de Ramat Aviv.**
- Entrée **à partir du 8 décembre 2026**, location longue durée. Visites possibles tout de suite.
- Les deux travaillent (Dov : ingénieur biomédical / développeur). Pas d'animaux.
- Le mamad est un gros plus, l'abri dans l'immeuble est acceptable. À confirmer avec Dov : mamad obligatoire ou non.

## Ce qui existe
| Élément | Où |
|---|---|
| Tracker partagé (claude.ai) : annonces, score, messages hébreu/EN/FR, WhatsApp, Gmail, photos, agences, dossier | https://claude.ai/artifact/1EUHH9DjoTxyPys7XjcZY1 (base `apts`, `agencies`, `settings/profile`, `settings/dossier`) |
| App installable (écran d'accueil, GitHub Pages) | https://dov1906.github.io/dov1906/dira-tlv/app/ |
| Scan automatique 3×/jour (7 h 47, 12 h 47, 20 h 47, heure d'Israël) | tâche planifiée « Scan appartements Tel Aviv » (trig_01EW7SUxG4KcWPeUH44h152Z) qui exécute `dira-tlv/SCAN.md` |
| Code | branche `claude/tel-aviv-apartment-tracker-wo8lg8`, dossier `dira-tlv/` (voir `dira-tlv/README.md`) |

Les données personnelles (téléphone de Dov, notes, étapes) sont **uniquement** dans la base privée du tracker, jamais dans ce repo, qui est public.

## Fonctionnement
- `index.html` est la source unique. Elle est publiée telle quelle comme artefact, et `build.py` en génère `app/` (manifest, service worker, icônes).
- Dans claude.ai, la page utilise la base partagée. Hébergée sur Pages, elle lit `app/data/listings.json` et garde l'état sur le téléphone.
- `export_listings.py` passe la base à `app/data/listings.json` : uniquement les annonces scannées, sans notes ni étapes.
- `fetch_photos.py` et l'étape 4 de `SCAN.md` récupèrent les photos (Realta → img.yad2.co.il). Les photos sont envoyées comme assets de l'artefact (`photoAssets`).
- Yad2, Madlan, dili et Homeless refusent la lecture directe. La meilleure source passe par Exa : realta.co.il, qui reprend Yad2 et Facebook.
- Les numéros des annonceurs sont presque toujours masqués. La fiche propose « Voir le numéro sur Yad2/Facebook » (`sourceUrl`), puis on colle le numéro et WhatsApp s'active.

## Points ouverts (au 25/11/2026)
- **Les scans planifiés ne peuvent pas pousser sur GitHub** : le repo n'est pas dans les sources de la tâche. Dov doit l'ajouter dans claude.ai (tâche planifiée → sources / repositories). En attendant, l'app n'est à jour que quand une session interactive exporte (dernier export : 50 annonces, le 25/11).
- **Agences** : 7 contactées le 24/11.
  - ProperTLV (Tovi) : réponse faite, frais = 1 mois + TVA.
  - Casael : écrire à leur agent Noam au 054-779-1193 (WhatsApp).
  - Evenis (Yael) : demande le numéro de Dov, **réponse pas encore envoyée**.
  - Ronkin (Steve) : cherche pour nous.
  - Pas encore de réponse : My TLV, Lev Florentin, Davidson.
- Questions encore posées à Dov :
  - surveiller Gmail pour les annonces reçues par mail ;
  - prénom de la cousine, et partager le tracker avec elle ;
  - réponses aux agences : brouillons ou envoi direct ;
  - exclure Shapira et Yad Eliyahu ou non ;
  - mamad obligatoire ou non ;
  - rappels de visite dans Google Agenda.
