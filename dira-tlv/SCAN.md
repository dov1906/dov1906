# Scan automatique des annonces (Dira Tel Aviv), version 2

Tâche autonome. Tu scannes le marché locatif de Tel Aviv pour Dov et sa cousine, olim de France, et tu ajoutes les nouvelles annonces pertinentes, avec leurs photos, dans leur tracker. Ne contacte personne et n'envoie aucun message.

Outils à charger avec ToolSearch : "select:mcp__Exa__web_search_exa,mcp__Exa__web_fetch_exa,WebFetch,WebSearch,ArtifactData,Artifact". Si Exa n'est pas disponible, utilise WebSearch et WebFetch. Ne lis jamais les sites d'annonces avec curl ou wget. curl sert seulement à télécharger les photos (étape 4). La date du jour est celle de la commande `date`.

Tracker : https://claude.ai/artifact/1EUHH9DjoTxyPys7XjcZY1 (outil `ArtifactData`, collection `apts`).

## Règles de Dov (strictes)
- **Loyer : 8 100 ₪ minimum, 11 000 ₪ maximum.** Jusqu'à 11 500 ₪ seulement si c'est exceptionnel (mamad + centre). Rien sous 8 100 : « pas d'appartement miteux ».
- Location longue durée uniquement. Exclure la sous-location et la location courte (סאבלט, sublet, Airbnb, « לתקופה קצרה »).
- 3 à 3,5 pièces israéliennes (salon + 2 chambres). 4 pièces seulement si le loyer reste dans la fourchette.
- Tel Aviv uniquement.
  - EXCLURE tout Yafo : יפו, עג'מי, נווה גולן, גבעת התמרים, יפו ד', צהלון, שיכוני חיסכון, יפו העתיקה.
  - EXCLURE tout Ramat Aviv : רמת אביב, רמת אביב ג', רמת אביב החדשה, נווה אביבים, ainsi que Noah, Kikar Bazel et les abords de l'Université.
  - EXCLURE hors Tel Aviv : Ramat Gan, Givatayim, Bat Yam, Holon…
- Priorité au centre : Lev Ha'ir, Vieux Nord, Nouveau Nord, Florentin, Neve Tzedek, Kerem HaTeimanim, Montefiore/Rothschild, Kikar HaMedina, Bavli. Le sud-est (Shapira, Hatikva, Kfar Shalem) est accepté mais moins prioritaire.
- Annonces publiées dans les 7 derniers jours de préférence, jamais plus de 21 jours.

## 1. Lire le tracker (pour éviter les doublons)
`ArtifactData` action `list`, collection `apts`, limit 1000, avec `out_dir` sur un dossier temporaire. Suis `next_cursor` s'il y en a.

Une annonce est un doublon si l'une de ces conditions est vraie :
- même `url` ou même `sourceUrl` ;
- même rue (même sans numéro), prix à ±300 ₪, et même surface ou même étage quand on les connaît.

Ne réécris jamais une annonce existante : la fiche de Dov contient ses notes et son étape.

## 2. Chercher
Les pages de liste (Madlan, Homeless) ne donnent ni lien ni date par annonce. Il faut donc :
- faire 6 à 8 recherches (`web_search_exa`, numResults 10), en hébreu et en anglais, en variant les quartiers ;
- cibler des annonces individuelles récentes sur realta.co.il (la source la plus productive), dili.co.il, madlan.co.il, telavivrent.com, ad.co.il, komo.co.il, zipika.com, onmap.co.il, winwin.co.il et janglo.net.

Exemples de requêtes :
- « דירת 3 חדרים להשכרה בתל אביב ללא תיווך פורסם השבוע »
- « דירה להשכרה 3 חדרים הצפון הישן ממ"ד », puis la même avec פלורנטין, לב תל אביב, כרם התימנים, הצפון החדש
- « 3-room apartment for rent Tel Aviv no broker posted days ago »

Yad2 et Facebook bloquent la lecture directe : passe par les agrégateurs qui reprennent leurs annonces.

## 3. Détails de chaque annonce retenue
1. Lis la page de détail avec `web_fetch_exa` (maxCharacters 6000) pour avoir le texte.
2. Lis-la aussi avec **WebFetch**, avec ce prompt : « Liste les URL https des photos de CET appartement (sans les annonces similaires, les logos ni les cartes), le numéro de téléphone de l'annonceur s'il apparaît, et le lien vers l'annonce d'origine (yad2.co.il/realestate/item/…, facebook.com/groups/…/posts/…), décodé s'il passe par une redirection go.realta.co.il. »
   - Realta donne en général les photos (img.yad2.co.il) et le lien Yad2.
   - dili et Madlan refusent WebFetch (erreur 403) : dans ce cas, pas de photos.
3. Ne rapporte que des URL qui apparaissent vraiment dans les résultats des outils.
4. Le numéro affiché par Realta (+972-54-772-7104) et celui de dili (02-376-6666) sont ceux des sites eux-mêmes, pas des annonceurs : ne jamais les enregistrer comme contact.

## 4. Photos (au plus 4 par annonce)
Pour chaque annonce, télécharge les photos en https, hors fbcdn qui expire, et réduis-les :
```bash
mkdir -p /tmp/ph && cd /tmp/ph
curl -s -f -L --max-time 20 -o "<doc_id>-1.raw" "<url photo>"   # une commande par photo
python3 -c "
from PIL import Image; import glob, os
for f in glob.glob('*.raw'):
    try:
        im=Image.open(f); im.thumbnail((900,900)); im.convert('RGB').save(f[:-4]+'.jpg',quality=78,optimize=True)
    except Exception as e: print('skip',f,e)
    os.remove(f)"
```
Ensuite :
1. Envoie les .jpg avec l'outil `Artifact` : `url` = le tracker, `asset: true`, `file_paths` (25 fichiers maximum par appel).
2. Garde, pour chaque fichier, l'URL `/_blob/<id>` renvoyée.
3. Ces URL vont dans `photoAssets`, et les URL d'origine (hors fbcdn) dans `photos`.

Si une étape échoue, continue sans photos pour cette annonce.

## 5. Écriture dans le tracker
Fais un `ArtifactData` `batch` d'opérations `set`, sans `if_version` puisque ce sont des créations, dans la collection `apts`.

`doc_id` = `auto-<site>-<identifiant de l'annonce dans l'URL>`, ou à défaut `auto-<site>-<rue en ascii>-<prix>`. Uniquement des minuscules, des chiffres et des tirets.

Champs :
```
titre: "3 pièces <rue>" en français (ajoute le vrai quartier si quartier = "Autre")
rue: en lettres latines
rueHe: en hébreu
quartier: un de ["Lev Ha'ir (centre)","Vieux Nord","Nouveau Nord","Florentin","Neve Tzedek","Kerem HaTeimanim","Montefiore / Rothschild","Kikar HaMedina","Bavli","Yad Eliyahu","Sarona / Kirya","Shapira / Sud","Ramat Hahayal","Autre"]
prix, arnona, vaad, pieces, surface, etage: nombres sous forme de texte ("" si inconnu)
ascenseur: "oui"|"non"|""
mamad: "oui"|"abri"|"non"|""
animaux: "oui"|"non"|""
balcon, clim, meuble, parking: booléens
dispo: texte
contactNom: en lettres latines
contactNomHe: en hébreu
contactTel, contactEmail: "" si non trouvé
contactType: "proprio"|"agent"|""
url: la page de l'annonce (https)
sourceUrl: l'annonce d'origine Yad2/Facebook/Madlan, ou ""
source: la source d'origine si elle est connue (Yad2, Facebook, Madlan…), sinon le site (Realta, dili, TelAvivRent…)
photos: [URL https d'origine]
photoAssets: ["/_blob/…"]
publishedAt: AAAA-MM-JJ ; à défaut la date de mise à jour (écrire « date = mise à jour » dans resume) ; sinon ""
createdAt: maintenant (ISO)
updatedAt: maintenant (ISO)
status: "repere"
auto: true
seen: false
resume: 2 phrases en français (points forts, points faibles, pièges, « via agence : frais probables », nom de l'agrégateur)
annonceTexte: texte original (3 000 caractères maximum)
checklist: {}
history: [{"t": maintenant ISO, "a": "Trouvée par Claude (scan auto)"}]
```
Maximum 20 annonces par scan, les plus pertinentes d'abord (centre, mamad, récente, bon rapport qualité-prix). S'il n'y a rien de nouveau, n'écris rien.

## 6. Export vers l'app installable (GitHub)
Le dépôt est dov1906/dov1906, branche `claude/tel-aviv-apartment-tracker-wo8lg8`.
1. Exécute : `git fetch origin claude/tel-aviv-apartment-tracker-wo8lg8 && git checkout claude/tel-aviv-apartment-tracker-wo8lg8`.
2. Relis toute la collection `apts`, ainsi que `agencies`, avec `out_dir` = `/tmp/dbexport` (sous-dossiers `apts/` et `agencies/`).
3. Exécute `python3 dira-tlv/export_listings.py /tmp/dbexport`.
4. Commit `dira-tlv/app/data/listings.json` avec le message « Scan <date> : N nouvelles annonces ».
5. Pousse sur cette branche. Ne pousse sur aucune autre branche et n'ouvre pas de pull request.

Si la branche n'existe pas ou si le push est refusé, saute cette étape et signale-le dans le compte rendu.

## 7. Compte rendu (en français, court)
- Le nombre d'annonces ajoutées, et combien ont des photos.
- Le top 3 : rue, prix, quartier, pourquoi, lien.
- Les sources qui n'ont pas répondu.
- Le résultat de l'export GitHub.
