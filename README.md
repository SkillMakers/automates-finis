# Automates finis : déterminiser et minimiser, exercices corrigés

Code de la vidéo [**Automates finis : déterminiser et minimiser, exercices corrigés**](https://youtu.be/DWeajOx1au4) de la chaîne
[IT Skills Maker](https://www.youtube.com/@ItSkillsMaker).

Le programme refait le corrigé **comme sur une copie** : table de transitions, déterminisation par la méthode des
sous-ensembles (états découverts dans l'ordre où on les écrit), complétion par un état puits, minimisation par
l'algorithme de Moore (chaque étape gardée), complémentaire, expression régulière vers automate (Thompson), et le
plus court mot qui sépare deux automates. Les tests comparent ces calculs au module `re` de Python et à une
énumération de tous les mots courts, sur des centaines d'automates et d'expressions tirés au hasard.

## Lancer

Python 3.11 ou plus, aucune dépendance.

```
python demo.py           # le cours, les quatre exercices et le piège du complémentaire
python -m unittest -v    # les 24 tests
```

Sous Windows, si la console refuse le symbole de l'ensemble vide : `set PYTHONUTF8=1` avant de lancer.

Les sorties obtenues pour la vidéo sont dans [`preuves/`](preuves/) : `demo.txt` (Python 3.15.1) et `tests.txt`
(24 tests verts sous 3.15.1 et 3.11).

## L'énoncé

Alphabet {a, b}.

1. L'automate non déterministe ci-dessous reconnaît les mots qui contiennent aba. Déterminise-le.

| État | a | b |
|---|---|---|
| → 0 | 0, 1 | 0 |
| 1 | — | 2 |
| 2 | 3 | — |
| * 3 | 3 | 3 |

2. Minimise l'automate obtenu (algorithme de Moore).
3. Écris un automate pour l'expression a(a+b)\*b, puis rends-le déterministe et complet.
4. Donne un automate qui reconnaît le complémentaire du langage de la question 3.

## Le corrigé

**1.** Six états, finaux = ceux qui contiennent 3 :

| Ensemble | a | b |
|---|---|---|
| → {0} | {0,1} | {0} |
| {0,1} | {0,1} | {0,2} |
| {0,2} | {0,1,3} | {0} |
| * {0,1,3} | {0,1,3} | {0,2,3} |
| * {0,2,3} | {0,1,3} | {0,3} |
| * {0,3} | {0,1,3} | {0,3} |

**2.** Moore : étape 0 : finaux | {0} {0,1} {0,2} · étape 1 : finaux | {0} {0,1} | {0,2} · étape 2 : finaux | {0} |
{0,1} | {0,2} · puis plus rien ne bouge. **4 états** : les trois finaux fusionnent.

**3.** À la main : 0 —a→ 1, boucle a, b sur 1, 1 —b→ 2 (final). Déterministe complet : {0}, {1}, ∅ (le puits) et
{1,2} (final). Aucun écart avec le module `re` sur les 2 047 mots de 0 à 10 lettres.

**4.** Le même automate, finaux inversés : {0}, {1} et ∅ finaux, {1,2} non final.

**Le piège** : inverser les finaux de l'automate écrit à la main (non déterministe) classe mal **382 mots sur 511**
(de 0 à 8 lettres) : b est refusé, ab est accepté. Sur l'automate déterministe sans état puits : **255** mots faux,
tous ceux qui commencent par b. Il faut un automate déterministe **et** complet avant d'inverser.

**L'explosion** : « la k-ième lettre en partant de la fin est un a » s'écrit avec k + 1 états non déterministes, et
demande 2 puissance k états déterministes ; Moore n'en retire aucun (k = 10 : 11 états → 1 024).

## Les fichiers

| Fichier | Rôle |
|---|---|
| `automates.py` | lecture d'un mot, déterminisation, complétion, Moore, complémentaire, Thompson, équivalence, table de transitions |
| `enonces.py` | les automates du cours et des exercices |
| `demo.py` | le cours et les exercices, exécutés |
| `test_automates.py` | chaque résultat de la vidéo, et les algorithmes contre des juges indépendants |

## Écrire ses propres automates

```python
from automates import automate, determiniser, minimiser, table_transitions, difference

A = automate([(0, "a", 0), (0, "b", 0), (0, "a", 1), (1, "b", 2)], {0}, {2}, alphabet=("a", "b"))
D, _ = determiniser(A)
M, etapes = minimiser(D)
print(table_transitions(M))
print(difference(A, M))   # None : même langage ; sinon le plus court mot qui les sépare
```

Une flèche est `(départ, lettre, arrivée)` ; la lettre `""` est une transition epsilon. Les expressions régulières
acceptent `+` ou `|` pour l'union, `*`, les parenthèses et `ε` pour le mot vide : `thompson("a(a+b)*b")`.
