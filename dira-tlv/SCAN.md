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

## Sources (avec `mcp__Exa__web_search_exa` et `mcp__Exa__web_fetch_exa` ; jamais curl)
Les pages de liste (Madlan, Homeless) ne donnent ni lien ni date par annonce : la base, ce sont les **recherches Exa** qui renvoient des pages d'annonces individuelles, puis la lecture de chaque page de détail.
1. 6 à 8 recherches `web_search_exa` (numResults 10), en hébreu et en anglais, qui ciblent des annonces individuelles récentes sur realta.co.il (la source la plus productive), dili.co.il, madlan.co.il, telavivrent.com, ad.co.il, komo.co.il, zipika.com, onmap.co.il, winwin.co.il, janglo.net. Varie par quartier. Exemples :
   - « דירת 3 חדרים להשכרה בתל אביב ללא תיווך פורסם השבוע »
   - « דירה להשכרה 3 חדרים הצפון הישן ממ"ד », « … פלורנטין », « … לב תל אביב », « … כרם התימנים », « … הצפון החדש »
   - « 3-room apartment for rent Tel Aviv no broker posted days ago », « telavivrent 3 rooms apartment mamad »
2. Lis aussi les pages de liste Realta par quartier, si une recherche en renvoie, pour récupérer les liens de plusieurs annonces d'un coup.
3. Pour chaque annonce prometteuse, ouvre sa page de détail (`web_fetch_exa`, maxCharacters 6000) pour récupérer la rue, l'étage, l'ascenseur, le mamad ou l'abri, le balcon, la clim, le meublé, le parking, l'arnona, le vaad bayit, la date d'entrée, la date de publication, le contact et le type (particulier ou agence). Les contacts sont souvent masqués par l'agrégateur : laisse-les vides, le lien suffit.
4. Yad2 et Facebook bloquent la lecture directe : passe par les agrégateurs qui les reprennent.

Règles de remplissage :
- `source` = la source d'origine si la page l'indique (Yad2, Facebook, Madlan…), sinon le site (« Realta », « dili », « TelAvivRent »…). Mentionne toujours l'agrégateur dans `resume`.
- `publishedAt` = la date de publication ; à défaut, la date de mise à jour (et écris « date = mise à jour » dans `resume`) ; à défaut, laisse vide.
- Quartiers absents de la liste (Neve Shaanan, Nahalat Yitzhak, HaMishtala, Givat Herzl…) : utilise « Autre » et écris le vrai nom dans `titre`. Noah, Kikar Bazel et les alentours de l'Université sont à compter comme Ramat Aviv, donc exclus.

## Déduplication
Avant d'écrire, lis toute la collection `apts` (les autres collections, comme `agencies`, ne comptent pas) (`ArtifactData` action `list`, limit 1000). Une annonce est un doublon si elle a la même `url`, ou la même rue (même sans numéro) avec un prix à ±300 ₪ et la même surface ou le même étage quand on les connaît. Ne réécris jamais une annonce existante : la fiche de Dov contient ses notes et son étape.

## Écriture
Un `ArtifactData` `batch` d'opérations `set` (sans `if_version`, ce sont des créations), collection `apts`. `doc_id` = `auto-<site>-<identifiant de l'annonce dans l'URL>`, ou à défaut `auto-<site>-<rue en ascii>-<prix>` (lettres minuscules, chiffres et tirets uniquement). Champs :
```
titre: "3 pièces <rue>" (français), rue: lettres latines, rueHe: en hébreu,
quartier: un de ["Lev Ha'ir (centre)","Vieux Nord","Nouveau Nord","Florentin","Neve Tzedek","Kerem HaTeimanim","Montefiore / Rothschild","Kikar HaMedina","Bavli","Yad Eliyahu","Sarona / Kirya","Shapira / Sud","Ramat Hahayal","Autre"],
prix, arnona, vaad, pieces, surface, etage: nombres sous forme de texte ("" si inconnu),
ascenseur: "oui"|"non"|"", mamad: "oui"|"abri"|"non"|"", animaux: "oui"|"non"|"",
balcon, clim, meuble, parking: booléens,
dispo: texte, contactNom, contactTel, contactEmail, contactType: "proprio"|"agent"|"",
url: lien de l'annonce (https), source: voir les règles de remplissage,
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
