---
layout: default
title: Solving the GCHQ christmas card with Python and pycosat
---

{% include post-title.html %}

{% include img.html src="/assets/gchq-xmas-card/header.png" alt="Header" %}

## Introduction

As you may have seen, Britain's intelligence organization
[GCHQ](https://en.wikipedia.org/wiki/Government_Communications_Headquarters)
has released a Christmas card [featuring a grid-shading
puzzle](http://www.gchq.gov.uk/press_and_media/news_and_features/Pages/
Directors-Christmas-puzzle-2015.aspx). The puzzle is the first stage of a
sequence of puzzles. After all stages are completed, GCHQ's director Robert
Hannigan invites you to submit your solution (before Feb next year) in order to
win an unspecified prize.

Anyway, back to the puzzle. Being the over-zealous programmer I am I
immediately dispensed with the idea that I might fill the grid in manually,
instead leaping to trusty Python. While it may not have saved me time over
doing it by hand, it certainly was less tedious! Also the same script can be
re-used to solve other [Nonogram puzzles](https://en.wikipedia.org/wiki/
Nonogram), so the same script can be repurposed to solve those too.

In this post I'll explain how my script works, with the disclaimer that I don't
claim to be an expert in CNF or SAT solvers. Please let me know if there's
anything I've missed!

## SAT solvers

I decided to solve the problem by expressing it as a boolean formula in
[Conjunctive normal
form](https://en.wikipedia.org/wiki/Conjunctive_normal_form). My reasons for
doing this were threefold:

* [The problem is NP-complete](https://en.wikipedia.org/wiki/
  Nonogram#Nonograms_in_computing). As such I felt justified in reducing it to
  an instance of the satisfiability problem (also NP-complete).
* Other, ostensibly similar problems such as Sudoku are [tersely expressibly in
  CNF](https://www.lri.fr/~conchon/mpri/weber.pdf).
* There's an easy to use Python binding to the SAT solver
  [picosat](http://fmv.jku.at/picosat/), in the form of
  [pycosat](https://pypi.python.org/pypi/pycosat).

So what exactly is CNF, and what is a SAT solver? In short, CNF is a way of
writing a boolean formula:

$$A \wedge (B \vee (D \wedge E))$$

as series of *AND*s of *ORs*:

$$A \wedge (B \vee D) \wedge (B \vee E)$$

A SAT solver is a program which, given a boolean formula in CNF, assigns truth
values to the variables of the formula such that the formula is True. Each such
assignment is a solution to the boolean satisfiability problem. Above, \(A =
True, B = True, C = False, D = True\), is a solution, as is \(A = True, B =
False, D = True, E = True\), for example. \(A = False, B = True, C = True, D =
True\) is not a solution however.

SAT solving algorithms have been the subject of [intense competition](http://
www.satcompetition.org/) over the past decade due to applications in AI,
circuit design, and automatic theorem proving.  As such we can leverage these
advances just by expressing our problem as CNF.

## From puzzle to formula ##

So, we're looking to map our puzzle into a CNF expression, with the idea 

