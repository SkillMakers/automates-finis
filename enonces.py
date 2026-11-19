"""Les automates de la video : les exemples du cours et les quatre exercices. Alphabet {a, b} partout."""
from automates import automate

AB = ("a", "b")

# Cours 1 : automate deterministe, « nombre pair de a »
PAIR_DE_A = automate([("P", "a", "I"), ("P", "b", "P"), ("I", "a", "P"), ("I", "b", "I")],
                     {"P"}, {"P"}, alphabet=AB)

# Cours 2 : automate non deterministe, « finit par ab »
FINIT_PAR_AB = automate([(0, "a", 0), (0, "b", 0), (0, "a", 1), (1, "b", 2)], {0}, {2}, alphabet=AB)

# Cours 3 : le meme langage que PAIR_DE_A, ecrit avec quatre etats (1 et 3 : pair ; 2 et 4 : impair)
PAIR_DE_A_EN_4 = automate([(1, "a", 2), (1, "b", 3), (2, "a", 3), (2, "b", 4),
                           (3, "a", 4), (3, "b", 1), (4, "a", 1), (4, "b", 2)], {1}, {1, 3}, alphabet=AB)

# Cours 4 : l'explosion. « La k-ieme lettre avant la fin est un a » : k + 1 etats non deterministes.
def kieme_avant_la_fin(k):
    fleches = [(0, "a", 0), (0, "b", 0), (0, "a", 1)]
    fleches += [(i, c, i + 1) for i in range(1, k) for c in AB]
    return automate(fleches, {0}, {k}, alphabet=AB)


# Exercice 1 (puis 2) : « contient aba », non deterministe ; determiniser, puis minimiser
CONTIENT_ABA = automate([(0, "a", 0), (0, "b", 0), (0, "a", 1), (1, "b", 2), (2, "a", 3),
                         (3, "a", 3), (3, "b", 3)], {0}, {3}, alphabet=AB)

# Exercice 3 : l'automate de a(a+b)*b, ecrit a la main (3 etats), a determiniser et completer
REGEX_EX3 = "a(a+b)*b"
EX3_A_LA_MAIN = automate([(0, "a", 1), (1, "a", 1), (1, "b", 1), (1, "b", 2)], {0}, {2}, alphabet=AB)

# Exercice 4 : le complementaire du langage de l'exercice 3 (le piege)


def langage_ex3(mot):
    return mot.startswith("a") and mot.endswith("b")
