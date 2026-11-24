# Scan automatique des annonces (Dira Tel Aviv)

Tu scannes le marché locatif de Tel Aviv pour Dov et sa cousine, olim de France, et tu ajoutes les nouvelles annonces pertinentes dans leur tracker.

Tracker : https://claude.ai/artifact/1EUHH9DjoTxyPys7XjcZY1 (outil `ArtifactData`, collection `apts`).

## Critères
- Location longue durée (pas de sous-location ni de location courte : exclure סאבלט, sublet, Airbnb, « לתקופה קצרה »).
- 3 à 3,5 pièces israéliennes (salon + 2 chambres). Accepter 4 pièces seulement si le loyer est sous 11 000 ₪.
- Loyer entre 6 000 et 11 500 ₪/mois. Au-dessus de 11 000 ₪, ne garder que si c'est exceptionnel (mamad, central).
- Tel Aviv uniquement. EXCLURE tout Yafo (יפו, עג'מי, נווה גולן, גבעת התמרים, יפו ד', צהלון, שיכוני חיסכון, יפו העתיקה) et tout Ramat Aviv (רמת אביב, רמת אביב ג', רמת אביב החדשה, נווה אביבים). Hors Tel Aviv (Ramat Gan, Givatayim, Bat Yam, Holon…) : exclure.
- Priorité au centre : Lev Ha'ir, Vieux Nord, Nouveau Nord, Florentin, Neve Tzedek, Kerem HaTeimanim, Montefiore/Rothschild, Kikar HaMedina, Bavli. Le sud-est (Shapira, Hatikva, Kfar Shalem…) et l'extrême nord-est sont acceptés mais moins prioritaires.
- Annonces publiées dans les 7 derniers jours de préférence (jamais plus de 21 jours).

## Sources (avec `mcp__Exa__web_fetch_exa` et `mcp__Exa__web_search_exa` ; ne pas utiliser curl)
1. Madlan : https://www.madlan.co.il/for-rent/%D7%AA%D7%9C-%D7%90%D7%91%D7%99%D7%91-%D7%99%D7%A4%D7%95-%D7%99%D7%A9%D7%A8%D7%90%D7%9C/3-bd (et la variante `/secure-room`). Lire avec maxCharacters ≈ 15000.
2. Homeless : https://www.homeless.co.il/rent/city=%D7%AA%D7%9C%20%D7%90%D7%91%D7%99%D7%91$$iNumber4=5 (le tableau contient la date de mise à jour).
3. Recherches Exa (3 à 5 requêtes, en hébreu et en anglais) qui ciblent des annonces individuelles récentes sur dili.co.il, realta.co.il, dorin.app, zipika.com, ad.co.il, komo.co.il, onmap.co.il, winwin.co.il, janglo.net, homeless.co.il, madlan.co.il et yad2.co.il. Ces agrégateurs reprennent aussi des annonces des groupes Facebook. Exemples :
   - « דירת 3 חדרים להשכרה בתל אביב ללא תיווך פורסם השבוע »
   - « 3-room apartment for rent Tel Aviv no broker posted days ago »
   - « דירה להשכרה 3 חדרים הצפון הישן / לב העיר / פלורנטין / כרם התימנים ממ"ד »
4. Pour chaque annonce prometteuse, ouvre sa page de détail (web_fetch_exa) pour récupérer : rue, étage, ascenseur, mamad/abri, balcon, clim, meublé, parking, arnona, vaad, date d'entrée, date de publication, nom, téléphone et email du contact, et le type (particulier ou agence).
   Yad2 et Facebook bloquent souvent la lecture directe : ne pas insister, passer par les agrégateurs.

## Déduplication
Avant d'écrire, lis toute la collection `apts` (`ArtifactData` action `list`, limit 1000). Une annonce est un doublon si elle a la même `url`, ou la même rue + numéro avec un prix à ±300 ₪. Ne réécris jamais une annonce existante : la fiche de Dov contient ses notes et son étape.

## Écriture
Un `ArtifactData` `batch` d'opérations `set` (sans `if_version`, ce sont des créations), collection `apts`. `doc_id` = `auto-<source>-<identifiant de l'annonce ou rue-prix en ascii>` (lettres, chiffres et tirets uniquement). Champs :
```
titre: "3 pièces <rue>" (français), rue: lettres latines, rueHe: en hébreu,
quartier: un de ["Lev Ha'ir (centre)","Vieux Nord","Nouveau Nord","Florentin","Neve Tzedek","Kerem HaTeimanim","Montefiore / Rothschild","Kikar HaMedina","Bavli","Yad Eliyahu","Sarona / Kirya","Shapira / Sud","Ramat Hahayal","Autre"],
prix, arnona, vaad, pieces, surface, etage: nombres sous forme de texte ("" si inconnu),
ascenseur: "oui"|"non"|"", mamad: "oui"|"abri"|"non"|"", animaux: "oui"|"non"|"",
balcon, clim, meuble, parking: booléens,
dispo: texte, contactNom, contactTel, contactEmail, contactType: "proprio"|"agent"|"",
url: lien de l'annonce (https), source: "Madlan"|"Homeless"|"Yad2"|"Komo"|"Facebook"|"Autre" (+ nom de l'agrégateur dans resume),
publishedAt: date de publication ISO (AAAA-MM-JJ) estimée depuis la page (« il y a 3 jours » → calcule-la), 
createdAt: maintenant (ISO), updatedAt: maintenant,
status: "repere", auto: true, seen: false,
resume: 2 phrases en français (points forts / points faibles / pièges, y compris « via agence : frais probables »),
annonceTexte: texte original de l'annonce (max 3000 caractères),
checklist: {}, history: [{"t": maintenant ISO, "a": "Trouvée par Claude (scan auto)"}]
```
Maximum 25 annonces par scan, les plus pertinentes d'abord (centre, mamad, récente, prix bas).

## Compte rendu
Termine par un court résumé en français : le nombre d'annonces ajoutées, le top 3 (rue, prix, quartier, pourquoi), et les sources qui n'ont pas répondu. N'envoie aucun message à personne et ne contacte aucun propriétaire.
