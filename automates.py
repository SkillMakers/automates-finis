"""Automates finis : lecture d'un mot, determinisation (methode des sous-ensembles), completion, minimisation
(algorithme de Moore), complementaire, expression reguliere vers automate (construction de Thompson) et
equivalence de deux automates.

Tout est fait comme sur une copie : les etats d'un automate determinise sont des ensembles d'etats, decouverts
dans l'ordre ou on les ecrit dans la table (lettres dans l'ordre de l'alphabet) ; la minimisation garde chaque
etape de Moore. Le mot vide s'ecrit "" ; une epsilon-transition porte la lettre "".
"""
import re
from collections import deque
from dataclasses import dataclass
from itertools import product

EPS = ""


@dataclass(frozen=True)
class Automate:
    etats: tuple          # dans l'ordre d'affichage
    alphabet: tuple       # lettres, sans epsilon
    delta: dict           # (etat, lettre) -> frozenset d'etats ; lettre "" = epsilon
    initiaux: frozenset
    finaux: frozenset

    def suivants(self, q, lettre):
        return self.delta.get((q, lettre), frozenset())


def automate(fleches, initiaux, finaux, alphabet=None, etats=None):
    """Construit un automate a partir d'une liste de fleches (depart, lettre, arrivee).

    Les etats sont pris dans l'ordre ou ils apparaissent (ou dans `etats`), l'alphabet dans l'ordre trie.
    """
    vus, deja = [], set()
    for e in list(etats or []) + [e for p, _, q in fleches for e in (p, q)] + list(initiaux) + list(finaux):
        if e not in deja:
            deja.add(e)
            vus.append(e)
    affiches = [str(e) for e in vus]
    if len(set(affiches)) != len(affiches):
        doubles = sorted({s for s in affiches if affiches.count(s) > 1})
        raise ValueError(f"deux etats s'affichent pareil ({', '.join(doubles)}) : les renommer")
    lettres = tuple(alphabet) if alphabet else tuple(sorted({a for _, a, _ in fleches if a != EPS}))
    delta = {}
    for p, a, q in fleches:
        if a != EPS and a not in lettres:
            raise ValueError(f"la lettre {a!r} n'est pas dans l'alphabet {lettres}")
        delta[(p, a)] = delta.get((p, a), frozenset()) | {q}
    if not initiaux:
        raise ValueError("un automate a au moins un etat initial")
    return Automate(tuple(vus), lettres, delta, frozenset(initiaux), frozenset(finaux))


# --- Lecture -------------------------------------------------------------------------------------------------

def cloture(A, ensemble):
    """Epsilon-cloture : les etats atteints sans lire de lettre."""
    pile, vus = list(ensemble), set(ensemble)
    while pile:
        q = pile.pop()
        for r in A.suivants(q, EPS):
            if r not in vus:
                vus.add(r)
                pile.append(r)
    return frozenset(vus)


def lire(A, mot):
    """Les etats ou l'on peut se trouver apres avoir lu `mot` (ensemble vide = blocage)."""
    courant = cloture(A, A.initiaux)
    for lettre in mot:
        if lettre not in A.alphabet:
            return frozenset()
        courant = cloture(A, frozenset().union(*(A.suivants(q, lettre) for q in courant)))
    return courant


def accepte(A, mot):
    return bool(lire(A, mot) & A.finaux)


def mots(alphabet, n_max):
    """Tous les mots de longueur 0 a n_max, par longueur puis dans l'ordre de l'alphabet."""
    for n in range(n_max + 1):
        for t in product(alphabet, repeat=n):
            yield "".join(t)


# --- Proprietes ----------------------------------------------------------------------------------------------

def est_deterministe(A):
    return (len(A.initiaux) == 1
            and not any(a == EPS for (_, a) in A.delta)
            and all(len(v) <= 1 for v in A.delta.values()))


def est_complet(A):
    return all(A.suivants(q, a) for q in A.etats for a in A.alphabet)


def accessibles(A):
    """Les etats qu'on peut atteindre depuis un etat initial."""
    vus, file = set(cloture(A, A.initiaux)), deque(cloture(A, A.initiaux))
    while file:
        q = file.popleft()
        for a in A.alphabet + (EPS,):
            for r in A.suivants(q, a):
                if r not in vus:
                    vus.add(r)
                    file.append(r)
    return [q for q in A.etats if q in vus]


def emonder(A):
    """Retire les etats inaccessibles (ils ne changent pas le langage)."""
    garder = set(accessibles(A))
    delta = {(q, a): v & garder for (q, a), v in A.delta.items() if q in garder and v & garder}
    return Automate(tuple(q for q in A.etats if q in garder), A.alphabet, delta,
                    A.initiaux & garder, A.finaux & garder)


def nom_libre(A, base="P"):
    """Un nom d'etat qui n'existe pas encore : P, puis P', P''..."""
    pris = {str(q) for q in A.etats}
    nom = base
    while nom in pris:
        nom += "'"
    return nom


def completer(A, puits=None):
    """Ajoute un etat puits (non final, qui boucle sur toutes les lettres) pour chaque transition manquante.
    Sans nom donne, le puits s'appelle P (ou P', P''... si P existe deja)."""
    if est_complet(A):
        return A
    puits = puits or nom_libre(A)
    if puits in A.etats or str(puits) in {str(q) for q in A.etats}:
        raise ValueError(f"l'etat {puits!r} existe deja")
    delta = dict(A.delta)
    for q in A.etats + (puits,):
        for a in A.alphabet:
            if not delta.get((q, a)):
                delta[(q, a)] = frozenset({puits})
    return Automate(A.etats + (puits,), A.alphabet, delta, A.initiaux, A.finaux)


# --- Determinisation -----------------------------------------------------------------------------------------

def nom_ensemble(ens, ordre):
    """{0,1,3} ; l'ensemble vide s'ecrit avec le symbole de l'ensemble vide."""
    if not ens:
        return "∅"
    return "{" + ",".join(str(q) for q in sorted(ens, key=ordre.__getitem__)) + "}"


def determiniser(A, garder_vide=True):
    """Methode des sous-ensembles.

    On part de l'ensemble des etats initiaux (avec sa cloture), puis pour chaque ensemble decouvert et chaque
    lettre on calcule l'ensemble des etats atteints. Un ensemble est FINAL s'il contient AU MOINS UN etat final.
    Renvoie (automate deterministe, table) ; la table liste les lignes dans l'ordre de la copie :
    (ensemble, {lettre: ensemble atteint}).

    garder_vide : l'ensemble vide devient un etat puits (l'automate est alors complet). Sinon, les transitions
    vers l'ensemble vide sont simplement absentes.
    """
    depart = cloture(A, A.initiaux)
    ordre, vus, table, file = [depart], {depart}, [], deque([depart])
    while file:
        E = file.popleft()
        ligne = {}
        for a in A.alphabet:
            F = cloture(A, frozenset().union(*(A.suivants(q, a) for q in E)))
            ligne[a] = F
            if (F or garder_vide) and F not in vus:
                vus.add(F)
                ordre.append(F)
                file.append(F)
        table.append((E, ligne))
    rang = {q: i for i, q in enumerate(A.etats)}
    noms = {E: nom_ensemble(E, rang) for E in ordre}
    if len(set(noms.values())) != len(noms):
        raise ValueError("deux ensembles d'etats s'ecrivent pareil : renommer les etats (sans virgule ni accolade)")
    delta = {}
    for E, ligne in table:
        for a, F in ligne.items():
            if F or garder_vide:
                delta[(noms[E], a)] = frozenset({noms[F]})
    D = Automate(tuple(noms[E] for E in ordre), A.alphabet, delta, frozenset({noms[depart]}),
                 frozenset(noms[E] for E in ordre if E & A.finaux))
    return D, table


# --- Minimisation (Moore) ------------------------------------------------------------------------------------

def minimiser(A):
    """Algorithme de Moore, sur un automate deterministe.

    1. on garde les etats accessibles ; 2. on complete (etat puits) ; 3. premiere partition : finaux / non
    finaux ; 4. on separe deux etats d'une meme classe si une lettre les envoie dans deux classes differentes ;
    on recommence jusqu'a ce que plus rien ne bouge.
    Renvoie (automate minimal, etapes) ; chaque etape est une liste de classes (listes d'etats).
    """
    if not est_deterministe(A):
        raise ValueError("Moore s'applique a un automate deterministe : determiniser d'abord")
    A = completer(emonder(A))
    cible = {(q, a): next(iter(A.suivants(q, a))) for q in A.etats for a in A.alphabet}

    def classes_de(partition):
        return {q: i for i, c in enumerate(partition) for q in c}

    partition = [c for c in ([q for q in A.etats if q in A.finaux],
                             [q for q in A.etats if q not in A.finaux]) if c]
    etapes = [partition]
    while True:
        num = classes_de(partition)
        nouvelle = []
        for c in partition:
            groupes = {}
            for q in c:
                signature = tuple(num[cible[(q, a)]] for a in A.alphabet)
                groupes.setdefault(signature, []).append(q)
            nouvelle.extend(groupes.values())
        if len(nouvelle) == len(partition):
            break
        partition = nouvelle
        etapes.append(partition)

    num = classes_de(partition)
    init = next(iter(A.initiaux))
    # les classes sont numerotees dans l'ordre de decouverte depuis l'etat initial
    ordre, vus, file = [num[init]], {num[init]}, deque([num[init]])
    while file:
        i = file.popleft()
        rep = partition[i][0]
        for a in A.alphabet:
            j = num[cible[(rep, a)]]
            if j not in vus:
                vus.add(j)
                ordre.append(j)
                file.append(j)
    # une classe d'un seul etat garde son nom ; une classe fusionnee s'ecrit 1=3 ; en cas de doublon, C0, C1...
    nom = {i: "=".join(str(q) for q in partition[i]) for i in ordre}
    if len(set(nom.values())) != len(nom):
        nom = {i: f"C{k}" for k, i in enumerate(ordre)}
    delta = {(nom[i], a): frozenset({nom[num[cible[(partition[i][0], a)]]]}) for i in ordre for a in A.alphabet}
    M = Automate(tuple(nom[i] for i in ordre), A.alphabet, delta, frozenset({nom[num[init]]}),
                 frozenset(nom[i] for i in ordre if partition[i][0] in A.finaux))
    return M, etapes


# --- Complementaire ------------------------------------------------------------------------------------------

def complementaire(A):
    """Le bon complementaire : determiniser, completer, PUIS echanger finaux et non finaux."""
    D = A if est_deterministe(A) else determiniser(A)[0]
    D = completer(D)
    return Automate(D.etats, D.alphabet, D.delta, D.initiaux, frozenset(D.etats) - D.finaux)


def complementaire_naif(A):
    """L'erreur de copie : echanger finaux et non finaux sur l'automate tel qu'il est."""
    return Automate(A.etats, A.alphabet, A.delta, A.initiaux, frozenset(A.etats) - A.finaux)


# --- Equivalence ---------------------------------------------------------------------------------------------

def difference(A, B):
    """Le plus court mot (puis le premier dans l'ordre de l'alphabet) reconnu par l'un et pas par l'autre,
    ou None si les deux automates reconnaissent le meme langage.

    Parcours en largeur du produit des deux automates determinises : c'est exact, sans limite de longueur.
    """
    lettres = tuple(sorted(set(A.alphabet) | set(B.alphabet)))
    a0, b0 = cloture(A, A.initiaux), cloture(B, B.initiaux)
    vus, file = {(a0, b0)}, deque([(a0, b0, "")])
    while file:
        x, y, mot = file.popleft()
        if bool(x & A.finaux) != bool(y & B.finaux):
            return mot
        for lettre in lettres:
            x2 = cloture(A, frozenset().union(*(A.suivants(q, lettre) for q in x)))
            y2 = cloture(B, frozenset().union(*(B.suivants(q, lettre) for q in y)))
            if (x2, y2) not in vus:
                vus.add((x2, y2))
                file.append((x2, y2, mot + lettre))
    return None


# --- Expression reguliere -> automate (Thompson) -------------------------------------------------------------

def _analyser(expr):
    """Arbre d'une expression : lettres, union (| ou +, comme dans beaucoup de cours), concatenation, etoile,
    parentheses, et le mot vide ecrit avec la lettre grecque epsilon. Priorites : etoile, puis concatenation,
    puis union. Une suite de concatenations (ou d'unions) donne UN noeud a plusieurs enfants : un mot de
    1 500 lettres ne fait pas 1 500 niveaux d'arbre."""
    s = expr.replace(" ", "")
    pos = 0

    def voir():
        return s[pos] if pos < len(s) else None

    def union():
        nonlocal pos
        branches = [concat()]
        while voir() in ("|", "+"):
            pos += 1
            branches.append(concat())
        return branches[0] if len(branches) == 1 else ("|", branches)

    def concat():
        morceaux = []
        while voir() is not None and voir() not in ("|", "+", ")"):
            morceaux.append(etoile())
        if not morceaux:
            raise ValueError(f"expression vide ou mal formee : {expr!r}")
        return morceaux[0] if len(morceaux) == 1 else (".", morceaux)

    def etoile():
        nonlocal pos
        g = atome()
        while voir() == "*":
            pos += 1
            g = ("*", g)
        return g

    def atome():
        nonlocal pos
        c = voir()
        if c == "(":
            pos += 1
            g = union()
            if voir() != ")":
                raise ValueError(f"parenthese non fermee : {expr!r}")
            pos += 1
            return g
        if c is None or c in "|+*)":
            raise ValueError(f"caractere inattendu en position {pos} : {expr!r}")
        pos += 1
        return ["eps"] if c == "ε" else ["l", c]  # des listes : chaque feuille est un objet distinct (id)

    arbre = union()
    if pos != len(s):
        raise ValueError(f"caractere inattendu en position {pos} : {expr!r}")
    return arbre


def thompson(expr, alphabet=None):
    """Construction de Thompson : un petit automate par morceau, recolle par des epsilon-transitions.

    Une lettre : deux etats et une fleche. Une concatenation : la fin d'un morceau reliee au debut du suivant.
    Une union : un nouvel etat de depart vers chaque morceau, et chaque morceau vers un nouvel etat de fin. Une
    etoile : un retour de la fin au debut, et un passage direct du depart a l'arrivee. Les etats sont numerotes
    0, 1, 2... dans l'ordre de creation.
    """
    fleches, compteur = [], [0]

    def nouveau():
        compteur[0] += 1
        return compteur[0] - 1

    # parcours sans recursion : chaque noeud est empile deux fois, avant et apres ses enfants
    racine = _analyser(expr)
    resultats, pile = {}, [(racine, False)]
    while pile:
        n, enfants_faits = pile.pop()
        enfants = n[1] if n[0] in (".", "|") else [n[1]] if n[0] == "*" else []
        if not enfants_faits:
            i = nouveau() if n[0] in ("|", "*") else None
            resultats[id(n)] = [i]
            pile.append((n, True))
            for e in reversed(enfants):
                pile.append((e, False))
            continue
        if n[0] in ("l", "eps"):
            i, f = nouveau(), nouveau()
            fleches.append((i, n[1] if n[0] == "l" else EPS, f))
        elif n[0] == ".":
            bouts = [resultats.pop(id(e)) for e in enfants]
            fleches.extend((f1, EPS, i2) for (_, f1), (i2, _) in zip(bouts, bouts[1:]))
            i, f = bouts[0][0], bouts[-1][1]
        elif n[0] == "|":
            i = resultats[id(n)][0]
            bouts = [resultats.pop(id(e)) for e in enfants]
            f = nouveau()
            for i1, f1 in bouts:
                fleches.extend([(i, EPS, i1), (f1, EPS, f)])
        else:  # etoile
            i = resultats[id(n)][0]
            i1, f1 = resultats.pop(id(enfants[0]))
            f = nouveau()
            fleches.extend([(i, EPS, i1), (f1, EPS, i1), (i, EPS, f), (f1, EPS, f)])
        resultats[id(n)] = (i, f)
    i, f = resultats[id(racine)]
    lettres = alphabet or tuple(sorted({a for _, a, _ in fleches if a != EPS}))
    return automate(fleches, {i}, {f}, alphabet=lettres, etats=list(range(compteur[0])))


def en_regex_python(expr):
    """Traduit la notation des cours pour le module re de Python, qui sert de juge : union '+' -> '|', mot
    vide -> groupe vide '()', et chaque lettre echappee (une lettre '.' reste une lettre)."""
    sortie = []
    for c in expr.replace(" ", ""):
        if c == "+":
            sortie.append("|")
        elif c == "ε":
            sortie.append("()")
        elif c in "|*()":
            sortie.append(c)
        else:
            sortie.append(re.escape(c))
    return "".join(sortie)


# --- Affichage -----------------------------------------------------------------------------------------------

def table_transitions(A):
    """La table de transitions en texte : -> marque l'etat initial, * les etats finaux, - une case vide."""
    lignes, rang = [], {q: i for i, q in enumerate(A.etats)}
    larg = max(len(str(q)) for q in A.etats) + 6
    cases = [max(len(", ".join(str(r) for r in A.suivants(q, a))) for q in A.etats) for a in A.alphabet]
    cases = [max(c, 1, len(a)) + 2 for c, a in zip(cases, A.alphabet)]
    entete = " " * larg + "".join(a.ljust(c) for a, c in zip(A.alphabet, cases))
    lignes.append(entete.rstrip())
    for q in A.etats:
        marque = ("->" if q in A.initiaux else "  ") + ("*" if q in A.finaux else " ")
        cellules = []
        for a, c in zip(A.alphabet, cases):
            v = A.suivants(q, a)
            cellules.append((", ".join(str(r) for r in sorted(v, key=rang.__getitem__)) if v else "-").ljust(c))
        lignes.append((marque + " " + str(q)).ljust(larg) + "".join(cellules).rstrip())
    return "\n".join(lignes)
