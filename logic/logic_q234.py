# ------------------------------------------------------------------------
# logic_q234.py
# Questions 2, 3 and 4 - Propositional logic.
#
# The written answers in answers.md were worked out by hand. This program
# checks them using the algorithms from AIMA 4th ed., Chapter 7:
#
#   truth_table() / classify()   model checking by enumeration, the same
#                                idea as TT-ENTAILS (Section 7.4.4): try
#                                every model (row of the truth table)
#   count_models()               number of models of a sentence over a
#                                given vocabulary (Question 3)
#   cnf_steps()                  conversion to CNF, one step at a time
#                                (Section 7.5.2):
#                                  1. eliminate <=>   2. eliminate =>
#                                  3. move NOT inwards 4. distribute OR over AND
#   pl_resolution()              PL-RESOLUTION (Section 7.5.2):
#
#     function PL-RESOLUTION(KB, a) returns true or false
#       clauses <- the set of clauses in the CNF representation of KB AND NOT a
#       new <- {}
#       while true do
#         for each pair of clauses Ci, Cj in clauses do
#           resolvents <- PL-RESOLVE(Ci, Cj)
#           if resolvents contains the empty clause then return true
#           new <- new UNION resolvents
#         if new SUBSET-OF clauses then return false
#         clauses <- clauses UNION new
#
# Sentences can be typed with ASCII or the book's symbols:
#   not: ~ or ¬    and: & or ∧    or: | or ∨    implies: => or ⇒    iff: <=> or ⇔
#
# Run from the project root:   python -m logic.logic_q234
# ------------------------------------------------------------------------

import itertools
import re
import sys
from dataclasses import dataclass

# ====================== 1. Sentences (syntax) ===========================
# Each kind of sentence is a small class with value(model), which gives
# its truth value in a model (a dict like {"Smoke": True, "Fire": False}).


@dataclass(frozen=True)
class Symbol:
    name: str

    def value(self, model):
        return model[self.name]

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class Not:
    arg: object

    def value(self, model):
        return not self.arg.value(model)

    def __str__(self):
        return f"¬{wrap(self.arg)}"


@dataclass(frozen=True)
class And:
    args: tuple

    def value(self, model):
        return all(a.value(model) for a in self.args)

    def __str__(self):
        return " ∧ ".join(wrap(a) for a in self.args)


@dataclass(frozen=True)
class Or:
    args: tuple

    def value(self, model):
        return any(a.value(model) for a in self.args)

    def __str__(self):
        return " ∨ ".join(wrap(a) for a in self.args)


@dataclass(frozen=True)
class Implies:
    left: object
    right: object

    def value(self, model):
        # P => Q is false only when P is true and Q is false
        return (not self.left.value(model)) or self.right.value(model)

    def __str__(self):
        return f"{wrap(self.left)} ⇒ {wrap(self.right)}"


@dataclass(frozen=True)
class Iff:
    left: object
    right: object

    def value(self, model):
        return self.left.value(model) == self.right.value(model)

    def __str__(self):
        return f"{wrap(self.left)} ⇔ {wrap(self.right)}"


def wrap(e):
    # Adds brackets around compound parts when printing.
    return str(e) if isinstance(e, (Symbol, Not)) else f"({e})"


def symbols(e):
    # The proposition symbols used in a sentence, in order of first
    # appearance: "Smoke => Fire" -> ["Smoke", "Fire"].
    if isinstance(e, Symbol):
        return [e.name]
    if isinstance(e, Not):
        return symbols(e.arg)
    parts = e.args if isinstance(e, (And, Or)) else (e.left, e.right)
    names = []
    for part in parts:
        names += [n for n in symbols(part) if n not in names]
    return names


# ====================== 2. Parser =======================================
# Turns text like "(Smoke & Heat) => Fire" into a sentence object.
# Precedence (strongest first), as in the book: ¬, ∧, ∨, ⇒, ⇔

TOKEN = re.compile(r"\s*(<=>|⇔|=>|⇒|~|¬|&|∧|\||∨|\(|\)|[A-Za-z_][A-Za-z_0-9]*)")
ALIASES = {"⇔": "<=>", "⇒": "=>", "¬": "~", "∧": "&", "∨": "|"}


def parse(text):
    tokens, pos = [], 0
    text = text.strip()
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m:
            raise ValueError(f"cannot read {text[pos:]!r}")
        tokens.append(ALIASES.get(m.group(1), m.group(1)))
        pos = m.end()
        while pos < len(text) and text[pos].isspace():
            pos += 1

    def peek():
        return tokens[0] if tokens else None

    def take(expected=None):
        tok = tokens.pop(0)
        if expected and tok != expected:
            raise ValueError(f"expected {expected!r}, got {tok!r}")
        return tok

    def iff():
        left = implies()
        if peek() == "<=>":
            take()
            return Iff(left, iff())
        return left

    def implies():
        left = disjunction()
        if peek() == "=>":
            take()
            return Implies(left, implies())     # => groups to the right
        return left

    def disjunction():
        args = [conjunction()]
        while peek() == "|":
            take()
            args.append(conjunction())
        return args[0] if len(args) == 1 else Or(tuple(args))

    def conjunction():
        args = [negation()]
        while peek() == "&":
            take()
            args.append(negation())
        return args[0] if len(args) == 1 else And(tuple(args))

    def negation():
        if peek() == "~":
            take()
            return Not(negation())
        if peek() == "(":
            take("(")
            e = iff()
            take(")")
            return e
        return Symbol(take())

    sentence = iff()
    if tokens:
        raise ValueError(f"unexpected {tokens[0]!r}")
    return sentence


# ====================== 3. Truth tables (Questions 2, 3, 4a) ============

def all_models(names):
    # Every combination of True/False for the symbols: 2^n models.
    # Order: T before F, like the truth tables in the book.
    for values in itertools.product([True, False], repeat=len(names)):
        yield dict(zip(names, values))


def truth_table(e, vocabulary=None):
    # List of (model, value of e in that model).
    names = vocabulary or symbols(e)
    return [(m, e.value(m)) for m in all_models(names)]


def classify(e):
    # valid         = true in EVERY model
    # unsatisfiable = true in NO model
    # neither       = true in some models (satisfiable but not valid)
    values = [v for _, v in truth_table(e)]
    if all(values):
        return "valid"
    if not any(values):
        return "unsatisfiable"
    return "neither"


def count_models(e, vocabulary):
    # Number of models (over the WHOLE vocabulary) in which e is true.
    # Symbols not in e can be anything, so each one doubles the count.
    return sum(v for _, v in truth_table(e, vocabulary))


def equivalent(a, b):
    # Two sentences are equivalent if they agree in every model.
    names = symbols(a) + [n for n in symbols(b) if n not in symbols(a)]
    return all(a.value(m) == b.value(m) for m in all_models(names))


# ====================== 4. Conversion to CNF (Question 4b) ==============

def eliminate_iff(e):
    # a ⇔ b   becomes   (a ⇒ b) ∧ (b ⇒ a)
    if isinstance(e, Symbol):
        return e
    if isinstance(e, Not):
        return Not(eliminate_iff(e.arg))
    if isinstance(e, (And, Or)):
        return type(e)(tuple(eliminate_iff(a) for a in e.args))
    left, right = eliminate_iff(e.left), eliminate_iff(e.right)
    if isinstance(e, Iff):
        return And((Implies(left, right), Implies(right, left)))
    return Implies(left, right)


def eliminate_implies(e):
    # a ⇒ b   becomes   ¬a ∨ b
    if isinstance(e, Symbol):
        return e
    if isinstance(e, Not):
        return Not(eliminate_implies(e.arg))
    if isinstance(e, (And, Or)):
        return type(e)(tuple(eliminate_implies(a) for a in e.args))
    return Or((Not(eliminate_implies(e.left)), eliminate_implies(e.right)))


def move_not_inwards(e):
    # ¬¬a        becomes  a                  (double negation)
    # ¬(a ∧ b)   becomes  ¬a ∨ ¬b            (De Morgan)
    # ¬(a ∨ b)   becomes  ¬a ∧ ¬b            (De Morgan)
    if isinstance(e, Symbol):
        return e
    if isinstance(e, (And, Or)):
        return type(e)(tuple(move_not_inwards(a) for a in e.args))
    a = e.arg
    if isinstance(a, Symbol):
        return e
    if isinstance(a, Not):
        return move_not_inwards(a.arg)
    if isinstance(a, And):
        return Or(tuple(move_not_inwards(Not(x)) for x in a.args))
    return And(tuple(move_not_inwards(Not(x)) for x in a.args))


def flatten(e):
    # (a ∨ b) ∨ c  becomes  a ∨ b ∨ c, and repeated parts are removed
    # (a ∨ a  becomes  a), keeping the first one.
    if isinstance(e, (Symbol, Not)):
        return e
    args = []
    for a in (flatten(x) for x in e.args):
        for part in (a.args if type(a) is type(e) else (a,)):
            if part not in args:
                args.append(part)
    return args[0] if len(args) == 1 else type(e)(tuple(args))


def distribute(e):
    # a ∨ (b ∧ c)  becomes  (a ∨ b) ∧ (a ∨ c)
    e = flatten(e)
    if isinstance(e, And):
        return flatten(And(tuple(distribute(a) for a in e.args)))
    if isinstance(e, Or):
        args = [distribute(a) for a in e.args]
        for i, a in enumerate(args):
            if isinstance(a, And):
                rest = args[:i] + args[i + 1:]
                return distribute(And(tuple(Or(tuple(rest + [x])) for x in a.args)))
        return flatten(Or(tuple(args)))
    return e


def cnf_steps(e):
    # Returns every step of the conversion as (description, sentence).
    steps = [("original", e)]
    for name, rule in (("1. eliminate ⇔", eliminate_iff),
                       ("2. eliminate ⇒", eliminate_implies),
                       ("3. move ¬ inwards", move_not_inwards),
                       ("4. distribute ∨ over ∧ and simplify", distribute)):
        new = rule(e)
        steps.append((name if new != e else name + " (no change)", new))
        e = new
    return steps


def to_cnf(e):
    return cnf_steps(e)[-1][1]


def clauses(cnf):
    # Turns a CNF sentence into a list of clauses. A clause is a frozenset
    # of literals, and a literal is a string like "P" or "¬P".
    def literal(x):
        return str(x)

    parts = cnf.args if isinstance(cnf, And) else (cnf,)
    result = []
    for part in parts:
        lits = part.args if isinstance(part, Or) else (part,)
        result.append(frozenset(literal(x) for x in lits))
    return result


# ====================== 5. Resolution (Question 4c) =====================

def negate(literal):
    return literal[1:] if literal.startswith("¬") else "¬" + literal


def is_tautology(clause):
    # A clause with both P and ¬P is always true, so it is useless.
    return any(negate(lit) in clause for lit in clause)


def pl_resolve(ci, cj):
    # All clauses we get by resolving ci and cj on ONE complementary pair.
    # From (A ∨ B) and (¬B ∨ C) we get (A ∨ C).
    resolvents = []
    for lit in ci:
        if negate(lit) in cj:
            r = frozenset((ci - {lit}) | (cj - {negate(lit)}))
            if not is_tautology(r):
                resolvents.append(r)
    return resolvents


def pl_resolution(kb_clauses, query_negated_clauses):
    # PL-RESOLUTION. Returns (True, proof) if the empty clause is derived,
    # otherwise (False, []). proof = list of (clause, parent1, parent2)
    # for every clause used to reach the empty clause.
    clauses_set = set(kb_clauses) | set(query_negated_clauses)
    parents = {c: None for c in clauses_set}       # None = given clause
    while True:
        new = set()
        ordered = sorted(clauses_set, key=lambda c: (len(c), sorted(c)))
        for ci, cj in itertools.combinations(ordered, 2):
            for r in pl_resolve(ci, cj):
                if r not in parents:
                    parents[r] = (ci, cj)
                if not r:                           # the empty clause
                    return True, _proof(r, parents)
                new.add(r)
        if new <= clauses_set:
            return False, []
        clauses_set |= new


def _proof(clause, parents):
    # Walks back from the empty clause to list only the steps it needs.
    steps, seen = [], set()

    def visit(c):
        if c in seen or parents[c] is None:
            return
        seen.add(c)
        a, b = parents[c]
        visit(a)
        visit(b)
        steps.append((c, a, b))

    visit(clause)
    return steps


def prove_valid(e):
    # A sentence is valid exactly when its negation is unsatisfiable,
    # so we add ¬sentence (with an empty KB) and look for a contradiction.
    return pl_resolution([], clauses(to_cnf(Not(e))))


def show_clause(c):
    return "{" + ", ".join(sorted(c, key=lambda lit: lit.lstrip("¬"))) + "}" if c else "{} (empty clause)"


# ====================== 6. Printing the answers =========================

def print_truth_table(e, vocabulary=None, columns=()):
    # Prints the truth table; `columns` are extra sub-sentences to show.
    names = vocabulary or symbols(e)
    heads = names + [str(c) for c in columns] + [str(e)]
    print(" | ".join(heads))
    for model, value in truth_table(e, names):
        cells = [model[n] for n in names] + [c.value(model) for c in columns] + [value]
        print(" | ".join(("T" if v else "F").center(len(h)) for v, h in zip(cells, heads)))


def main():
    # The logic symbols (¬ ∧ ∨ ⇒ ⇔) need UTF-8; the Windows console
    # does not use it by default.
    sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 70, "\nQuestion 2 - valid, unsatisfiable or neither?\n")
    for label, text in (("a", "Smoke => Fire"),
                        ("b", "((Smoke & Heat) => Fire) <=> ((Smoke => Fire) | (Heat => Fire))")):
        e = parse(text)
        print(f"({label}) {e}")
        columns = [] if label == "a" else [e.left, e.right]
        print_truth_table(e, columns=columns)
        print(f"=> {classify(e)}\n")

    print("=" * 70, "\nQuestion 3 - number of models over {A, B, C, D}\n")
    for label, text in (("a", "B | C"), ("b", "(A => B) & A & ~B & C & D")):
        e = parse(text)
        print(f"({label}) {e}: {count_models(e, ['A', 'B', 'C', 'D'])} models out of 16")
    print()

    print("=" * 70, "\nQuestion 4\n")
    s = parse("((Food => Party) | (Drinks => Party)) => ((Food & Drinks) => Party)")
    print(f"(a) {s}")
    print_truth_table(s, columns=[s.left, s.right])
    print(f"=> {classify(s)}\n")

    print("(b) CNF conversion")
    for side, part in (("Left-hand side", s.left), ("Right-hand side", s.right)):
        print(f"  {side}:")
        for step, e in cnf_steps(part):
            print(f"    {step:38} {e}")
    same = set(clauses(to_cnf(s.left))) == set(clauses(to_cnf(s.right)))
    print(f"  Both sides give the same clause set: {same}\n")

    print("(c) Resolution: clauses of ¬sentence")
    for c in clauses(to_cnf(Not(s))):
        print(f"    {show_clause(c)}")
    proved, proof = prove_valid(s)
    for c, a, b in proof:
        print(f"    {show_clause(a)} + {show_clause(b)}  ->  {show_clause(c)}")
    print(f"  => empty clause derived: {proved}, so the sentence is valid")


if __name__ == "__main__":
    main()
