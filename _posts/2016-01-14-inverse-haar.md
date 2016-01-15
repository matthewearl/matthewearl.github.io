---
layout: default
title: Making faces with Haar cascades and mixed integer linear programming
noindex: 1
---

{% include post-title.html %}

## Introduction

I've previously mentioned face detection in my [Face swapping
post](/2015/07/28/switching-eds-with-python/). The face detection step there
uses the popular "cascade of Haar-like features" algorithm to get initial
bounds for faces in an image.

In this post I discuss my attempts to invert this face detection algorihm:
Instead of taking an image and telling you whether it contains a face, it will
generate an image of a face, using nothing more than cascade data.

## Haar Cascades

In 2001 Viola and Jones introduced their revolutionary [object detection
algorithm based on cascades of Haar-like
features](https://en.wikipedia.org/wiki/
Viola%E2%80%93Jones_object_detection_framework), enabling for the first time
real-time detection of faces (and other objects) in video data.

At its core, the algorithm accepts a small (typically 20x20) image along with
some cascade data, and returns whether or not the object of interest is present
there.  The full algorithm simply applies this core algorithm to the full
image in multiple windows, with the windows at various scales and positions,
returning any where the core algorithm detected the object.

It is this core algorithm that I'm attempting to invert in this post. But how
does it work? Well, it's based on so called Haar-like features:

@@@Insert pic

Each feature is associated with a threshold to form a so-called *weak
classifer*.  If the sum of the pixel values in the black region subtracted 
from the sum of the pixel values in the white region exceed the threshold then
the weak classifier is said to have passed. In this case the weak classifer is
detecting a dark area around the eyes, compared to above the cheeks.

Weak classifiers are combined into *stages*. A stage passes based on which
weak classifiers associated with the stage pass; each weak classifier has a
weight associated with it, and if the sum of all the passing weak classifiers'
weights exceeds a *stage threshold* then the stage is said to have passed.

If all the stages in the cascade data pass then the algorithm returns that an
object has been detected.

This can be written in Python like:

{% highlight python %}
def detect(cascade, im):
    for stage in cascade.stages:
        total = 0
        for classifier in stage.weak_classifiers:
            if numpy.sum(classifier.feature * im) >= classifier.threshold:
                total += classifier.weight
        if total < stage.threshold:
            return False
    return True 
{% endhighlight %}

The input image `im` is assumed to already have been resized to the small
cascade size.  `classifier.feature` is an array the same shape as `im`, with
`1`s at points corresponding with white areas of the feature, `-1`s at points
corresponding with black areas of the feature, and `0`s elsewhere.  Note the
actual algorithm as described by Viola and Jones uses integral images at this
point (one of the main reasons for the algorithms fast operation).

The main reason for the multiple stages is efficiency: Typically the first
stage will contain only a handful of features, but can reject a large
proportion of negative images. There are typically hundreds of features in a
particular cascade, and a dozen or more stages.

## Mixed integer linear programming

In order to invert the `detect` function described above, I express the forward
problem in terms of [Mixed integer linear programming](https://
en.wikipedia.org/wiki/Integer_programming), and then apply a MILP solver to the
linear program.

Here's the `detect` function described in terms of MILP constraints. First the
constraints to ensure a weak classifer passes, if it is required to. Lets call
these *feature constraints*:

$$ \forall j \in {positive\_classifiers} \ \colon \ \Bigg(
M_{j} (1 - {passed}_j)\ + \sum_{i=0}^{N_{pixels} - 1} {pixel}_i {feature}_{j,i}
                                                   \geq threshold_{j} \Bigg) $$

$$ \forall j \in {negative\_classifiers} \ \colon \ \Bigg(
   -M_{j} {passed}_j\ + \sum_{i=0}^{N_{pixels} - 1} {pixel}_i {feature}_{j,i} 
                                                      < threshold_{j} \Bigg) $$

...and a set of constraints to ensure that each stage passes. Let's call these
*stage constraints*:

$$ \forall k \in [0, {N_{stages}} - 1] \ \colon \ \Bigg(
        \sum_{j \in {classifiers}_k}  {passed}_j * {weight}_j \geq
                                                   stage\_threshold_k \Bigg) $$

Where:

* $$ {pixel}_i \in [0, 1], 0 \leq i < N_{pixels} $$ are the pixel values of the
  input image. (Corresponds with `im` in the code.)
* $$ {feature}_{j,i} \in \mathbb{R}, 0 \leq j < N_{classifiers},
  0 \leq i < N_{pixels} $$ are the weight values of the feature associated with
  weak classifier $$ j $$.  (Corresponds with `classifier.feature` in the
  code.)
* $$ {threshold}_j $$ is the threshold value of weak classifier $$ j $$.
  (`classifier.threshold` in the code.)
* $$ {weight}_j $$ is the weight of weak classifier $$ j $$. (Corresponds
  with `classifier.weight` in the code.)
* $$ {positive\_classifiers} $$ is the set of classifier indices with
  positive weights, ie. $$ \{ j \in [0, N_{classifiers} - 1] : {weight}_j > 0
  \} $$
* $$ {negative\_classifiers} $$ is the set of classifier indices with
  negative weights, ie. $$ \{ j \in [0, N_{classifiers} - 1] : {weight}_j < 0
  \} $$.
* $$ {passed}_j \in \{0, 1\} $$ is a binary indicator variable, corresponding
  with whether weak classifier $$ j $$ has passed.
* $$ M_{j} $$ are numbers chosen to be large enough such that if the term they
  appear in is non-zero, then the inequality holds true.
* $$ classifiers\_k $$ is the set of weak classifier indices associated with
  stage $$ k $$.
* $$ stage\_threshold_k $$ is the stage threshold of stage $$ k $$.
  (Corresponds with `stage.threshold` in the code.)

The variables to be sought by the MILP solver are the $$ {pixel}_i $$ and
$$ {passed}_j $$ values. The rest of the values are derived from the cascade
definition itself.

The main thing to note is the use of $$ {passed}_j $$ as an indicator variable,
ie. how it's state can turn on or off one of the feature constraints.  For
example, take $$ j \in {positive\_classifiers} $$. If a particular solution
$$ {passed}_j $$ as 1, then we better be sure that the feature $$ j $$ actually
exceeds the classifier's threshold, as it is contributing positively towards
the stage passing.

Conversely, for a classifier $$ j $$ with a negative weight, we only care that
the feature *doesn't* pass its classifier threshold if $$ {passed}_j $$ is 0.

With this in mind, it's clear that `detect(cascade, im)` is True if and only if
there's a solution to the linear program derived from `cascade` where the $$
{pixel}_j $$ variables take on the corresponding pixel values in `im`.

## MILPs in Python

I chose to use the [docplex](https://pypi.python.org/pypi/
docplex?cm_mc_uid=67935383877914501094737&cm_mc_sid_50200000=1452877037) module
to write the above constraints in Python. With this module constraints can be
written in the "natural" way, which are then dispatched to [IBM's DoCloud
Service](https://developer.ibm.com/docloud/) for solving offline. Note DoCloud
requires registration and is not free, although they offer a free month's
trial which is what I used for this project.

For what it's worth I did initially try solving the problem with the
[PuLP](https://pypi.python.org/pypi/PuLP) module, with which I had limited
success either due to the underlying solver being less sophisticated, or
limitations of my machine.

As an example, here's how the variables are defined:

{% highlight python %}

from docplex.mp.model import Model

model = Model("Inverse haar cascade", docloud_context=docloud_context)

pixel_vars = {(x, y): model.continuous_var(
                name="pixel_{}_{}".format(x, y)
                lb=0., ub=1.0)
                for y in range(cascade.height)
                for x in range(cascade.width)}
passed_vars = [self.binary_var(name="passed_{}".format(idx))
                                       for idx in range(len(cascade.features))]
{% endhighlight %}

And an (abridged) snippet which adds the stage constraint:

{% highlight python %}
for stage in cascade.stages:
    model.add_constraint(sum(c.weight * passed_vars[c.feature_idx]
                                        for c in stage.weak_classifiers) >=
                                                               stage.threshold)
{% endhighlight %}

The problem is then solved by calling `model.solve()`.

If succesful, the pixel variable values are extracted from the solution, and
converted into an image (a `numpy` array):

{% highlight python %}
im = numpy.array([[pixel_vars[x, y].solution_value
                    for x in range(cascade.width)]
                  for y in range(cascade.width)])
{% endhighlight %}

See the [source code](https://github.com/matthewearl/inversehaar) for the full
details.

## Results

@@@ Add results here
