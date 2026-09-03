#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CATNAT — collecte, detection et generation. Tourne seul dans GitHub Actions.

    python scripts/catnat.py verifier   # 6 assertions sur la donnee officielle
    python scripts/catnat.py build      # collecte + detection + generation du site

Aucune dependance externe. Python 3.9+.
Sources publiques, sans jeton :
  - Georisques v1   https://www.georisques.gouv.fr/api/v1/gaspar/catnat
  - Decoupage adm.  https://geo.api.gouv.fr/departements/{dep}/communes
"""

import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(RACINE, "config.json")
DONNEES = os.path.join(RACINE, "data", "donnees.json")
HISTORIQUE = os.path.join(RACINE, "data", "historique.jsonl")
SORTIE = os.path.join(RACINE, "site")

GEORISQUES = "https://www.georisques.gouv.fr/api/v1/gaspar/catnat"
GEOAPI = "https://geo.api.gouv.fr/departements/{dep}/communes"
UA = "catnat-veille/1.0 (+https://github.com/) test de faisabilite"
PAUSE = 0.30
DELAI = 30  # jours pour declarer, a compter de la publication au JO


# --------------------------------------------------------------------- outils

def cfg():
    with open(CONFIG, encoding="utf-8") as f:
        c = json.load(f)
    c["base_url"] = c.get("base_url", "").rstrip("/")
    c["base_path"] = urllib.parse.urlparse(c["base_url"]).path.rstrip("/")
    return c


def get(url, essais=3):
    dernier = None
    for i in range(essais):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                d = json.loads(r.read().decode("utf-8"))
            time.sleep(PAUSE)
            return d
        except Exception as e:                                     # noqa: BLE001
            dernier = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"echec {url} : {dernier}")


def liste(rep):
    if isinstance(rep, list):
        return rep
    for k in ("data", "results", "records"):
        v = rep.get(k)
        if isinstance(v, list):
            return v
    return []


def arretes(insee, max_pages=30):
    out, page, vus = [], 1, set()
    while page <= max_pages:
        url = GEORISQUES + "?" + urllib.parse.urlencode(
            {"code_insee": insee, "page": page, "page_size": 100})
        rep = get(url)
        lot = liste(rep)
        neuf = [a for a in lot if a.get("code_national_catnat") not in vus]
        for a in neuf:
            vus.add(a.get("code_national_catnat"))
        out.extend(neuf)
        if not lot or not (isinstance(rep, dict) and rep.get("next")) or not neuf:
            break
        page += 1
    return out


def d(txt):
    if not txt:
        return None
    for f in ("%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(str(txt)[:19], f).date()
        except ValueError:
            continue
    return None


def restants(djo):
    return None if not djo else (djo + timedelta(days=DELAI) - date.today()).days


def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", t.lower())).strip("-")


def cle(c):
    return slug(c["nom"]) + "-" + c["code"]


# ----------------------------------------------------------------- 1. VERIFIER

def verifier():
    print("Six assertions sur la donnee officielle.\n")
    ok, corpus = {}, {}
    for insee, nom in [("34172", "Montpellier"), ("33063", "Bordeaux"), ("47001", "Agen (47001)")]:
        try:
            corpus[insee] = arretes(insee)
            print(f"  [ok]  {nom:22s} {len(corpus[insee]):3d} arretes")
        except Exception as e:                                     # noqa: BLE001
            print(f"  [KO]  {nom:22s} {e}")
    ok["A1 api sans jeton"] = bool(corpus)

    sigs = {i: frozenset(a.get("code_national_catnat") for a in v) for i, v in corpus.items()}
    ok["A2 filtre code_insee"] = len(sigs) > 1 and len(set(sigs.values())) == len(sigs)

    ex = next((a for v in corpus.values() for a in v), None)
    if ex:
        print("\n  Champs reellement renvoyes :")
        for k, v in ex.items():
            print(f"    {k:30s} = {v!r}")
    ok["A3 date_publication_jo"] = bool(ex and d(ex.get("date_publication_jo")))

    recent = max((d(a.get("date_publication_jo")) for v in corpus.values()
                  for a in v if d(a.get("date_publication_jo"))), default=None)
    if recent:
        print(f"\n  Arrete le plus recent des temoins : {recent:%d/%m/%Y} "
              f"({(date.today() - recent).days} jours)")
    ok["A4 fraicheur"] = bool(recent and (date.today() - recent).days < 500)

    ok["A5 pas de doublons"] = all(
        len({a.get("code_national_catnat") for a in v}) == len(v) for v in corpus.values())

    vol = {i: len(v) for i, v in corpus.items()}
    ok["A6 volume plausible"] = all(0 <= n <= 150 for n in vol.values())
    print(f"\n  Volumes : {vol}")
    if not ok["A6 volume plausible"]:
        print("  [!] Volume anormal : le filtre code_insee ne s'applique probablement pas.")

    print("\n  RESULTAT")
    for k in sorted(ok):
        print(f"    {'PASS ' if ok[k] else 'ECHEC'}  {k}")
    bon = all(ok.values())
    print("\n  => " + ("Donnee validee." if bon else "Au moins une assertion echoue. On ne genere pas."))
    return 0 if bon else 1


# --------------------------------------------------------------- 2. COLLECTE

def collecte(c):
    """Retourne (communes, arretes_par_commune) et signale les nouveautes."""
    communes, par_commune = {}, {}
    for dep in c["departements"]:
        lot = get(GEOAPI.format(dep=dep) + "?fields=nom,code,population&format=json")
        lot.sort(key=lambda x: -(x.get("population") or 0))
        if c.get("limite_communes"):
            lot = lot[: c["limite_communes"]]
        for com in lot:
            com["departement"] = dep
            communes[com["code"]] = com
    total = len(communes)
    for i, (insee, com) in enumerate(sorted(communes.items()), 1):
        try:
            par_commune[insee] = arretes(insee)
        except Exception as e:                                     # noqa: BLE001
            print(f"  [!] {com['nom']} : {e}", file=sys.stderr)
            par_commune[insee] = []
        if i % 25 == 0 or i == total:
            print(f"  collecte {i}/{total}", flush=True)
    return communes, par_commune


def charger_precedent():
    try:
        with open(DONNEES, encoding="utf-8") as f:
            return json.load(f)
    except Exception:                                              # noqa: BLE001
        return {"communes": {}, "arretes": {}}


# --------------------------------------------------------------- 3. PAGES

GABARIT = """<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titre}</title>
<meta name="description" content="{meta}">
<link rel="canonical" href="{url}">{verif}
<script type="application/ld+json">{jsonld}</script>
<style>{css}</style></head><body>
<header><div class="w"><p class="fil"><a href="{base}/">Accueil</a> · <a href="{base}/departement/{dep}/">Département {dep}</a></p>
<h1>{h1}</h1><p class="lede">{lede}</p></div></header>
<div class="w">{banniere}
<h2>Les arrêtés qui concernent {nom}</h2>
{tableau}
<div class="cta"><b>Être prévenu du prochain arrêté sur {nom}</b>
<p>Le délai pour déclarer à votre assureur est de <b>30 jours à compter de la publication au
<i>Journal officiel</i></b>. Nous envoyons un e-mail le jour même, avec la date limite calculée.
Gratuit pendant la phase de test.</p>{bouton}</div>
<h2>Que faire si vous êtes concerné</h2>
<p>Déclarez le sinistre à votre assureur <b>dans les 30 jours suivant la publication de l'arrêté au
<i>Journal officiel</i></b>, par écrit, en décrivant les dommages et en joignant photos et devis.
Passé ce délai, l'assureur peut refuser la prise en charge. La garantie catastrophe naturelle est
attachée à votre contrat multirisque habitation : vous n'avez pas d'option à souscrire.</p>
<p class="mini">Ce site est un service d'information indépendant. Il ne conseille pas en assurance,
ne garantit aucune indemnisation et ne remplace pas les publications officielles. En cas de litige
avec votre assureur, la Médiation de l'assurance peut être saisie.</p>
<footer>Source : base GASPAR, API Géorisques (ministère de la Transition écologique).
Relevé du {maj}. Site indépendant, sans lien avec l'administration ni avec un assureur.</footer>
</div></body></html>"""

CSS = """
:root{--bg:#eef1f4;--sf:#fff;--ink:#101519;--ink2:#4e5a64;--rule:#d6dde3;--deep:#12566e;
--sig:#a8390f;--sigbg:#faeae3}
@media(prefers-color-scheme:dark){:root{--bg:#0c1116;--sf:#131a21;--ink:#e4ebf0;--ink2:#9fadb8;
--rule:#232f38;--deep:#4fa8c7;--sig:#e08356;--sigbg:#26140c}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.62 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
.w{max-width:740px;margin:0 auto;padding:0 20px 60px}
header{background:var(--sf);border-bottom:1px solid var(--rule);padding:22px 0 20px;margin-bottom:24px}
.fil{margin:0 0 10px;font-size:13px;color:var(--ink2)}
h1{font-size:26px;line-height:1.2;margin:0 0 7px;letter-spacing:-.02em}
h2{font-size:19px;margin:32px 0 10px}
.lede{color:var(--ink2);margin:0;font-size:16.5px}
.urg{background:var(--sigbg);border:1px solid var(--sig);border-left:4px solid var(--sig);
border-radius:5px;padding:15px 17px;margin:0 0 22px}
.urg b.t{color:var(--sig);display:block;font-size:13px;letter-spacing:.06em;text-transform:uppercase;margin-bottom:5px}
.urg p{margin:0}
table{width:100%;border-collapse:collapse;background:var(--sf);border:1px solid var(--rule);
border-radius:5px;font-size:14.5px;overflow:hidden}
th{text-align:left;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink2);
padding:10px 12px;border-bottom:1px solid var(--rule)}
td{padding:9px 12px;border-bottom:1px solid var(--rule)}
tr:last-child td{border-bottom:none}
.cta{background:var(--sf);border:1px solid var(--rule);border-left:4px solid var(--deep);
border-radius:5px;padding:16px 18px;margin:26px 0}
.cta b{display:block;margin-bottom:6px;font-size:17px}
.cta p{margin:0 0 12px;font-size:14.5px;color:var(--ink2)}
.btn{display:inline-block;background:var(--deep);color:#fff;text-decoration:none;padding:10px 18px;
border-radius:4px;font-weight:600;font-size:15px}
.mini{font-size:13px;color:var(--ink2);margin-top:18px}
footer{margin-top:32px;padding-top:16px;border-top:1px solid var(--rule);color:var(--ink2);font-size:12.5px}
a{color:var(--deep)}
.liste td a{font-weight:600}
"""


def page_commune(com, arr, c):
    nom, insee, dep = com["nom"], com["code"], com["departement"]
    arr = sorted(arr, key=lambda a: d(a.get("date_publication_jo")) or date(1900, 1, 1), reverse=True)
    url = f"{c['base_url']}/{cle(com)}/"

    lignes = "".join(
        "<tr><td>{r}</td><td>{p}</td><td>{j}</td></tr>".format(
            r=html.escape(str(a.get("libelle_risque_jo") or "—")),
            p=(f"{d(a.get('date_debut_evt')):%d/%m/%Y} → {d(a.get('date_fin_evt')):%d/%m/%Y}"
               if d(a.get("date_debut_evt")) and d(a.get("date_fin_evt"))
               else (f"{d(a.get('date_debut_evt')):%d/%m/%Y}" if d(a.get("date_debut_evt")) else "—")),
            j=(f"{d(a.get('date_publication_jo')):%d/%m/%Y}" if d(a.get("date_publication_jo")) else "—"))
        for a in arr)
    tableau = ("<table><thead><tr><th>Phénomène</th><th>Période de l'événement</th>"
               "<th>Publication au JO</th></tr></thead><tbody>" + lignes + "</tbody></table>"
               ) if arr else (f"<p>Aucun arrêté de reconnaissance de l'état de catastrophe naturelle "
                              f"n'est recensé pour {html.escape(nom)} dans la base GASPAR.</p>")

    banniere = ""
    if arr:
        jr = restants(d(arr[0].get("date_publication_jo")))
        if jr is not None and 0 <= jr <= DELAI:
            lim = d(arr[0]["date_publication_jo"]) + timedelta(days=DELAI)
            banniere = ("<div class='urg'><b class='t'>Délai en cours — {j} jour{s} restant{s}</b>"
                        "<p>Un arrêté concernant {n} a été publié au <i>Journal officiel</i> le {p}. "
                        "Vous avez jusqu'au <b>{l:%d/%m/%Y}</b> pour déclarer vos dommages à votre "
                        "assureur.</p></div>").format(
                j=jr, s="s" if jr > 1 else "", n=html.escape(nom),
                p=f"{d(arr[0]['date_publication_jo']):%d/%m/%Y}", l=lim)

    dernier = d(arr[0].get("date_publication_jo")) if arr else None
    titre = f"Catastrophes naturelles à {nom} ({dep}) : arrêtés et délais de déclaration"
    meta = (f"{len(arr)} arrêté(s) de catastrophe naturelle recensé(s) pour {nom}"
            + (f", le dernier publié au Journal officiel le {dernier:%d/%m/%Y}. " if dernier else ". ")
            + "Délai de déclaration à l'assurance : 30 jours après publication.")
    verif = (f'\n<meta name="google-site-verification" content="{html.escape(c["verification_google"])}">'
             if c.get("verification_google") else "")
    bouton = (f'<a class="btn" href="{html.escape(c["formulaire_url"])}" rel="nofollow">'
              f'Me prévenir pour {html.escape(nom)}</a>'
              if c.get("formulaire_url", "").startswith("http")
              else '<p class="mini">Formulaire en cours d\'ouverture.</p>')
    jsonld = json.dumps({"@context": "https://schema.org", "@type": "Dataset",
                         "name": f"Arrêtés de catastrophe naturelle — {nom}",
                         "description": meta, "url": url,
                         "spatialCoverage": {"@type": "Place", "name": nom, "identifier": insee},
                         "isBasedOn": "https://www.georisques.gouv.fr/donnees/bases-de-donnees",
                         "dateModified": date.today().isoformat()}, ensure_ascii=False)

    return GABARIT.format(
        titre=html.escape(titre), meta=html.escape(meta), url=url, verif=verif, jsonld=jsonld,
        css=CSS, base=c["base_path"] or "", dep=dep, h1=html.escape(titre.split(" :")[0]),
        lede=html.escape(f"{len(arr)} arrêté(s) de reconnaissance depuis 1982"
                         + (f", le dernier publié le {dernier:%d/%m/%Y}." if dernier else ".")),
        banniere=banniere, tableau=tableau, nom=html.escape(nom), bouton=bouton,
        maj=f"{date.today():%d/%m/%Y}")


def page_liste(titre, h1, lede, lignes, c, chemin_canonique):
    corps = "".join(
        "<tr><td><a href='{b}/{k}/'>{n}</a></td><td>{a}</td><td>{j}</td><td>{u}</td></tr>".format(
            b=c["base_path"] or "", k=k, n=html.escape(n), a=nb,
            j=f"{dt:%d/%m/%Y}" if dt else "—",
            u="<b>délai en cours</b>" if chaud else "")
        for k, n, nb, dt, chaud in lignes)
    return GABARIT.format(
        titre=html.escape(titre), meta=html.escape(lede), url=c["base_url"] + chemin_canonique,
        verif=(f'\n<meta name="google-site-verification" content="{html.escape(c["verification_google"])}">'
               if c.get("verification_google") else ""),
        jsonld="{}", css=CSS, base=c["base_path"] or "", dep=c["departements"][0],
        h1=html.escape(h1), lede=html.escape(lede), banniere="",
        tableau=("<table class='liste'><thead><tr><th>Commune</th><th>Arrêtés</th>"
                 "<th>Dernier JO</th><th></th></tr></thead><tbody>" + corps + "</tbody></table>"),
        nom="ces communes", bouton="", maj=f"{date.today():%d/%m/%Y}")


# ------------------------------------------------------------------ 4. BUILD

def build():
    c = cfg()
    precedent = charger_precedent()
    anciens = {code for lot in precedent.get("arretes", {}).values() for code in lot}

    communes, par_commune = collecte(c)

    # detection des nouveautes : ce qui n'etait pas la hier
    nouveaux = []
    for insee, lot in par_commune.items():
        for a in lot:
            if a.get("code_national_catnat") not in anciens and anciens:
                nouveaux.append({"commune": communes[insee]["nom"], "insee": insee,
                                 "risque": a.get("libelle_risque_jo"),
                                 "jo": a.get("date_publication_jo"),
                                 "ref": a.get("code_national_catnat")})

    os.makedirs(SORTIE, exist_ok=True)
    urls, lignes, en_cours = [], [], []
    for insee, com in sorted(communes.items(), key=lambda kv: kv[1]["nom"]):
        arr = par_commune.get(insee, [])
        rep = os.path.join(SORTIE, cle(com))
        os.makedirs(rep, exist_ok=True)
        with open(os.path.join(rep, "index.html"), "w", encoding="utf-8") as f:
            f.write(page_commune(com, arr, c))
        urls.append(f"{c['base_url']}/{cle(com)}/")
        dernier = max((d(a.get("date_publication_jo")) for a in arr
                       if d(a.get("date_publication_jo"))), default=None)
        jr = restants(dernier)
        chaud = jr is not None and 0 <= jr <= DELAI
        if chaud:
            en_cours.append({"commune": com["nom"], "jours": jr, "jo": f"{dernier:%d/%m/%Y}"})
        lignes.append((cle(com), com["nom"], len(arr), dernier, chaud))

    lignes.sort(key=lambda r: (not r[4], -(r[3].toordinal() if r[3] else 0)))
    deps = ", ".join(c["departements"])
    with open(os.path.join(SORTIE, "index.html"), "w", encoding="utf-8") as f:
        f.write(page_liste(
            f"Arrêtés de catastrophe naturelle — département {deps}",
            f"Arrêtés de catastrophe naturelle — département {deps}",
            f"{len(lignes)} communes suivies, dont {len(en_cours)} avec un délai de déclaration en cours.",
            lignes, c, "/"))
    for dep in c["departements"]:
        sous = [l for l in lignes if communes[l[0].rsplit('-', 1)[1]]["departement"] == dep]
        rep = os.path.join(SORTIE, "departement", dep)
        os.makedirs(rep, exist_ok=True)
        with open(os.path.join(rep, "index.html"), "w", encoding="utf-8") as f:
            f.write(page_liste(f"Catastrophes naturelles dans le département {dep}",
                               f"Département {dep} — arrêtés par commune",
                               f"{len(sous)} communes suivies.", sous, c, f"/departement/{dep}/"))
        urls.append(f"{c['base_url']}/departement/{dep}/")

    with open(os.path.join(SORTIE, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset '
                'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + f"  <url><loc>{c['base_url']}/</loc><lastmod>{date.today()}</lastmod></url>\n"
                + "".join(f"  <url><loc>{u}</loc><lastmod>{date.today()}</lastmod></url>\n" for u in urls)
                + "</urlset>\n")
    with open(os.path.join(SORTIE, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {c['base_url']}/sitemap.xml\n")
    open(os.path.join(SORTIE, ".nojekyll"), "w").close()

    with open(DONNEES, "w", encoding="utf-8") as f:
        json.dump({"genere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "communes": {k: v["nom"] for k, v in communes.items()},
                   "arretes": {k: [a.get("code_national_catnat") for a in v]
                               for k, v in par_commune.items()}}, f, ensure_ascii=False, indent=1)

    ligne = {"date": date.today().isoformat(),
             "communes": len(communes),
             "pages": len(urls) + 1,
             "arretes_total": sum(len(v) for v in par_commune.values()),
             "nouveaux": nouveaux,
             "delais_en_cours": sorted(en_cours, key=lambda x: x["jours"])}
    with open(HISTORIQUE, "a", encoding="utf-8") as f:
        f.write(json.dumps(ligne, ensure_ascii=False) + "\n")

    print(f"\n  {len(urls) + 1} pages ecrites dans site/")
    print(f"  {len(nouveaux)} nouvel(s) arrete(s) detecte(s) depuis la derniere execution")
    print(f"  {len(en_cours)} commune(s) avec un delai de declaration en cours")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    sys.exit({"verifier": verifier, "build": build}[cmd]())
