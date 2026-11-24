#!/usr/bin/env python3
"""Export the tracker database to app/data/listings.json (public, no private notes).

Usage: python3 export_listings.py <dir saved by ArtifactData list out_dir>
The directory must contain apts/*.json and optionally agencies/*.json, as written by
`ArtifactData` action "list" with `out_dir`.
"""
import json, sys, pathlib, datetime

PUBLIC = ["titre","rue","rueHe","quartier","prix","arnona","vaad","pieces","surface","etage","ascenseur","mamad",
          "animaux","balcon","clim","meuble","parking","dispo","contactNom","contactTel","contactEmail","contactType",
          "url","sourceUrl","source","publishedAt","createdAt","auto","resume","annonceTexte","photos","frais"]
AGENCY = ["name","tel","email","site","notes"]

def load(d):
    out = []
    for f in sorted(pathlib.Path(d).glob("*.json")):
        doc = json.loads(f.read_text(encoding="utf8"))
        data = doc.get("data", doc)
        data["id"] = doc.get("id", f.stem)
        out.append(data)
    return out

src = pathlib.Path(sys.argv[1])
apts = [dict({k: a[k] for k in PUBLIC if k in a}, id=a["id"], status="repere", seen=False)
        for a in load(src / "apts") if a.get("auto")]  # only scanned listings are public
ags = [dict({k: a[k] for k in AGENCY if k in a}, id=a["id"], status="a_contacter") for a in load(src / "agencies")] if (src / "agencies").exists() else []
out = {"updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "apts": apts, "agencies": ags}
dest = pathlib.Path(__file__).resolve().parent / "app" / "data" / "listings.json"
dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf8")
print(f"exported {len(apts)} listings, {len(ags)} agencies -> {dest}")
