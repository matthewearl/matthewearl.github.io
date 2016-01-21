---
layout: default
title: 12 years in 12 seconds&#58;
    Aligning and condensing a self-portrait time-lapse
noindex: 1
---

{% include post-title.html %}

<!-- Add video here -->

<sup>Based on [this video](https://www.youtube.com/watch?v=iPPzXlMdi7o) 
by [Noah Kalina](http://www.noahkalina.com/). Used with permission.</sup>

## Introduction

Following from [my previous experiments](/2015/07/28/
switching-eds-with-python/) with face alignment, I got to thinking if the same
techniques could be applied to photo-a-day time lapse projects, such as Noah
Kalina's [12.5 year (and counting) epic](https://www.youtube.com/
watch?v=iPPzXlMdi7o).

The idea is to account for incidental variances to acheive a smooth, yet
extremely fast-forwarded view of the subject. Specifically, the variances being
eliminated are:

* *Face position*: The orientation of the face within the frame.
* *Lighting*: Differences in illumination colour and/or white balance.
* *Pose*: Differences in facial pose, and lighting direction.

As usual, I'm attacking this problem in Python. I'm using
[dlib](http://dlib.net/), [OpenCV](http://opencv.org/) and
[numpy](http://www.numpy.org/) to do the heavy lifting. Source code
[is available here](https://github.com/matthewearl/photo-a-day-aligner).

## Aligning and Color Correction


