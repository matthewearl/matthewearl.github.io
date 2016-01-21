---
layout: default
title: 12 years in 12 seconds&#58;
    Aligning and condensing a self-portrait time-lapse
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

## Aligning

As a first step, lets account for facial position by rotating, translating and
scaling images to match the first:

{% highlight python %}
ref_landmarks = None
for fname in input_fnames:
    im = cv2.imread(fname)

    # Compute landmark features for the face in the image.
    try:
        landmarks = get_landmarks(im)
    except NoFaces:
        print "Warning: No faces in image {}".format(fname)
        continue
    except TooManyFaces:
        print "Warning: Too many faces in image {}".format(fname)
        continue

    # If this is the first image, make it the reference.
    if ref_landmarks is None:  
        ref_landmarks = landmarks

    # Compute the transformation required to map the facial landmarks of the
    # current image onto the reference landmarks.
    M = orthogonal_procrustes(ref_landmarks, landmarks)

    # Translate/rotate/scale the image to fit over the reference image.
    warped = warp_im(im, M, im.shape)

    # Write the file to disk.
    cv2.imwrite(os.path.join(OUT_PATH, fname), warped)
{% endhighlight %}

The `get_landmarks()` function uses `dlib` to use facial landmark features:

{% include img.html src="/assets/portrait-timelapse/annotated.jpg" alt="Annotated image" %}

...and `orthogonal_procrustes()` generates a transformation matrix which maps
one set of landmarks features onto another.  This transformation is used by
`warp_im()` to translate, rotate and scale images to line up with the first
image.  For more details refer to my [Switching Eds post](/2015/07/28/
switching-eds-with-python/) which uses an identical approach in steps 1 and 2
to align the images.

After correcting for face position, you get a video that looks like this:

<!-- insert 5s video of just correcting for face position -->

# Colour adjustment

There are still a few obvious discontinuities. One variance we can easily iron out is the
overall change in colour on the face due to different lighting and/or white
balance settings.

The correction works by computing a mask for each image:

{% highlight python %}
mask = numpy.zeros(im.shape[:2], dtype=numpy.float64)
cv2.fillConvexPoly(mask, cv2.convexHull(points), color=color)
{% endhighlight %}

{% include img.html src="/assets/portrait-timelapse/mask.png" alt="Mask" %}

...based on the [convex hull](https://en.wikipedia.org/wiki/Convex_hull) of the
landmark points. This is then multiplied by the image itself:

{% highlight python %}
masked_im = mask[:, :, numpy.newaxis] * im
{% endhighlight %}

{% include img.html src="/assets/portrait-timelapse/masked.png" alt="Masked image" %}

The sum of the pixels in the masked image is then divided by the sum of the
values in the mask, to give an average colour for the face:

{% highlight python %}
color = ((numpy.sum(masked_im, axis=(0, 1)) /
          numpy.sum(mask, axis=(0, 1))))
{% endhighlight %}

Images' RGB values are then scaled such that their average face colour matches
that of the average face colour of the first image:

{% highlight python %}
im = im * ref_color / color
{% endhighlight %}

Here's the first 5 seconds with color correction applied:

<!-- insert 5s video of correcting for position and colour -->

