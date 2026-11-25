"""Daily job feed for Dov's "Radar emploi Israël".

Runs in GitHub Actions (full internet access) and writes:
  goozali/jobs.json  - filtered Goozali (Airtable) offers
  feeds/ats.json     - Israel offers from public ATS APIs + defense sites
  feeds/status.json  - per-source counts and errors

The evening radar scan reads these files through raw.githubusercontent.com.
"""
import json
import re
import sys
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
NOW = datetime.now(timezone.utc)
STATUS = {}
ROOT = Path(__file__).resolve().parent.parent

ISRAEL = re.compile(r"israel|tel[ -]?aviv|herzliya|ramat[ -]?gan|haifa|yokneam|jerusalem|"
                    r"petah|petach|ra'?anana|netanya|rehovot|hod hasharon|kfar saba|"
                    r"beer[ -]?sheva|caesarea|bnei brak|givatayim|holon|rishon|airport city|"
                    r"modiin|or yehuda|\bil\b", re.I)


def note(name, count=None, error=None):
    STATUS[name] = {"count": count, "error": error}
    print(f"[{name}] count={count} error={error}", flush=True)


# ---------------------------------------------------------------- Goozali
GZ_APP = "appwewqLk7iUY4azc"
GZ_SHARE = "shrQBuWjXd0YgPqV6"
GZ_FIELDS = {"Software Engineering", "Data Science, ML & Algorithms", "Data Engineering",
             "Data Analytics & BI", "Product Management", "Solutions & Sales Engineering",
             "Frontend Development"}
GZ_DAYS = 10


def goozali():
    page = S.get(f"https://airtable.com/embed/{GZ_APP}/{GZ_SHARE}", timeout=60)
    page.raise_for_status()
    html = page.text
    m = re.search(r'urlWithParams["\']?\s*:\s*"([^"]+readSharedViewData[^"]+)"', html)
    if not m:
        m = re.search(r'"(\\?/v0\.3\\?/view\\?/[^"]+readSharedViewData[^"]+)"', html)
    if not m:
        dbg = [f"status={page.status_code} len={len(html)}"]
        for kw in ("readSharedViewData", "urlWithParams", "accessPolicy", "initData", "viw", "requestId"):
            for mm in list(re.finditer(kw, html))[:3]:
                dbg.append(f"--- {kw} @{mm.start()}: " + html[max(0, mm.start() - 150):mm.start() + 400])
        (ROOT / "feeds").mkdir(exist_ok=True)
        (ROOT / "feeds" / "goozali_debug.txt").write_text("\n".join(dbg))
        print("\n".join(dbg)[:6000], flush=True)
        raise RuntimeError("readSharedViewData URL not found in embed page")
    path = m.group(1).encode().decode("unicode_escape").replace("\\/", "/")
    url = urllib.parse.urljoin("https://airtable.com", path)
    u = urllib.parse.urlparse(url)
    q = dict(urllib.parse.parse_qsl(u.query))
    params = json.loads(q.get("stringifiedObjectParams", "{}") or "{}")
    params["shouldUseNestedResponseFormat"] = True
    params["allowMsgpackOfResult"] = False
    q["stringifiedObjectParams"] = json.dumps(params)
    url = urllib.parse.urlunparse(u._replace(query=urllib.parse.urlencode(q)))
    pl = re.search(r'pageLoadId["\']?\s*:\s*"([^"]+)"', html)
    headers = {
        "x-airtable-application-id": GZ_APP,
        "x-requested-with": "XMLHttpRequest",
        "x-time-zone": "Asia/Jerusalem",
        "x-user-locale": "en",
        "Accept": "application/json",
        "Referer": f"https://airtable.com/embed/{GZ_APP}/{GZ_SHARE}",
    }
    if pl:
        headers["x-airtable-page-load-id"] = pl.group(1)
    r = S.get(url, headers=headers, timeout=180)
    r.raise_for_status()
    ctype = r.headers.get("content-type", "")
    if "msgpack" in ctype:
        import msgpack
        data = msgpack.unpackb(r.content, raw=False, strict_map_key=False)
    else:
        data = r.json()
    table = data["data"]["table"]
    cols = {c["name"]: c for c in table["columns"]}

    def raw(row, name):
        c = cols.get(name)
        return row.get("cellValuesByColumnId", {}).get(c["id"]) if c else None

    def choice(name, v):
        if v is None:
            return ""
        opts = (cols.get(name, {}).get("typeOptions") or {}).get("choices") or {}
        if isinstance(v, list):
            return "/".join((opts.get(x) or {}).get("name", str(x)) for x in v)
        return (opts.get(v) or {}).get("name", str(v))

    out = []
    cutoff = NOW - timedelta(days=GZ_DAYS)
    for row in table["rows"]:
        posted = raw(row, "Posted")
        try:
            pdt = datetime.fromisoformat(str(posted).replace("Z", "+00:00"))
        except Exception:
            continue
        if pdt.tzinfo is None:
            pdt = pdt.replace(tzinfo=timezone.utc)
        if pdt < cutoff:
            continue
        field = choice("Field", raw(row, "Field"))
        if not any(f in field for f in GZ_FIELDS):
            continue
        scope = choice("Scope", raw(row, "Scope"))
        if scope and scope != "Full Time":
            continue
        lang = choice("Language requirement", raw(row, "Language requirement"))
        if lang == "Hebrew":
            continue
        exp = raw(row, "Min Experience (Y)")
        if isinstance(exp, (int, float)) and exp > 5:
            continue
        out.append({
            "id": str(raw(row, "Job ID") or row.get("id")),
            "title": raw(row, "Job Title"),
            "company": raw(row, "Company") if not isinstance(raw(row, "Company"), list)
            else ", ".join(map(str, raw(row, "Company"))),
            "location": choice("Location", raw(row, "Location")),
            "exp": exp,
            "posted": str(posted)[:10],
            "url": raw(row, "Position Link"),
            "field": field,
            "language": lang,
        })
    note("goozali", len(out))
    return out


# ---------------------------------------------------------------- ATS APIs
GREENHOUSE = ["fireblocks", "orcasecurity", "axonius", "bigid", "appsflyer", "riskified", "jfrog",
              "island", "catonetworks", "forter", "payoneer", "yotpo", "similarweb", "taboola",
              "transmitsecurity", "gongio", "sentinellabs", "saltsecurity", "apiiro", "augury",
              "duda", "optimove", "jamf", "elastic", "gitlab", "okta", "zscaler", "datadog",
              "mongodb", "tripactions", "eonio", "nanit", "scaleops", "nift", "connecteam",
              "monticelloam", "beyondtrust", "via", "phasev", "wiz", "cyberark", "armis",
              "snyk", "lightricks", "melio", "hibob", "papayaglobal", "tipalti", "pagaya"]
GREENHOUSE_EU = ["guidde", "nice", "scaleops"]
LEVER = ["walkme"]
LEVER_EU = ["mobileye"]
ASHBY = ["lemonade", "moonactive", "honeybook", "finout", "monday.com", "Irregular", "ElevenLabs"]
SMARTR = ["Wix2", "CheckPointSoftwareTechnologies2", "kalturainc", "nexarinc"]


def j(url, **kw):
    r = S.get(url, timeout=60, **kw)
    r.raise_for_status()
    return r.json()


def ats():
    jobs = []

    def add(src, company, title, location, url, posted="", jid=""):
        if not title or not ISRAEL.search(location or ""):
            return
        jobs.append({"source": src, "company": company, "title": title.strip(),
                     "location": location, "url": url, "posted": (posted or "")[:10],
                     "id": str(jid)})

    for host, boards in (("boards-api.greenhouse.io", GREENHOUSE),
                         ("boards-api.eu.greenhouse.io", GREENHOUSE_EU)):
        for b in boards:
            try:
                d = j(f"https://{host}/v1/boards/{b}/jobs")
                n0 = len(jobs)
                for x in d.get("jobs", []):
                    add("Greenhouse", b, x.get("title"), (x.get("location") or {}).get("name", ""),
                        x.get("absolute_url"), x.get("updated_at", ""), f"gh-{x.get('id')}")
                note(f"greenhouse:{b}", len(jobs) - n0)
            except Exception as e:
                note(f"greenhouse:{b}", error=str(e)[:120])
    for host, cos in (("api.lever.co", LEVER), ("api.eu.lever.co", LEVER_EU)):
        for c in cos:
            try:
                n0 = len(jobs)
                for x in j(f"https://{host}/v0/postings/{c}?mode=json"):
                    loc = (x.get("categories") or {}).get("location", "")
                    ts = x.get("createdAt")
                    posted = datetime.fromtimestamp(ts / 1000, timezone.utc).isoformat() if ts else ""
                    add("Lever", c, x.get("text"), loc, x.get("hostedUrl"), posted, f"lv-{c}-{x.get('id')}")
                note(f"lever:{c}", len(jobs) - n0)
            except Exception as e:
                note(f"lever:{c}", error=str(e)[:120])
    for c in ASHBY:
        try:
            n0 = len(jobs)
            for x in j(f"https://api.ashbyhq.com/posting-api/job-board/{c}").get("jobs", []):
                locs = " / ".join([x.get("location") or ""] +
                                  [s.get("location", "") for s in x.get("secondaryLocations") or []])
                add("Ashby", c, x.get("title"), locs, x.get("jobUrl"), x.get("publishedAt", ""),
                    f"ab-{c}-{x.get('id')}")
            note(f"ashby:{c}", len(jobs) - n0)
        except Exception as e:
            note(f"ashby:{c}", error=str(e)[:120])
    for c in SMARTR:
        try:
            n0, off = len(jobs), 0
            while True:
                d = j(f"https://api.smartrecruiters.com/v1/companies/{c}/postings?limit=100&offset={off}&country=il")
                for x in d.get("content", []):
                    loc = (x.get("location") or {})
                    add("SmartRecruiters", c, x.get("name"),
                        f"{loc.get('city', '')}, {loc.get('country', '')} israel",
                        f"https://jobs.smartrecruiters.com/{c}/{x.get('id')}", x.get("releasedDate", ""),
                        f"sr-{c}-{x.get('id')}")
                off += 100
                if off >= d.get("totalFound", 0):
                    break
            note(f"smartrecruiters:{c}", len(jobs) - n0)
        except Exception as e:
            note(f"smartrecruiters:{c}", error=str(e)[:120])
    # Eightfold pcsx
    for name, host, domain in (("NVIDIA", "jobs.nvidia.com", "nvidia.com"),
                               ("Microsoft", "apply.careers.microsoft.com", "microsoft.com"),
                               ("Qualcomm", "careers.qualcomm.com", "qualcomm.com"),
                               ("PayPal", "paypal.eightfold.ai", "paypal.com")):
        try:
            n0, start = len(jobs), 0
            while start < 600:
                d = j(f"https://{host}/api/pcsx/search?domain={domain}&location=Israel&start={start}")
                pos = (d.get("data") or {}).get("positions") or []
                if not pos:
                    break
                for x in pos:
                    locs = " / ".join(x.get("locations") or []) or "Israel"
                    ts = x.get("postedTs")
                    posted = datetime.fromtimestamp(ts, timezone.utc).isoformat() if ts else ""
                    purl = x.get("positionUrl") or ""
                    if purl.startswith("/"):
                        purl = f"https://{host}{purl}"
                    add(name, name, x.get("name"), locs, purl, posted, f"{name.lower()}-{x.get('id')}")
                start += len(pos)
                time.sleep(0.5)
            note(f"pcsx:{name}", len(jobs) - n0)
        except Exception as e:
            note(f"pcsx:{name}", error=str(e)[:120])
    try:
        n0 = len(jobs)
        d = j("https://career.mlp.com/api/apply/v2/jobs?domain=mlp.com&location=Tel%20Aviv%2C%20Israel&start=0&num=50")
        for x in d.get("positions", []):
            add("Millennium", "Millennium", x.get("name"), x.get("location") or "Tel Aviv, Israel",
                x.get("canonicalPositionUrl"), "", f"mlp-{x.get('id')}")
        note("millennium", len(jobs) - n0)
    except Exception as e:
        note("millennium", error=str(e)[:120])
    try:
        n0, off = len(jobs), 0
        while off < 500:
            d = j(f"https://www.amazon.jobs/en/search.json?base_query=&loc_query=Israel&country=ISR"
                  f"&result_limit=100&offset={off}&sort=recent")
            js = d.get("jobs", [])
            if not js:
                break
            for x in js:
                add("Amazon", x.get("company_name") or "Amazon", x.get("title"),
                    f"{x.get('city', '')}, Israel", "https://www.amazon.jobs" + (x.get("job_path") or ""),
                    x.get("posted_date", ""), f"amazon-{x.get('id_icims')}")
            off += 100
        note("amazon", len(jobs) - n0)
    except Exception as e:
        note("amazon", error=str(e)[:120])
    # Defense
    try:
        n0 = len(jobs)
        for x in j("https://elbitsystemscareer.com/cron/jobs.json"):
            add("Elbit", "Elbit Systems", x.get("jobTitle"), f"{x.get('area', '')} Israel",
                f"https://elbitsystemscareer.com/job/?jid={x.get('jobId')}", x.get("openDate", ""),
                f"el-{x.get('jobId')}")
        note("elbit", len(jobs) - n0)
    except Exception as e:
        note("elbit", error=str(e)[:120])
    try:
        n0 = len(jobs)
        for x in j("https://jobs.iai.co.il/wp-content/themes/tyco-wp/assets/json/jobs.json"):
            jobs.append({"source": "IAI", "company": "IAI", "title": x.get("tl"),
                         "location": f"{x.get('ct', '')} Israel", "category": x.get("jc"),
                         "url": f"https://jobs.iai.co.il/job/{x.get('id')}", "posted": "",
                         "id": f"iai-{x.get('id')}"})
        note("iai", len(jobs) - n0)
    except Exception as e:
        note("iai", error=str(e)[:120])
    return jobs


def main():
    (ROOT / "goozali").mkdir(exist_ok=True)
    (ROOT / "feeds").mkdir(exist_ok=True)
    try:
        gz = goozali()
        (ROOT / "goozali" / "jobs.json").write_text(json.dumps(
            {"generated": NOW.isoformat(), "count": len(gz), "jobs": gz}, ensure_ascii=False, indent=1))
    except Exception as e:
        note("goozali", error=f"{type(e).__name__}: {str(e)[:200]}")
    a = ats()
    (ROOT / "feeds" / "ats.json").write_text(json.dumps(
        {"generated": NOW.isoformat(), "count": len(a), "jobs": a}, ensure_ascii=False, indent=1))
    (ROOT / "feeds" / "status.json").write_text(json.dumps(
        {"generated": NOW.isoformat(), "sources": STATUS}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
