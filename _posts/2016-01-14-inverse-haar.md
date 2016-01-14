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

Mixed integer linear programming is a variant of [Integer programming](
[Mixed integer linear
programming](https://en.wikipedia.org/wiki/Integer_programming) is a variant of 

$$ f_i^T p >= t_i $$ 

Where \\( f_i \\) is a column vector representing feature \\( i \\), \\( t_i
\\) is the threshold associated with \\( f_i \\) and \\( p \\) is a column 
vector containing the pixel values in the image. \\( f_i \\) would contain 1s
for the white regions of the feature, and -1s for the black regions. All other
regions would be zero.


