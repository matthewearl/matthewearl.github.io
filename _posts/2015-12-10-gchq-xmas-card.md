---
layout: default
title: Solving the GCHQ christmas card with Python and pycosat
---

{% include post-title.html %}

{% include img.html src="/assets/gchq-xmas-card/header.jpg" alt="Header" %}
<sup>(c) GCHQ</sup>

## Introduction

As you may have seen, Britain's intelligence organization
[GCHQ](https://en.wikipedia.org/wiki/Government_Communications_Headquarters)
has released a Christmas card [featuring a grid-shading
puzzle](http://www.gchq.gov.uk/press_and_media/news_and_features/Pages/
Directors-Christmas-puzzle-2015.aspx).

The puzzle is an instance of a [Nonogram puzzle](https://en.wikipedia.org/
wiki/ Nonogram), which is a grid with numbers by each row and column,
indicating the lengths of runs of shaded cells in the completed puzzle.

Being the over-zealous programmer I am I immediately dispensed with the idea
that I might fill the grid in manually, instead leaping to trusty Python and
some rusty CS knowledge. While it may not have saved me time over doing it by
hand, it certainly was more interesting! Also the same script can be re-used to
solve other Nonogram puzzles, so it's potentially useful beyond this teaser.

In this post I'll explain how my script works, with the disclaimer that I don't
claim to be an expert in CNF or SAT solvers. This approach may not even be
more efficient than a basic backtracking algorithm, although it certainly
*feels* more elegant.

## SAT solvers

I decided to solve the problem by expressing it as a boolean formula in
[Conjunctive normal
form](https://en.wikipedia.org/wiki/Conjunctive_normal_form) (CNF) and feeding
the result into a [SAT
solver](https://en.wikipedia.org/wiki/
Boolean_satisfiability_problem#Algorithms_for_solving_SAT). My reasons for
doing this were as follows:

* [The problem is NP-complete](https://en.wikipedia.org/wiki/
  Nonogram#Nonograms_in_computing). As such I felt justified in reducing it to
  an instance of the satisfiability problem (also NP-complete).
* Other, ostensibly similar problems such as Sudoku are [tersely expressibly in
  CNF](https://www.lri.fr/~conchon/mpri/weber.pdf).
* There's an easy to use Python binding to the SAT solver
  [picosat](http://fmv.jku.at/picosat/), in the form of
  [pycosat](https://pypi.python.org/pypi/pycosat).

So what exactly is CNF, and what is a SAT solver? In short, CNF is a way of
writing a boolean formula, eg:

$$A \wedge (B \vee \neg (D \vee E))$$

as series of *AND*s of *ORs*, where *NOT*s may only appear directly applied to
variables:

$$A \wedge (B \vee \neg D) \wedge (B \vee \neg E)$$

A SAT solver is a program which, given a boolean formula in CNF, assigns truth
values to the variables of the formula such that the formula is true. Each such
assignment is a solution to the boolean satisfiability problem. Above, \\(A =
True, B = True, C = False, D = True\\), is a solution, as is \\(A = True, B =
False, D = True, E = True\\), for example. \\(A = False, B = True, C = True, D =
True\\) is not a solution however.

SAT solving algorithms have been the subject of [intense competition](http://
www.satcompetition.org/) over the past decade due to applications in AI,
circuit design, and automatic theorem proving.  As such we can leverage these
advances just by expressing our problem as CNF.

## Variables ##

So, we're looking to map our puzzle into a CNF expression, with the idea that
we'll be able to read the truth assignments in any solution to determine which
grid cells should be filled in. As such it would seem natural to introduce a
variable \\( shaded_{i,j} \\)for each grid cell, which is true iff the
corresponding cell should be filled in. In our case the grid is 25x25, so we'd
have 625 such variables.

So what should the formula be? Let's start off by writing our clauses out in
English. In the below rules, a "row run" refers to a horizontal sequence of
consecutive shaded cells, each of which corresponds with one of the numbers
down the left hand side of the original puzzle. Similarly, a "column run" is a
vertical sequence of shaded cells, corresponding with the numbers at the top of
the puzzle. With that in mind, here are the rules:

1. A row run being in a particular position implies the corresponding cells are
   shaded.
2. The converse of the above: If a given cell is shaded, then there must be a
   row run that covers this cell.
3. A column run being in a particular position implies the corresponding cells
   are shaded.
4. The converse of the above: If a given cell is shaded, then there must be a
   column run that covers this cell.
5. A row run can be in at most one position.
6. A column run can be in at most one position.
7. A row run being in a particular position implies that the next row runs on
   the same row must appear after the first row run.
8. Same as above but for column runs.
9. Row runs and column runs must not be in invalid positions.
10. Any cells that are shaded in the problem ("givens") must be shaded in the
    solution.

With the above in mind, it seems intuitive to introduce new
variables \\( rowrunpos_{i,j,k} \\) and \\( colrunpos_{i,j,k} \\) with the
following semantics:

* \\( rowrunpos_{i,j,k} \\) is true iff the \\( j^{th} \\) row run on row
  \\( i \\) starts at column \\( k \\).
* \\( colrunpos_{i,j,k} \\) is true iff the \\( j^{th} \\) column run on column
  \\( i \\) starts at row \\( k \\).

This means for each number around the edge of the puzzle we'll have 25 new
variables.

Introducing new variables helps constrain the size of the CNF while
maintaining equivalence. See the [Wikipedia page for CNF](https://
en.wikipedia.org/wiki/Conjunctive_normal_form#Conversion_into_CNF) for an
illustrative example.

The exact choice of where it is best to introduce variables is non-trivial and
is not discussed here.

## CNF clauses ##

With the above in place, we can now more or less directly translate the above
English clauses into CNF clauses. Here's the code for rule #1:

{% highlight python %}
# A row run being present at a particular column implies the corresponding
# cells are shaded.
def row_run_implies_shaded():
    clauses = []
    for (row, run_idx, start_col), run_var in row_run_vars.items():
        run_len = ROW_RUNS[row][run_idx]
        for col in range(start_col,
                         min(start_col + run_len, WIDTH)):
            clauses.append([-run_var.idx, shaded_vars[row, col].idx])
    return clauses
{% endhighlight %}

This is encoding the expression:

$$\forall i \in rows \; \forall j \in (runs\ in\ row\ i) \;
\forall j \in cols \; rowrunpos_i,j,k \implies shaded_i,k$$

Which by expanding the implication is equivalent to:

$$\forall i \in rows \; \forall j \in (runs\ in\ row\ i) \;
\forall j \in cols \; \neg rowrunpos_i,j,k \vee shaded_i,k$$
    
Some things to note about CNF expressions expected by `pycosat`:

* A CNF expression is a list of lists of integers (!= 0).
* Each variable in the formula is represented by an integer > 0. Negative
  numbers may appear in the expression, in which case they correspond with the
  logical NOT of the variable represented by the unnegated number.
* The inner lists represent an OR of the terms contained within that list.
* The outer list represents an AND of the clauses contained within.

In the above code, `row_run_vars[row, run_idx, start_col]` and
`shaded_vars[row, col]` correspond with the variables \\( rowrunpos_{i,j,k} \\)
and \\( shaded_{i,k} \\) respectively. Each variable is represented by a `Var`
object (created by me) which exists to keep track of variable indices
(accessible via the `.idx` attribute).

`ROW_RUNS` encodes the numbers down the left hand side of the puzzle as a list
of lists.

The remaining clauses follow a similar pattern of translation. See [the source
code for the full shebang](https://github.com/matthewearl/gchq-xmas).

## Extracting the solution ##

Having `pycosat` solve the problem is simply a case of calling
`pycosat.solve()`:

{% highlight python %}
solution = pycosat.solve(all_clauses)
{% endhighlight %}

The result encodes a single truth assignment:

* A list of integers (!= 0).
* As before, each integer corresponds with a variable.
* If the integer is negative then the corresponding variable is false in the
  solution, otherwise the variable is true in the solution.

Each variable in the input problem will appear exactly once in the solution.

It's then just a case of mapping the integers back to variables, and displaying
in grid form.

{% highlight python %}
def pretty_print_solution(sol):
    true_var_indices = {t for t in sol if t > 0}
    for row in range(HEIGHT):
        print "".join(".#"[shaded_vars[row, col].idx in true_var_indices]
                                                       for col in range(WIDTH))
    print
{% endhighlight %}

And here is the result:

{% include img.html src="/assets/gchq-xmas-card/output.png" alt="Output" %}
