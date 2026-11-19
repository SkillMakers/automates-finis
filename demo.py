"""Le cours et les quatre exercices, executes. Chaque table est celle qu'on ecrit sur la copie.

    python demo.py
"""
import re
import time

from automates import (accepte, complementaire, complementaire_naif, determiniser, difference, en_regex_python,
                       est_complet, est_deterministe, lire, minimiser, mots, table_transitions, thompson)
from enonces import (CONTIENT_ABA, EX3_A_LA_MAIN, FINIT_PAR_AB, PAIR_DE_A, PAIR_DE_A_EN_4, REGEX_EX3,
                     kieme_avant_la_fin, langage_ex3)


def titre(t):
    print()
    print("=" * 78)
    print(t)
    print("=" * 78)


def etapes_moore(etapes):
    for i, p in enumerate(etapes):
        print(f"  etape {i} : " + " | ".join("{" + " ".join(str(q) for q in c) + "}" for c in p))


titre("COURS 1 - automate deterministe : nombre pair de a")
print(table_transitions(PAIR_DE_A))
etat = "P"
trace = [etat]
for lettre in "abba":
    etat = next(iter(PAIR_DE_A.suivants(etat, lettre)))
    trace.append(etat)
print("lecture de abba :", " -> ".join(trace), "| accepte :", accepte(PAIR_DE_A, "abba"))
print("lecture de aba  :", "accepte :", accepte(PAIR_DE_A, "aba"))

titre("COURS 2 - automate non deterministe : finit par ab")
print(table_transitions(FINIT_PAR_AB))
print("deterministe :", est_deterministe(FINIT_PAR_AB), "| complet :", est_complet(FINIT_PAR_AB))
for prefixe in ["", "a", "aa", "aab"]:
    print(f"apres {prefixe or 'le mot vide'!r:6} : etats possibles {sorted(lire(FINIT_PAR_AB, prefixe))}")
print("aab accepte :", accepte(FINIT_PAR_AB, "aab"), "| aba accepte :", accepte(FINIT_PAR_AB, "aba"))

titre("COURS 3 - determinisation de finit par ab")
D, _ = determiniser(FINIT_PAR_AB)
print(table_transitions(D))
print("meme langage :", difference(FINIT_PAR_AB, D) is None)

titre("COURS 4 - l'explosion : la k-ieme lettre avant la fin est un a")
print(" k   etats non det.   etats det.   etats minimaux   temps")
for k in range(1, 13):
    A = kieme_avant_la_fin(k)
    t0 = time.perf_counter()
    D, _ = determiniser(A)
    M, _ = minimiser(D)
    dt = time.perf_counter() - t0
    print(f"{k:2}   {len(A.etats):10}   {len(D.etats):10}   {len(M.etats):14}   {dt:6.3f} s")

titre("COURS 5 - Moore sur nombre pair de a, ecrit avec 4 etats")
print(table_transitions(PAIR_DE_A_EN_4))
M, etapes = minimiser(PAIR_DE_A_EN_4)
etapes_moore(etapes)
print(table_transitions(M))
print("meme langage que l'automate a 2 etats :", difference(M, PAIR_DE_A) is None)

titre("COURS 6 - Thompson sur a(a+b)*b")
T = thompson(REGEX_EX3)
nb_eps = sum(len(v) for (q, a), v in T.delta.items() if a == "")
print(f"{len(T.etats)} etats, {nb_eps} epsilon-transitions")
print("meme langage que l'automate a la main :", difference(T, EX3_A_LA_MAIN) is None)

titre("EXERCICE 1 - determiniser contient aba")
print(table_transitions(CONTIENT_ABA))
D1, table = determiniser(CONTIENT_ABA)
print()
print(table_transitions(D1))
print(f"{len(D1.etats)} etats ; meme langage : {difference(CONTIENT_ABA, D1) is None}")

titre("EXERCICE 2 - minimiser le resultat (Moore)")
M1, etapes = minimiser(D1)
etapes_moore(etapes)
print(table_transitions(M1))
print(f"{len(M1.etats)} etats ; meme langage : {difference(M1, CONTIENT_ABA) is None}")

titre("EXERCICE 3 - a(a+b)*b : automate a la main, puis deterministe complet")
print(table_transitions(EX3_A_LA_MAIN))
D3, _ = determiniser(EX3_A_LA_MAIN)
print()
print(table_transitions(D3))
juge = re.compile(en_regex_python(REGEX_EX3))
ecarts = [m for m in mots("ab", 10) if accepte(D3, m) != bool(juge.fullmatch(m))]
print(f"compare au module re sur les {2 ** 11 - 1} mots de 0 a 10 lettres : {len(ecarts)} ecart")

titre("EXERCICE 4 - le complementaire de a(a+b)*b (le piege)")
D3_incomplet, _ = determiniser(EX3_A_LA_MAIN, garder_vide=False)
essais = [("inverser les finaux de l'automate non deterministe", complementaire_naif(EX3_A_LA_MAIN)),
          ("inverser les finaux du deterministe SANS puits", complementaire_naif(D3_incomplet)),
          ("determiniser, completer, puis inverser", complementaire(EX3_A_LA_MAIN))]
for nom, C in essais:
    faux = [m for m in mots("ab", 8) if accepte(C, m) == langage_ex3(m)]
    print(f"{nom} :")
    print(f"   {len(faux)} mots mal classes sur {2 ** 9 - 1} (0 a 8 lettres)"
          + (f", par exemple {', '.join(repr(m) for m in faux[:4])}" if faux else ""))
for m in ["b", "ab"]:
    print(f"{m!r} : dans le langage {langage_ex3(m)} | naif non det. {accepte(essais[0][1], m)}"
          f" | naif sans puits {accepte(essais[1][1], m)} | correct {accepte(essais[2][1], m)}")
print(table_transitions(essais[2][1]))
