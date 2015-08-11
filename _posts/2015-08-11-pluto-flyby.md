---
layout: default
title: Creating a Pluto flyby using unaligned New Horizons images
---
# Creating a Pluto flyby using unaligned New Horizons images

{% include img.html src="/assets/pluto-flyby/anim2.gif" alt="Header" %}

<sup>[Image credit](#image_credits)</sup>

## Introduction

Last month, a few days before NASA's [New Horizons](https://en.wikipedia.org/
wiki/New_Horizons) probe made its historic flyby of Pluto, I [posted a GIF of
it doing so to Reddit](https://www.reddit.com/r/space/
comments/3csabx/i_aligned_and_combined_the_new_horizons_lorri/).

To produce this GIF, I wrote a Python script to process unaligned JPEG images
directly from the [New Horizons jhuapl.edu LORRI
page](http://pluto.jhuapl.edu/soc/Pluto-Encounter/index.php). The script
translates and rotates input images such that background stars in the image
line up, which are then composed into a GIF. The result is a timelapse of New
Horizon's view, as if the camera were pointing in the direction of travel for
the duration.

Back when I made the original post the code was very much a prototype due to me
rushing to get the image out before the point of closest approach. I've since
cleaned up the code, and [put it on
GitHub](https://github.com/matthewearl/lorri-align). In this post I'll describe
how it works.

The process breaks down into these steps:

* Extracting star coordinates from the input images.
* Aligning images. This involves determining a transformation that will map
  the position of stars in the first image to the corresponding positions in
  all other images.
* Outputting images. This involves transforming all images into the reference
  frame of the first image, and writing the resulting image to disk. Input
  images that were taken at approximately the same time are combined into the
  same output image.

##

## Credits

<a id="image_credits" />
LORRI images courtesy of NASA/Johns Hopkins University Applied Physics
Laboratory/Southwest Research Institute.

