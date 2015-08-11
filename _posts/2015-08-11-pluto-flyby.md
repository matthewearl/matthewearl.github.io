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

I won't cover how to obtain the input images from the JHUAPL website as this is
not very interesting (although it is included in [the source code](https://
github.com/matthewearl/lorri-align)).

## Extracting star coordinates

Looking at one of the input images we wish to compose, it doesn't appear at
first as if there are any background stars at all:

{% include img.html src="/assets/pluto-flyby/input.jpg" alt="Input" %}

<sup>[Image credit](#image_credits)</sup>

However, stretch the brightness 16 times and a few become visible:

{% include img.html src="/assets/pluto-flyby/input-bright.jpg" alt="Input Bright" %}

Given such an input image we wish to obtain the `x`, `y` coordinates of each
star.  To do so we first
[threshold](https://en.wikipedia.org/wiki/Thresholding_(image_processing)) the
input image:

{% highlight python %}
THRESHOLD_FRACTION = 0.025
THRESHOLD_BIAS = 2
def extract(im):
    hist = numpy.histogram(im, bins=range(256))[0]
    for thr in range(256):
        if sum(hist[thr + 1:]) < (im.shape[0] * im.shape[1] *
                                  THRESHOLD_FRACTION):
            break
    else:
        raise ExtractFailed("Image too bright")
    thr += THRESHOLD_BIAS
    _, thresh_im = cv2.threshold(im, thr, 255, cv2.THRESH_BINARY)
{% endhighlight %}

This code picks the smallest thresholding constanting `thr` such that less than
2.5% of the thresholded image is white, then adds 2 to it. The resulting image
is:

{% include img.html src="/assets/pluto-flyby/thresholded.png" alt="Thresholded" %}

<sup>[Image credit](#image_credits)</sup>

The idea is to make a mask such that contiguous white regions in the
thresholded image correspond with stars in the original image. The value of
`THRESHOLD_FRACTION` was chosen on the basis that 97% or more of an image is
just background blackness, which is strictly darker the stars we wish to
detect, so thresholding on this will remove almost all of the background
pixels. Due to sensor noise there are still some background pixels which get
through at this level. `THRESHOLD_BIAS` is chosen to account for this.

The above isn't perfect: Some stars have multiple contiguous regions associated
with them. We account for this by [dilating](https://en.wikipedia.org/wiki/
Dilation_(morphology)) the mask by a small amount, thereby joining up nearby
regions:

{% highlight python %}
    DILATION_SIZE = 9
    ...
    thresh_im = cv2.dilate(thresh_im, numpy.ones((DILATION_SIZE,
                                                  DILATION_SIZE)))
{% endhighlight %}

This gives the following:

{% include img.html src="/assets/pluto-flyby/dilated.png" alt="Dilated" %}

<sup>[Image credit](#image_credits)</sup>

At this point we assume each contiguous region is a star. We start by using
`cv2.findContours` to extract contiguous regions:

{% highlight python %}
    contours, _ = cv2.findContours(thresh_im, mode=cv2.RETR_EXTERNAL,
                                   method=cv2.CHAIN_APPROX_NONE)
    contours = [c for c in contours if len(c) > 1]
    if len(contours) > MAX_STARS:
        raise ExtractFailed("Too many stars ({})".format(len(contours)))
    if len(contours) < MIN_STARS:
        raise ExtractFailed("Not enough stars ({})".format(len(contours)))
{% endhighlight %}

And then masking the original image by each contiguous region, and using
`cv2.moments` to determine the centre-of-mass of the star, in terms of pixel
coordinates:

{% highlight python %}
    for idx, contour in enumerate(contours):
        x, y, w, h = cv2.boundingRect(contour)
        sub_im_mask = numpy.zeros((h, w), dtype=numpy.uint8)
        cv2.drawContours(sub_im_mask,
                         contours,
                         idx,
                         color=1,
                         thickness=-1,
                         offset=(-x, -y))
        sub_im = im[y:y + h, x:x + w] * sub_im_mask
        m = cv2.moments(sub_im)

        yield Star(x=(x + m['m10'] / m['m00']), y=(y + m['m01'] / m['m00']))
{% endhighlight %}

Here's the resuls, plotted over the stretched input image:

{% include img.html src="/assets/pluto-flyby/stars.jpg" alt="Stars" %}

<sup>[Image credit](#image_credits)</sup>

## Credits

<a id="image_credits" />
LORRI images courtesy of NASA/Johns Hopkins University Applied Physics
Laboratory/Southwest Research Institute.

