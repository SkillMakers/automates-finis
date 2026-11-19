"""Tests : chaque resultat cite dans la video, puis les algorithmes compares a des juges independants
(le module re de Python, et une enumeration de tous les mots courts) sur des automates tires au hasard.

    python -m unittest -v
"""
import random
import re
import unittest

from automates import (accepte, automate, complementaire, complementaire_naif, determiniser, difference,
                       en_regex_python, est_complet, est_deterministe, minimiser, mots, thompson)
from enonces import (AB, CONTIENT_ABA, EX3_A_LA_MAIN, FINIT_PAR_AB, PAIR_DE_A, PAIR_DE_A_EN_4, REGEX_EX3,
                     kieme_avant_la_fin, langage_ex3)


def afn_au_hasard(graine, n=5):
    """Un automate non deterministe de n etats : chaque fleche existe avec une probabilite 0,3, quelques
    epsilon-transitions, 1 ou 2 etats initiaux, 1 ou 2 finaux."""
    rnd = random.Random(graine)
    fleches = [(p, a, q) for p in range(n) for a in AB + ("",) for q in range(n)
               if rnd.random() < (0.3 if a else 0.08) and not (a == "" and p == q)]
    initiaux = set(rnd.sample(range(n), rnd.randint(1, 2)))
    finaux = set(rnd.sample(range(n), rnd.randint(1, 2)))
    return automate(fleches, initiaux, finaux, alphabet=AB, etats=list(range(n)))


def nb_comportements(D):
    """Juge de la minimisation, sans Moore : pour chaque etat d'un automate deterministe complet dont tous les
    etats sont accessibles, l'ensemble des mots acceptes en partant de cet etat (mots de 0 a N lettres, N = nombre
    d'etats : deux etats differents se distinguent toujours par un mot plus court). Le nombre de comportements
    differents est le nombre d'etats de l'automate minimal."""
    suffixes = list(mots(AB, len(D.etats)))

    def part_de(q, mot):
        for lettre in mot:
            q = next(iter(D.suivants(q, lettre)))
        return q in D.finaux

    return len({tuple(part_de(q, s) for s in suffixes) for q in D.etats})


def expression_au_hasard(rnd, profondeur=3):
    """Une expression avec des lettres, le mot vide, des etoiles, et des unions avec OU sans parentheses
    (sans parentheses, la priorite de la concatenation sur l'union est mise a l'epreuve)."""
    if profondeur == 0 or rnd.random() < 0.25:
        return rnd.choice(AB + ("ε",))
    forme = rnd.choice(["concat", "union", "union_nue", "etoile"])
    if forme == "etoile":
        return f"({expression_au_hasard(rnd, profondeur - 1)})*"
    g, d = expression_au_hasard(rnd, profondeur - 1), expression_au_hasard(rnd, profondeur - 1)
    if forme == "union":
        return f"({g}+{d})"
    if forme == "union_nue":
        return f"{g}+{d}"
    return f"({g})({d})" if "+" in g + d else f"{g}{d}"


class TestCours(unittest.TestCase):

    def test_nombre_pair_de_a(self):
        """abba (2 a) et aba (2 a) sont acceptes, ab (1 a) est refuse."""
        # WHEN / THEN
        self.assertTrue(est_deterministe(PAIR_DE_A) and est_complet(PAIR_DE_A))
        self.assertTrue(accepte(PAIR_DE_A, "abba"))
        self.assertTrue(accepte(PAIR_DE_A, "aba"))
        self.assertFalse(accepte(PAIR_DE_A, "ab"))
        self.assertTrue(accepte(PAIR_DE_A, ""))

    def test_finit_par_ab_non_deterministe(self):
        """Apres a, on peut etre en 0 ou en 1 : l'automate n'est ni deterministe ni complet."""
        # WHEN / THEN
        self.assertFalse(est_deterministe(FINIT_PAR_AB))
        self.assertFalse(est_complet(FINIT_PAR_AB))
        self.assertTrue(accepte(FINIT_PAR_AB, "aab"))
        self.assertFalse(accepte(FINIT_PAR_AB, "aba"))

    def test_determinisation_du_cours(self):
        """{0}, {0,1}, {0,2} : trois etats, seul {0,2} est final, et aucun ensemble vide."""
        # WHEN
        D, _ = determiniser(FINIT_PAR_AB)
        # THEN
        self.assertEqual(D.etats, ("{0}", "{0,1}", "{0,2}"))
        self.assertEqual(D.finaux, {"{0,2}"})
        self.assertEqual(D.suivants("{0,2}", "a"), {"{0,1}"})
        self.assertEqual(D.suivants("{0,2}", "b"), {"{0}"})
        self.assertIsNone(difference(D, FINIT_PAR_AB))

    def test_explosion(self):
        """k + 1 etats non deterministes donnent 2 puissance k etats, et Moore n'en enleve aucun."""
        for k in range(1, 11):
            # GIVEN
            A = kieme_avant_la_fin(k)
            # WHEN
            D, _ = determiniser(A)
            M, _ = minimiser(D)
            # THEN
            self.assertEqual((len(A.etats), len(D.etats), len(M.etats)), (k + 1, 2 ** k, 2 ** k))

    def test_moore_sur_quatre_etats(self):
        """1 et 3 se confondent, 2 et 4 aussi : la partition de depart ne bouge plus."""
        # WHEN
        M, etapes = minimiser(PAIR_DE_A_EN_4)
        # THEN
        self.assertEqual(etapes, [[[1, 3], [2, 4]]])
        self.assertEqual(len(M.etats), 2)
        self.assertIsNone(difference(M, PAIR_DE_A))

    def test_thompson_du_cours(self):
        """Thompson sur a(a+b)*b : 12 etats et 10 epsilon-transitions, meme langage que l'automate a 3 etats."""
        # WHEN
        T = thompson(REGEX_EX3)
        # THEN
        self.assertEqual(len(T.etats), 12)
        self.assertEqual(sum(len(v) for (q, a), v in T.delta.items() if a == ""), 10)
        self.assertIsNone(difference(T, EX3_A_LA_MAIN))


class TestExercices(unittest.TestCase):

    def test_exercice_1(self):
        """Contient aba : 6 ensembles, dans l'ordre de la copie, dont 3 finaux."""
        # WHEN
        D, _ = determiniser(CONTIENT_ABA)
        # THEN
        self.assertEqual(D.etats, ("{0}", "{0,1}", "{0,2}", "{0,1,3}", "{0,2,3}", "{0,3}"))
        self.assertEqual(D.finaux, {"{0,1,3}", "{0,2,3}", "{0,3}"})
        self.assertEqual(D.suivants("{0,2}", "a"), {"{0,1,3}"})
        self.assertEqual(D.suivants("{0,2}", "b"), {"{0}"})
        self.assertIsNone(difference(D, CONTIENT_ABA))

    def test_exercice_2(self):
        """Moore : finaux / non finaux, puis {0,2} se detache, puis {0} et {0,1} : 4 etats."""
        # GIVEN
        D, _ = determiniser(CONTIENT_ABA)
        # WHEN
        M, etapes = minimiser(D)
        # THEN
        finaux = ["{0,1,3}", "{0,2,3}", "{0,3}"]
        self.assertEqual(etapes, [
            [finaux, ["{0}", "{0,1}", "{0,2}"]],
            [finaux, ["{0}", "{0,1}"], ["{0,2}"]],
            [finaux, ["{0}"], ["{0,1}"], ["{0,2}"]],
        ])
        self.assertEqual(len(M.etats), 4)
        self.assertIsNone(difference(M, CONTIENT_ABA))

    def test_exercice_3(self):
        """a(a+b)*b : {0}, {1}, l'ensemble vide (puits), {1,2} ; memes mots que le module re."""
        # WHEN
        D, _ = determiniser(EX3_A_LA_MAIN)
        # THEN
        self.assertEqual(D.etats, ("{0}", "{1}", "∅", "{1,2}"))
        self.assertEqual(D.finaux, {"{1,2}"})
        self.assertTrue(est_complet(D))
        juge = re.compile(en_regex_python(REGEX_EX3))
        for m in mots(AB, 10):
            self.assertEqual(accepte(D, m), bool(juge.fullmatch(m)), m)

    def test_exercice_4_le_piege(self):
        """Inverser les finaux sans determiniser accepte ab ; sans puits, refuse b ; la bonne methode est juste."""
        # GIVEN
        D_sans_puits, _ = determiniser(EX3_A_LA_MAIN, garder_vide=False)
        naif = complementaire_naif(EX3_A_LA_MAIN)
        sans_puits = complementaire_naif(D_sans_puits)
        bon = complementaire(EX3_A_LA_MAIN)
        # WHEN
        faux = {nom: [m for m in mots(AB, 8) if accepte(C, m) == langage_ex3(m)]
                for nom, C in [("naif", naif), ("sans_puits", sans_puits), ("bon", bon)]}
        # THEN
        self.assertTrue(accepte(naif, "ab"))          # ab est DANS le langage : il devait etre refuse
        self.assertFalse(accepte(naif, "b"))          # b n'y est pas : il devait etre accepte
        self.assertFalse(accepte(sans_puits, "b"))
        self.assertEqual((len(faux["naif"]), len(faux["sans_puits"]), len(faux["bon"])), (382, 255, 0))


class TestContreJuges(unittest.TestCase):

    def test_determinisation_garde_le_langage(self):
        """300 automates au hasard : le determinise est deterministe, complet, et accepte les memes mots."""
        for graine in range(300):
            # GIVEN
            A = afn_au_hasard(graine)
            # WHEN
            D, _ = determiniser(A)
            # THEN
            self.assertTrue(est_deterministe(D) and est_complet(D), graine)
            for m in mots(AB, 7):
                self.assertEqual(accepte(D, m), accepte(A, m), (graine, m))

    def test_minimisation_est_minimale(self):
        """Automates au hasard : Moore garde le langage, et donne autant d'etats que de comportements differents."""
        verifies = 0
        for graine in range(300):
            # GIVEN
            D, _ = determiniser(afn_au_hasard(graine, n=4))
            if len(D.etats) > 9:
                continue  # le juge enumere 2 puissance (N + 1) mots par etat
            # WHEN
            M, _ = minimiser(D)
            # THEN
            self.assertIsNone(difference(M, D), graine)
            self.assertEqual(len(M.etats), nb_comportements(D), graine)
            verifies += 1
        self.assertGreater(verifies, 250)

    def test_complementaire(self):
        """300 automates : le complementaire accepte exactement les mots que l'automate refuse."""
        for graine in range(300):
            # GIVEN
            A = afn_au_hasard(graine)
            # WHEN
            C = complementaire(A)
            # THEN
            for m in mots(AB, 6):
                self.assertNotEqual(accepte(C, m), accepte(A, m), (graine, m))

    def test_thompson_contre_le_module_re(self):
        """300 expressions au hasard : l'automate de Thompson accepte les memes mots que re.fullmatch."""
        rnd = random.Random(2026)
        for _ in range(300):
            # GIVEN
            expr = expression_au_hasard(rnd)
            juge = re.compile(en_regex_python(expr))
            # WHEN
            T = thompson(expr, alphabet=AB)
            # THEN
            for m in mots(AB, 7):
                self.assertEqual(accepte(T, m), bool(juge.fullmatch(m)), (expr, m))

    def test_difference_trouve_le_plus_court_mot(self):
        """Contient aba contre contient ab : le plus court mot qui les separe est ab."""
        # GIVEN
        contient_ab = automate([(0, "a", 0), (0, "b", 0), (0, "a", 1), (1, "b", 2), (2, "a", 2), (2, "b", 2)],
                               {0}, {2}, alphabet=AB)
        # WHEN / THEN
        self.assertEqual(difference(CONTIENT_ABA, contient_ab), "ab")


class TestErreurs(unittest.TestCase):

    def test_moore_refuse_un_non_deterministe(self):
        """Moore sur un automate non deterministe : erreur, il faut determiniser d'abord."""
        # WHEN / THEN
        with self.assertRaises(ValueError):
            minimiser(FINIT_PAR_AB)

    def test_expression_mal_formee(self):
        """Parenthese non fermee, union sans second morceau, etoile en tete, expression vide : erreur."""
        for expr in ["(ab", "a+", "*a", ""]:
            # WHEN / THEN
            with self.assertRaises(ValueError, msg=expr):
                thompson(expr)


class TestCasLimites(unittest.TestCase):

    def test_deux_classes_ne_portent_jamais_le_meme_nom(self):
        """Etats 0, 1, 3, 13 : 1 et 3 fusionnent, 13 reste seul ; les deux classes gardent des noms differents."""
        # GIVEN
        A = automate([(0, "a", 1), (0, "b", 13), (1, "a", 1), (1, "b", 1), (3, "a", 3), (3, "b", 3),
                      (13, "a", 13), (13, "b", 3)], {0}, {1, 3}, alphabet=AB)
        # WHEN
        M, _ = minimiser(A)
        # THEN
        self.assertEqual(len(set(M.etats)), len(M.etats))
        self.assertIsNone(difference(M, A))

    def test_le_puits_prend_un_nom_libre(self):
        """Un etat s'appelle deja P : le puits s'appelle P'."""
        # GIVEN
        A = automate([("P", "a", "I")], {"P"}, {"I"}, alphabet=AB)
        # WHEN
        M, _ = minimiser(A)
        C = complementaire(A)
        # THEN
        self.assertIn("P'", C.etats)
        self.assertIsNone(difference(M, A))
        self.assertEqual([m for m in mots(AB, 4) if accepte(C, m) == accepte(A, m)], [])

    def test_mot_vide_dans_une_expression(self):
        """a suivi de epsilon etoile ne reconnait que a, et le juge re est d'accord."""
        # GIVEN
        expr = "aε*"
        # WHEN
        T = thompson(expr, alphabet=AB)
        juge = re.compile(en_regex_python(expr))
        # THEN
        self.assertEqual([m for m in mots(AB, 4) if accepte(T, m)], ["a"])
        self.assertEqual([m for m in mots(AB, 4) if juge.fullmatch(m)], ["a"])

    def test_priorite_de_l_union(self):
        """a+bc se lit a ou bc, pas (a ou b) puis c."""
        # WHEN
        T = thompson("a+bc")
        # THEN
        self.assertEqual(sorted(m for m in mots(("a", "b", "c"), 3) if accepte(T, m)), ["a", "bc"])

    def test_long_mot_sans_recursion(self):
        """Une concatenation de 1 500 lettres ne depasse pas la limite de recursion de Python."""
        # WHEN
        T = thompson("a" * 1500)
        # THEN
        self.assertTrue(accepte(T, "a" * 1500))
        self.assertFalse(accepte(T, "a" * 1499))

    def test_difference_entre_alphabets_differents(self):
        """a etoile (alphabet {a}) contre un automate sur {a, b} : on compare quand meme : meme langage."""
        # GIVEN
        T = thompson("a*")
        A = automate([(0, "a", 0)], {0}, {0}, alphabet=("b", "a"))
        # WHEN / THEN
        self.assertIsNone(difference(T, A))

    def test_deux_etats_qui_s_affichent_pareil(self):
        """Les etats 1 et '1' sont refuses : leurs ensembles s'ecriraient de la meme facon."""
        # WHEN / THEN
        with self.assertRaises(ValueError):
            automate([(1, "a", "1")], {1}, {1})


if __name__ == "__main__":
    unittest.main()
