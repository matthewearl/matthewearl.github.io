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
github.com/matthewearl/lorri-align)). Note for this project only the
short-exposure 100-150 msec images are used.

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

And then mask the original image by each contiguous region, using `cv2.moments`
to determine the centre-of-mass of the star, in terms of pixel coordinates:

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

## Aligning images

In this step, for each input image we seek to find an affine transformation
\\( M \\) which maps points on the first image to corresponding points on the
image in question. Given a function `register_pair` which takes stars from
two images and returns a transformation to map the first image on to the
second it is easy enough to write an algorithm that behaves well:

{% highlight python %}
REGISTRATION_RETRIES = 3

def register_many(stars_seq):
    stars_it = iter(stars_seq)

    registered = [(next(stars_it), numpy.matrix(numpy.identity(3)))]
    yield RegistrationResult(exception=None, transform=registered[0][1])

    for stars2 in stars_it:
        for stars1, M1 in [registered[0]] + registered[-REGISTRATION_RETRIES:]:
            try:
                M2 = register_pair(stars1, stars2)
            except RegistrationFailed as e:
                yield RegistrationResult(exception=e, transform=None)
            yield RegistrationResult(exception=None, transform=(M1 * M2))
        registered.append((stars2, (M1 * M2)))
{% endhighlight %}

What this does is to attempt to align each image directly with the first image.
If this succeeds the transformation is simply the one returned by
`register_pair`. Otherwise, the image is aligned with the third to last
successfully registered image, then the second to last, and so on. If one of
these succeeds the desired transformation is just the previously registered
image's transformation composed with that of transformation just returned by
`register_pair`.

This technique works quite well: The majority of images line up with the first
image directly, but if they don't (typically because they have a small set of
detected stars) then they are lined up with the images that they are most
similar to. Preferring to pair with the first image is desirable as it prevents
alignment errors accumulating.

## Aligning pairs of images

This is all well and good, but how does `register_pair()` work? Well, it starts
by selecting a random pair of stars from each image:

{% include img.html src="/assets/pluto-flyby/pair-align1.jpg" alt="Pair align 1" %}

<sup>[Image credit](#image_credits)</sup>

These are hypothetical corresponding stars. If later in the procedure they are
found not to be the same star, they procedure will restart, but for now they
are assumed to be the same star.

Next, random remaining (labelled red) pairs are picked until two are found
which have approximately the same (with 4 pixels) distance from the first star:

{% include img.html src="/assets/pluto-flyby/pair-align2.jpg" alt="Pair align 2" %}

<sup>[Image credit](#image_credits)</sup>

...if no such pairs are found the procedure restarts with a new initial pair.
Otherwise a third pair is sought, which must have the same distance to the
previously paired stars. This procedure repeats until 4 stars have been
successfully paired:

{% include img.html src="/assets/pluto-flyby/pair-align3.jpg" alt="Pair align 3" %}

<sup>[Image credit](#image_credits)</sup>

{% include img.html src="/assets/pluto-flyby/pair-align4.jpg" alt="Pair align 4" %}

<sup>[Image credit](#image_credits)</sup>

The procedure repeats a maximum of 500 times, after which the registration
fails.

This algorithm is similar to the [RANSAC](https://en.wikipedia.org/wiki/RANSAC)
algorithm, except with slightly more efficient behaviour. From the Wikipedia
page:

> Random sample consensus (RANSAC) is an iterative method to estimate
> parameters of a mathematical model from a set of observed data which contains
> outliers.

In our case the *parameters of the mathematical model* are the translation and
rotation required to map the first image onto the second. The *observed data*
are all possible pairs of stars in the first image and stars in the second
image, ie. (number of stars in image 1) * (number of stars in image 2) such
pairs.

Pure RANSAC would proceed by randomly selecting a minimal set of data points in
order to give a hypothetical model. In our case this would be 2 pairs: Enough
to give a translation and a rotation. The 2 pairings would be immediately
rejected and the process restarted if the distance between the two points in
the first image differed from the distance in the two points in the second
image. If the distances are the same, a model is constructed (in our case a
rotation and a translation), and the remaining data are inspected to see how
many fit the model. The model is accepted if the count reaches a predetermined
value.

Assuming there are \\( N \\) stars in each image, then RANSAC would
complete \\( N * (N - 1) \\) iterations before finding a match. On average
\\( N - 1 \\) of these iterations would pass the initial distance test, and
thus require \\( N - 2 \\) * \\( N - 2 \\) 


## Credits

<a id="image_credits" />
LORRI images courtesy of NASA/Johns Hopkins University Applied Physics
Laboratory/Southwest Research Institute.

