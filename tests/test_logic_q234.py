# ------------------------------------------------------------------------
# test_logic_q234.py
# Automated tests for Questions 2, 3 and 4 (propositional logic).
# Run from the project root with:   pytest -v
# ------------------------------------------------------------------------

import json
from pathlib import Path

import pytest

from logic.logic_q234 import (And, Not, Or, Symbol, classify, clauses, cnf_steps, count_models,
                              equivalent, parse, pl_resolution, pl_resolve, prove_valid, to_cnf,
                              truth_table)

# Test data: sentences with the expected answers.
CASES = json.loads((Path(__file__).parent / "logic_cases_q234.json").read_text(encoding="utf-8"))

Q4 = "((Food => Party) | (Drinks => Party)) => ((Food & Drinks) => Party)"


def is_cnf(e):
    # True if e is a conjunction of disjunctions of literals.
    def is_literal(x):
        return isinstance(x, Symbol) or (isinstance(x, Not) and isinstance(x.arg, Symbol))

    def is_clause(x):
        return is_literal(x) or (isinstance(x, Or) and all(is_literal(a) for a in x.args))

    return is_clause(e) or (isinstance(e, And) and all(is_clause(a) for a in e.args))


# ==================== 1. Parser ==========================================

def test_parse_ascii_and_unicode_give_the_same_sentence():
    assert parse("(Smoke & Heat) => Fire") == parse("(Smoke ∧ Heat) ⇒ Fire")
    assert parse("~A | B") == parse("¬A ∨ B")


def test_parse_precedence():
    # ¬ binds tighter than ∧, ∧ tighter than ∨, ∨ tighter than ⇒
    assert parse("~A & B | C => D") == parse("(((~A) & B) | C) => D")


def test_parse_rejects_bad_input():
    with pytest.raises((ValueError, IndexError)):
        parse("A & ")
    with pytest.raises(ValueError):
        parse("A ) B")


# ==================== 2. Truth tables (Q2, Q3, Q4a) ======================

def test_truth_table_has_two_to_the_n_rows():
    assert len(truth_table(parse("Smoke => Fire"))) == 4
    assert len(truth_table(parse(Q4))) == 8


def test_implication_is_false_only_when_true_implies_false():
    rows = truth_table(parse("Smoke => Fire"))
    false_rows = [m for m, v in rows if not v]
    assert false_rows == [{"Smoke": True, "Fire": False}]


@pytest.mark.parametrize("case", CASES["classify"], ids=lambda c: c["name"])
def test_classify(case):
    assert classify(parse(case["sentence"])) == case["expected"]


@pytest.mark.parametrize("case", CASES["count_models"], ids=lambda c: c["name"])
def test_count_models(case):
    assert count_models(parse(case["sentence"]), case["vocabulary"]) == case["expected"]


def test_q2b_both_sides_are_equivalent():
    # Q2b is valid BECAUSE its two sides are equivalent sentences.
    s = parse("((Smoke & Heat) => Fire) <=> ((Smoke => Fire) | (Heat => Fire))")
    assert equivalent(s.left, s.right)


# ==================== 3. CNF (Q4b) =======================================

@pytest.mark.parametrize("text", [
    Q4, "A <=> B", "~(A & (B | C))", "(A & B) | (C & D)", "((Smoke & Heat) => Fire) <=> ((Smoke => Fire) | (Heat => Fire))",
])
def test_cnf_is_in_cnf_and_equivalent(text):
    # Every conversion must give a CNF sentence with the same models.
    e = parse(text)
    cnf = to_cnf(e)
    assert is_cnf(cnf)
    assert equivalent(e, cnf)


def test_every_cnf_step_keeps_the_meaning():
    e = parse(Q4)
    for _, step in cnf_steps(e):
        assert equivalent(e, step)


def test_q4_both_sides_have_the_same_cnf():
    s = parse(Q4)
    expected = {frozenset({"¬Food", "¬Drinks", "Party"})}
    assert set(clauses(to_cnf(s.left))) == expected
    assert set(clauses(to_cnf(s.right))) == expected


def test_distribute_or_over_and():
    cnf = to_cnf(parse("A | (B & C)"))
    assert set(clauses(cnf)) == {frozenset({"A", "B"}), frozenset({"A", "C"})}


# ==================== 4. Resolution (Q4c) ================================

def test_pl_resolve_one_pair():
    # (A ∨ B) and (¬B ∨ C) resolve to (A ∨ C)
    assert pl_resolve(frozenset({"A", "B"}), frozenset({"¬B", "C"})) == [frozenset({"A", "C"})]


def test_pl_resolve_complementary_units_give_empty_clause():
    assert pl_resolve(frozenset({"P"}), frozenset({"¬P"})) == [frozenset()]


def test_pl_resolve_skips_tautologies():
    # Resolving on P leaves Q ∨ ¬Q, which is always true, so it is dropped.
    assert pl_resolve(frozenset({"P", "Q"}), frozenset({"¬P", "¬Q"})) == []


@pytest.mark.parametrize("case", CASES["resolution"], ids=lambda c: c["name"])
def test_resolution(case):
    kb = [c for text in case["kb"] for c in clauses(to_cnf(parse(text)))]
    negated_query = clauses(to_cnf(Not(parse(case["query"]))))
    proved, _ = pl_resolution(kb, negated_query)
    assert proved == case["expected"]


def test_q4_resolution_proof_ends_with_the_empty_clause():
    proved, proof = prove_valid(parse(Q4))
    assert proved
    assert proof[-1][0] == frozenset()             # last step derives {}
    assert len(proof) == 3                         # ¬Party, then Food, then Drinks


def test_resolution_agrees_with_truth_tables():
    # Resolution says "valid" exactly when the truth table does.
    for case in CASES["classify"]:
        e = parse(case["sentence"])
        assert prove_valid(e)[0] == (classify(e) == "valid")
