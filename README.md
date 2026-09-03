# CATNAT — banc d'essai automatisé

Un site qui se construit, se met à jour et se publie tout seul, tous les jours, gratuitement.
Vous n'avez rien à surveiller : **tous les lundis, un compte rendu s'ouvre en ticket dans l'onglet
Issues.** Vous le copiez-collez dans la conversation, et vous obtenez la décision d'étape suivante.

**Coût : 0 €.** Dépôt public GitHub + GitHub Pages + GitHub Actions + formulaire Tally, tout en
offre gratuite. Aucune carte bancaire nulle part.

---

## Ce que vous faites une fois — environ 25 minutes

### 1. Créer le dépôt, en public

Sur GitHub, **New repository**.

- **Nom** : `VOTRE-PSEUDO.github.io` si ce dépôt n'existe pas déjà chez vous — c'est le meilleur
  choix, le site sera à la racine du domaine. Sinon, nommez-le `catnat`.
- **Public** — obligatoire : Actions et Pages ne sont gratuits que sur un dépôt public.
- Ne cochez **rien** d'autre.

**À la fin de cette étape, vous connaissez l'adresse de votre futur site :**

| Nom du dépôt | Adresse du site |
|---|---|
| `VOTRE-PSEUDO.github.io` | `https://VOTRE-PSEUDO.github.io` |
| `catnat` | `https://VOTRE-PSEUDO.github.io/catnat` |

Notez-la. Elle sert aux étapes 3, 4 et 5.

### 2. Déposer les fichiers et régler deux cases

Sur la page du dépôt vide : **uploading an existing file**, puis glissez tout le contenu du dossier.

> Le dossier `.github` est caché sur Mac et sous Windows. S'il ne part pas avec le reste, créez ses
> deux fichiers à la main via **Add file > Create new file** en tapant le chemin complet
> `.github/workflows/quotidien.yml`, puis en collant le contenu.

Puis les deux réglages, sans lesquels rien ne fonctionne :

| Où | Réglage |
|---|---|
| **Settings > Pages** | *Build and deployment* → **Source : GitHub Actions** |
| **Settings > Actions > General** | tout en bas, *Workflow permissions* → **Read and write permissions** → **Save** |

### 3. Mettre le site en ligne — une seule ligne de `config.json`

Cliquez sur `config.json`, puis sur le crayon, et remplissez **uniquement** `base_url` avec
l'adresse notée à l'étape 1. Laissez les deux autres champs vides pour l'instant.

```json
{
  "departements": ["47"],
  "limite_communes": 30,
  "base_url": "https://VOTRE-PSEUDO.github.io",
  "formulaire_url": "",
  "verification_google": ""
}
```

**Commit changes.** Onglet **Actions** : le site se construit en 2 à 3 minutes. Ouvrez son adresse
dans le navigateur pour vérifier qu'il s'affiche. **Il faut qu'il soit en ligne avant l'étape 4.**

### 4. Google Search Console — ce que c'est, et pourquoi

Search Console est l'outil gratuit de Google qui vous dit **combien de vos pages sont dans son
index, et combien de fois elles sont apparues dans les résultats**. Sans lui, vous êtes aveugle :
c'est la source des deux chiffres qui décident du test. Vous avez déjà un compte, c'est votre compte
Google.

Sur [search.google.com/search-console](https://search.google.com/search-console) :

1. **Ajouter une propriété**. Deux cases s'affichent : *Domaine* et *Préfixe d'URL*.
   → **Préfixe d'URL**, celle de droite. (L'autre demande de modifier des DNS, que vous n'avez pas.)
2. Collez l'adresse exacte de votre site, avec le `https://`, telle qu'elle s'affiche dans votre
   navigateur. → **Continuer**.
3. Une liste de méthodes de validation apparaît. Choisissez **Balise HTML**.
4. Google affiche une ligne de ce genre :
   `<meta name="google-site-verification" content="AbC123dEf456..." />`
   **Copiez uniquement ce qu'il y a entre les guillemets après `content=`** — pas la balise entière,
   pas les guillemets. Juste `AbC123dEf456...`
5. **Laissez cet onglet ouvert.** Vous y reviendrez à l'étape 6.

### 5. Coller le code dans `config.json`

Retour sur GitHub, `config.json`, crayon. Collez la valeur copiée :

```json
  "verification_google": "AbC123dEf456..."
```

**Commit changes**, puis attendez 2 à 3 minutes que l'onglet **Actions** repasse au vert. Le code est
maintenant présent dans toutes les pages du site — c'est le générateur qui l'y met tout seul.

### 6. Cliquer sur « Valider »

Revenez sur l'onglet Search Console laissé ouvert et cliquez sur **Valider**. Google va chercher la
balise sur votre page d'accueil et confirme.

> **« Échec de la validation » ?** Neuf fois sur dix, la nouvelle version du site n'est pas encore
> publiée. Vérifiez que le job dans l'onglet **Actions** est terminé, attendez cinq minutes,
> recliquez sur **Valider**. Pour en avoir le cœur net : ouvrez votre site, faites *Afficher le code
> source de la page* et cherchez `google-site-verification`. S'il y est, la validation finira par
> passer.

### 7. Soumettre le plan du site, puis fermer l'onglet

Toujours dans Search Console, menu de gauche → **Sitemaps**. Dans le champ, tapez simplement :

```
sitemap.xml
```

→ **Envoyer**. C'est ainsi que vous dites à Google : « voici la liste complète de mes pages, viens
les chercher ». Le statut passera à *Réussite* en quelques heures.

Facultatif mais utile le premier jour : dans la barre de recherche en haut, collez l'adresse d'une
commune qui affiche un délai en cours, puis cliquez sur **Demander une indexation**. Faites-le pour
cinq ou dix pages, pas plus.

### 8. Le formulaire d'inscription (peut se faire plus tard)

Sur [tally.so](https://tally.so), un formulaire à deux champs : *E-mail* et *Commune*. Publiez,
copiez le lien `https://tally.so/r/XXXXXX`, collez-le dans `config.json` :

```json
  "formulaire_url": "https://tally.so/r/XXXXXX"
```

**Commit changes.** Tant que ce champ est vide, les pages affichent « Formulaire en cours
d'ouverture » à la place du bouton : le site fonctionne quand même.

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
