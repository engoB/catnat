# CATNAT — banc d'essai automatisé

Un site qui se construit, se met à jour et se publie tout seul, tous les jours, gratuitement.
Vous n'avez rien à surveiller : **tous les lundis, un compte rendu s'ouvre en ticket dans l'onglet
Issues.** Vous le copiez-collez dans la conversation, et vous obtenez la décision d'étape suivante.

**Coût : 0 €.** Dépôt public GitHub + GitHub Pages + GitHub Actions + formulaire Tally, tout en
offre gratuite. Aucune carte bancaire nulle part.

---

## Ce que vous faites une fois — environ 25 minutes

### 1. Créer le dépôt

Sur GitHub, **New repository**.

- **Nom** : `VOTRE-PSEUDO.github.io` si ce dépôt n'existe pas déjà chez vous — c'est le meilleur
  choix, le site sera à la racine du domaine et les adresses seront plus courtes.
  Sinon, nommez-le `catnat`.
- **Public** — obligatoire : les minutes GitHub Actions et GitHub Pages ne sont gratuites que
  sur un dépôt public.
- Ne cochez **rien** d'autre (pas de README, pas de .gitignore).

### 2. Déposer les fichiers

Sur la page du dépôt vide : **uploading an existing file**, puis glissez-déposez **tout le contenu
de ce dossier** (y compris le dossier caché `.github`). Si le glisser-déposer ignore `.github`,
créez les fichiers à la main avec **Add file > Create new file** en tapant le chemin complet
`.github/workflows/quotidien.yml`, puis collez le contenu.

### 3. Deux réglages, et c'est tout

| Où | Réglage |
|---|---|
| **Settings > Pages** | *Build and deployment* → **Source : GitHub Actions** |
| **Settings > Actions > General** | tout en bas, *Workflow permissions* → **Read and write permissions**, puis **Save** |

Sans le second réglage, le robot ne pourra pas enregistrer les données ni ouvrir les comptes rendus.

### 4. Le formulaire d'inscription (gratuit, illimité)

Sur [tally.so](https://tally.so), créez un formulaire à **deux champs** : *E-mail* et *Commune*.
Publiez-le, copiez le lien (`https://tally.so/r/XXXXXX`).

### 5. Google Search Console

[search.google.com/search-console](https://search.google.com/search-console) → **Ajouter une
propriété** → *Préfixe d'URL* → l'adresse de votre site. Choisissez la méthode **balise HTML** et
copiez la valeur `content="..."` — c'est elle, pas la balise entière.

### 6. Remplir `config.json`

C'est le seul fichier que vous modifiez. Cliquez dessus dans GitHub, puis sur le crayon :

```json
{
  "departements": ["47"],
  "limite_communes": 30,
  "base_url": "https://VOTRE-PSEUDO.github.io",
  "formulaire_url": "https://tally.so/r/XXXXXX",
  "verification_google": "la-valeur-copiee-a-l-etape-5"
}
```

Si votre dépôt s'appelle `catnat` et non `VOTRE-PSEUDO.github.io`, alors
`"base_url": "https://VOTRE-PSEUDO.github.io/catnat"`.

**Commit changes.** Le site se construit dans la foulée : onglet **Actions** pour regarder,
2 à 3 minutes.

### 7. Terminer la vérification et soumettre le plan du site

Une fois le site en ligne, retournez dans Search Console, cliquez **Vérifier**, puis
**Sitemaps** → soumettez `sitemap.xml`.

---

## Ensuite : plus rien.

| Quand | Ce qui se passe | Ce que vous faites |
|---|---|---|
| Tous les jours, 5 h 20 UTC | Les données sont récupérées, les nouveaux arrêtés détectés, le site régénéré et republié. | Rien. |
| Tous les lundis, 6 h 00 UTC | `RAPPORT.md` est écrit et **un ticket s'ouvre dans l'onglet Issues** — vous recevez la notification par e-mail. | Ouvrir le ticket, compléter les 4 chiffres demandés (3 minutes), coller le tout dans la conversation. |

---

## Ce qu'il y a dans ce dépôt

```
config.json                        le seul fichier que vous touchez
scripts/catnat.py                  collecte, détection des nouveautés, génération des pages
scripts/rapport.py                 écrit le compte rendu hebdomadaire
data/donnees.json                  l'état de la veille — sert à détecter ce qui est nouveau
data/historique.jsonl              une ligne par jour : c'est la mémoire du test
.github/workflows/quotidien.yml    la collecte et la publication automatiques
.github/workflows/rapport.yml      le compte rendu automatique
```

## Pour vérifier la donnée avant tout le reste (facultatif, 1 minute)

Onglet **Actions > Collecte quotidienne > Run workflow**. Si le job passe au vert, la donnée
officielle répond et le site est en ligne. S'il échoue, ouvrez le journal : le message dira
laquelle des sources n'a pas répondu.

## Limites à connaître

- GitHub Pages : site publié de **1 Go maximum**, **100 Go de trafic par mois** (large), et un
  déploiement qui **échoue au-delà de 10 minutes**. Sans objet pour quelques centaines de pages ;
  à surveiller au-delà de 20 000.
- Les tâches planifiées GitHub peuvent être **retardées de quelques heures** aux heures de pointe,
  et sont **désactivées après 60 jours sans activité** sur le dépôt. Le commit quotidien du robot
  entretient cette activité tout seul.
- `robots.txt` n'est lu qu'à la racine d'un domaine. Sur un dépôt `catnat`, il ne sera pas pris en
  compte — sans conséquence ici, puisque le plan du site est soumis directement dans Search Console.

## Ce que ce dépôt n'est pas

Ce n'est **pas** un service d'alerte : personne ne reçoit encore d'e-mail. C'est un test
d'intention. On mesure si des gens cherchent, arrivent, et laissent leur adresse. L'envoi réel des
alertes n'arrive qu'après, et seulement si les seuils sont atteints.

Source des données : base GASPAR, API Géorisques (ministère de la Transition écologique).
