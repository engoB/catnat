#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ecrit RAPPORT.md : le compte rendu a copier-coller tel quel dans la conversation.
Lit uniquement data/historique.jsonl, produit par catnat.py. Aucun reseau.
"""

import json
import os
from datetime import date, datetime

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORIQUE = os.path.join(RACINE, "data", "historique.jsonl")
CONFIG = os.path.join(RACINE, "config.json")
SORTIE = os.path.join(RACINE, "RAPPORT.md")


def lignes():
    if not os.path.exists(HISTORIQUE):
        return []
    out = []
    with open(HISTORIQUE, encoding="utf-8") as f:
        for l in f:
            l = l.strip()
            if l:
                try:
                    out.append(json.loads(l))
                except json.JSONDecodeError:
                    pass
    return out


def main():
    h = lignes()
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    aujourdhui = date.today()

    if not h:
        texte = ("# Compte rendu CATNAT\n\nAucune execution enregistree. "
                 "Le workflow quotidien n'a pas encore tourne, ou il echoue : "
                 "regardez l'onglet Actions du depot.\n")
        open(SORTIE, "w", encoding="utf-8").write(texte)
        print(texte)
        return

    # deduplication : une ligne par jour, la derniere
    par_jour = {}
    for l in h:
        par_jour[l["date"]] = l
    jours = sorted(par_jour)
    premier, dernier = par_jour[jours[0]], par_jour[jours[-1]]
    j0 = datetime.strptime(jours[0], "%Y-%m-%d").date()
    jn = (aujourdhui - j0).days

    # nouveautes de la periode : les 7 derniers jours enregistres
    recents = [par_jour[j] for j in jours[-7:]]
    nouveaux = [n for l in recents for n in l.get("nouveaux", [])]
    vus, nouveaux_uniques = set(), []
    for n in nouveaux:
        k = (n.get("ref"), n.get("insee"))
        if k not in vus:
            vus.add(k)
            nouveaux_uniques.append(n)

    en_cours = dernier.get("delais_en_cours", [])
    manquants = [j for j in
                 [(j0.toordinal() + i) for i in range((aujourdhui - j0).days + 1)]
                 if date.fromordinal(j).isoformat() not in par_jour]

    L = []
    a = L.append
    a(f"# Compte rendu CATNAT — J+{jn}")
    a("")
    a(f"- **Période couverte** : {jours[0]} → {jours[-1]}")
    a(f"- **Exécutions enregistrées** : {len(jours)} jours sur {jn + 1} attendus"
      + (f" — **{len(manquants)} jour(s) manquant(s)**" if manquants else " — aucune interruption"))
    a(f"- **Départements suivis** : {', '.join(cfg.get('departements', []))}")
    a(f"- **Site** : {cfg.get('base_url', '(non configuré)')}")
    a("")
    a("## 1. Ce que la machine a produit toute seule")
    a("")
    a("| Indicateur | Au départ | Aujourd'hui |")
    a("|---|---:|---:|")
    a(f"| Communes suivies | {premier.get('communes', 0)} | {dernier.get('communes', 0)} |")
    a(f"| Pages publiées | {premier.get('pages', 0)} | {dernier.get('pages', 0)} |")
    a(f"| Arrêtés dans la base | {premier.get('arretes_total', 0)} | {dernier.get('arretes_total', 0)} |")
    a("")
    a("## 2. Nouveaux arrêtés détectés sur les 7 derniers jours")
    a("")
    if nouveaux_uniques:
        a(f"**{len(nouveaux_uniques)} nouvel(s) arrêté(s).** C'est exactement ce qu'un abonné aurait reçu.")
        a("")
        a("| Commune | Phénomène | Publication au JO |")
        a("|---|---|---|")
        for n in nouveaux_uniques[:40]:
            a(f"| {n.get('commune')} | {n.get('risque')} | {n.get('jo')} |")
        if len(nouveaux_uniques) > 40:
            a(f"| … | … | et {len(nouveaux_uniques) - 40} autres |")
    else:
        a("**Aucun.** Période calme — c'est fréquent et ce n'est pas un mauvais signe en soi, "
          "mais cela veut dire que le test n'a pas encore rencontré son pic de trafic.")
    a("")
    a("## 3. Délais de déclaration en cours aujourd'hui")
    a("")
    if en_cours:
        a("| Commune | Jours restants | Publié au JO le |")
        a("|---|---:|---|")
        for e in en_cours[:25]:
            a(f"| {e.get('commune')} | {e.get('jours')} | {e.get('jo')} |")
        if len(en_cours) > 25:
            a(f"| … | | et {len(en_cours) - 25} autres |")
    else:
        a("Aucun délai en cours. Les pages n'affichent donc pas de bannière d'urgence en ce moment.")
    a("")
    a("## 4. À compléter par moi — 4 chiffres, 3 minutes, une seule fois par semaine")
    a("")
    a("> Ces chiffres ne peuvent pas être récupérés automatiquement sans donner des accès à "
      "des services tiers. Ouvrez les deux onglets, relevez, remplacez les points d'interrogation.")
    a("")
    a("**Google Search Console** → propriété du site → *Indexation > Pages* et *Performances* "
      "(période : 7 derniers jours)")
    a("")
    a("| Chiffre | Où | Valeur |")
    a("|---|---|---|")
    a("| Pages indexées | Indexation > Pages > « Indexées » | ? |")
    a("| Pages non indexées | Indexation > Pages > « Non indexées » | ? |")
    a("| Impressions (7 j) | Performances > Total des impressions | ? |")
    a("| Clics (7 j) | Performances > Total des clics | ? |")
    a("")
    a("**Formulaire (Tally)** → votre formulaire → onglet *Submissions*")
    a("")
    a("| Chiffre | Valeur |")
    a("|---|---|")
    a("| Inscriptions totales depuis le début | ? |")
    a("| Inscriptions des 7 derniers jours | ? |")
    a("")
    a("## 5. À dire en une phrase")
    a("")
    a("> Quelque chose s'est-il passé cette semaine que les chiffres ne montrent pas ? "
      "(un partage dans un groupe, un lien reçu, un e-mail d'un habitant, un article local)")
    a("")
    a("`Réponse : `")
    a("")
    a("---")
    a("")
    a("*Rapport généré automatiquement. Copiez-collez ce fichier entier dans la conversation "
      "pour obtenir la décision d'étape suivante.*")

    texte = "\n".join(L) + "\n"
    open(SORTIE, "w", encoding="utf-8").write(texte)
    print(texte)


if __name__ == "__main__":
    main()
