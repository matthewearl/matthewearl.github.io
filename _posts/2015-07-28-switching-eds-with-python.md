---
layout: default
title: Switching Eds&#58; Face swapping with Python, dlib, and OpenCV
reddit-url: https://www.reddit.com/r/programming/comments/3f591x/so_i_wrote_a_script_that_swaps_peoples_faces_in/
thumbimage: /assets/switching-eds/thumb.jpg
summary:
  Automating the algorithm from the previous post. Facial landmarks are
  detected using dlib. Alignment, colour correction, and blending is then done
  with numpy and OpenCV.
---

{% include post-title.html %}
 
{% include img.html src="/assets/switching-eds/header.jpg" alt="Header" %}

<sup>[Image credit](#image_credits)</sup>

## Introduction

In this post I'll describe how I wrote a short (200 line) Python script to
automatically replace facial features on an image of a face, with the facial
features from a second image of a face.

The process breaks down into four steps:

* Detecting facial landmarks.
* Rotating, scaling, and translating the second image to fit over the first.
* Adjusting the colour balance in the second image to match that of the first.
* Blending features from the second image on top of the first.

The full source-code for the script can be [found here](https://github.com/
matthewearl/faceswap/blob/master/faceswap.py).

## 1. Using dlib to extract facial landmarks

The script uses [dlib](http://dlib.net/)'s Python bindings to extract facial
landmarks:

{% include img.html src="/assets/switching-eds/landmarks.jpg" alt="Landmarks" %}

<sup>[Image credit](#image_credits)</sup>

Dlib implements the algorithm described in the paper [One Millisecond Face
Alignment with an Ensemble of Regression Trees](
http://www.csc.kth.se/~vahidk/papers/KazemiCVPR14.pdf), by Vahid Kazemi and
Josephine Sullivan. The algorithm itself is very complex, but dlib's interface
for using it is incredibly simple:

{% highlight python %}
PREDICTOR_PATH = "/home/matt/dlib-18.16/shape_predictor_68_face_landmarks.dat"

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_PATH)

def get_landmarks(im):
    rects = detector(im, 1)
    
    if len(rects) > 1:
        raise TooManyFaces
    if len(rects) == 0:
        raise NoFaces

    return numpy.matrix([[p.x, p.y] for p in predictor(im, rects[0]).parts()])
{% endhighlight %}

The function `get_landmarks()` takes an image in the form of a numpy array, and
returns a 68x2 element matrix, each row of which corresponding with the
x, y coordinates of a particular feature point in the input image.

The feature extractor (`predictor`) requires a rough bounding box as input to
the algorithm. This is provided by a traditional face detector (`detector`)
which returns a list of rectangles, each of which corresponding with a face in
the image.

To make the predictor a pre-trained model is required. Such a model can be
[downloaded from the dlib sourceforge repository](http://sourceforge.net/
projects/dclib/files/dlib/v18.10/shape_predictor_68_face_landmarks.dat.bz2).

##2. Aligning faces with a procrustes analysis

So at this point we have our two landmark matrices, each row having coordinates
to a particular facial feature (eg. the 30th row gives the coordinates of the
tip of the nose). We're now going to work out how to rotate, translate, and
scale the points of the first vector such that they fit as closely as possible
to the points in the second vector, the idea being that the same transformation
can be used to overlay the second image over the first.

To put it more mathematically, we seek \\( T \\), \\( s \\), and \\( R \\) such
that:

$$\sum_{i=1}^{68}||s R p_i^T + T - q_i^T||^{2}$$

is minimized, where \\( R \\) is an orthogonal 2x2 matrix, \\( s \\) is a
scalar, \\( T \\) is a 2-vector, and \\( p_i \\) and \\( q_i \\) are the rows
of the landmark matrices calculated above.

It turns out that this sort of problem can be solved with an
[Ordinary Procrustes Analysis](https://en.wikipedia.org/wiki/
Procrustes_analysis#Ordinary_Procrustes_analysis):

{% highlight python %}
def transformation_from_points(points1, points2):
    points1 = points1.astype(numpy.float64)
    points2 = points2.astype(numpy.float64)

    c1 = numpy.mean(points1, axis=0)
    c2 = numpy.mean(points2, axis=0)
    points1 -= c1
    points2 -= c2

    s1 = numpy.std(points1)
    s2 = numpy.std(points2)
    points1 /= s1
    points2 /= s2

    U, S, Vt = numpy.linalg.svd(points1.T * points2)
    R = (U * Vt).T

    return numpy.vstack([numpy.hstack(((s2 / s1) * R,
                                       c2.T - (s2 / s1) * R * c1.T)),
                         numpy.matrix([0., 0., 1.])])
{% endhighlight %}

Stepping through the code:

1. Convert the input matrices into floats. This is required for the operations
   that are to follow.
2. Subtract the centroid form each of the point sets. Once an optimal scaling
   and rotation has been found for the resulting point sets, the centroids `c1`
   and `c2` can be used to find the full solution.
3. Similarly, divide each point set by its standard deviation. This removes the
   scaling component of the problem.
4. Calculate the rotation portion using the [Singular Value
   Decomposition](https://en.wikipedia.org/wiki/Singular_value_decomposition).
   See the wikipedia article on the [Orthogonal Procrustes Problem](
   https://en.wikipedia.org/wiki/Orthogonal_Procrustes_problem) for details of
   how this works.
5. Return the complete transformaton as an [affine transformation matrix](
   https://en.wikipedia.org/wiki/Transformation_matrix#Affine_transformations).

The result can then be plugged into OpenCV's `cv2.warpAffine` function to map
the second image onto the first:

{% highlight python %}
def warp_im(im, M, dshape):
    output_im = numpy.zeros(dshape, dtype=im.dtype)
    cv2.warpAffine(im,
                   M[:2],
                   (dshape[1], dshape[0]),
                   dst=output_im,
                   borderMode=cv2.BORDER_TRANSPARENT,
                   flags=cv2.WARP_INVERSE_MAP)
    return output_im
{% endhighlight %}

Which produces the following alignment:

{% include img.html src="/assets/switching-eds/aligned-faces.gif" alt="Aligned faces" %}

<sup>[Image credit](#image_credits)</sup>

## 3. Colour correcting the second image

If we tried to overlay facial features at this point, we'd soon see we have a
problem:

{% include img.html src="/assets/switching-eds/non-colour-corrected-overlay.jpg" alt="Non colour-corrected overlay" %}

<sup>[Image credit](#image_credits)</sup>

The issue is that differences in skin-tone and lighting between the two images
is causing a discontinuity around the edges of the overlaid region. Let's try
to correct that:

{% highlight python %}
COLOUR_CORRECT_BLUR_FRAC = 0.6
LEFT_EYE_POINTS = list(range(42, 48))
RIGHT_EYE_POINTS = list(range(36, 42))

def correct_colours(im1, im2, landmarks1):
    blur_amount = COLOUR_CORRECT_BLUR_FRAC * numpy.linalg.norm(
                              numpy.mean(landmarks1[LEFT_EYE_POINTS], axis=0) -
                              numpy.mean(landmarks1[RIGHT_EYE_POINTS], axis=0))
    blur_amount = int(blur_amount)
    if blur_amount % 2 == 0:
        blur_amount += 1
    im1_blur = cv2.GaussianBlur(im1, (blur_amount, blur_amount), 0)
    im2_blur = cv2.GaussianBlur(im2, (blur_amount, blur_amount), 0)

    # Avoid divide-by-zero errors.
    im2_blur += 128 * (im2_blur <= 1.0)

    return (im2.astype(numpy.float64) * im1_blur.astype(numpy.float64) /
                                                im2_blur.astype(numpy.float64))
{% endhighlight %}

And the result:

{% include img.html src="/assets/switching-eds/colour-corrected.jpg" alt="Colour corrected" %}

<sup>[Image credit](#image_credits)</sup>

This function attempts to change the colouring of `im2` to match that of `im1`.
It does this by dividing `im2` by a gaussian blur of `im2`, and then
multiplying by a gaussian blur of `im1`. The idea here is that of a [RGB
scaling
colour-correction](https://en.wikipedia.org/wiki/Color_balance#
Scaling_monitor_R.2C_G.2C_and_B), but instead of a constant scale factor across
all of the image, each pixel has its own localised scale factor.

With this approach differences in lighting between the two images can be
accounted for, to some degree. For example, if image 1 is lit from one side
but image 2 has uniform lighting then the colour corrected image 2 will 
appear darker on the unlit side aswell.

That said, this is a fairly crude solution to the problem and an appropriate
size gaussian kernel is key. Too small and facial features from the first
image will show up in the second. Too large and kernel strays outside of the
face area for pixels being overlaid, and discolouration occurs. Here a kernel
of 0.6 * the pupillary distance is used.

## 4. Blending features from the second image onto the first

A mask is used to select which parts of image 2 and which parts of image 1
should be shown in the final image:

{% include img.html src="/assets/switching-eds/mask.png" alt="Mask" %}

Regions with value 1 (shown white here) correspond with areas where image 2
should show, and regions with colour 0 (shown black here) correspond with areas
where image 1 should show. Value in between 0 and 1 correspond with a mixture
of image 1 and image2.

Here's the code to generate the above:

{% highlight python %}
LEFT_EYE_POINTS = list(range(42, 48))
RIGHT_EYE_POINTS = list(range(36, 42))
LEFT_BROW_POINTS = list(range(22, 27))
RIGHT_BROW_POINTS = list(range(17, 22))
NOSE_POINTS = list(range(27, 35))
MOUTH_POINTS = list(range(48, 61))
OVERLAY_POINTS = [
    LEFT_EYE_POINTS + RIGHT_EYE_POINTS + LEFT_BROW_POINTS + RIGHT_BROW_POINTS,
    NOSE_POINTS + MOUTH_POINTS,
]
FEATHER_AMOUNT = 11

def draw_convex_hull(im, points, color):
    points = cv2.convexHull(points)
    cv2.fillConvexPoly(im, points, color=color)

def get_face_mask(im, landmarks):
    im = numpy.zeros(im.shape[:2], dtype=numpy.float64)

    for group in OVERLAY_POINTS:
        draw_convex_hull(im,
                         landmarks[group],
                         color=1)

    im = numpy.array([im, im, im]).transpose((1, 2, 0))

    im = (cv2.GaussianBlur(im, (FEATHER_AMOUNT, FEATHER_AMOUNT), 0) > 0) * 1.0
    im = cv2.GaussianBlur(im, (FEATHER_AMOUNT, FEATHER_AMOUNT), 0)

    return im

mask = get_face_mask(im2, landmarks2)
warped_mask = warp_im(mask, M, im1.shape)
combined_mask = numpy.max([get_face_mask(im1, landmarks1), warped_mask],
                          axis=0)
{% endhighlight %}

Let's break this down:

* A routine `get_face_mask()` is defined to generate a mask for an image and a
  landmark matrix. It draws two convex polygons in white: One surrounding the
  eye area, and one surrounding the nose and mouth area. It then feathers the
  edge of the mask outwards by 11 pixels. The feathering helps hide any
  remaning discontinuities.
* Such a face mask is generated for both images. The mask for the second is
  transformed into image 1's coordinate space, using the same transformation as
  in step 2.
* The masks are then combined into one by taking an element-wise maximum.
  Combining both masks ensures that the features from image 1 are covered up,
  and that the features from image 2 show through.

Finally, the mask is applied to give the final image:

{% highlight python %}
output_im = im1 * (1.0 - combined_mask) + warped_corrected_im2 * combined_mask
{% endhighlight %}

{% include img.html src="/assets/switching-eds/final.jpg" alt="Final" %}

<sup>[Image credit](#image_credits)</sup>

## Credits

<a id="image_credits" />
[Original Ed Miliband image](https://commons.wikimedia.org/
wiki/File:Ed_Miliband.jpg) by the Department of Energy, licensed under the 
[Open Government License v1.0](https://www.nationalarchives.gov.uk/doc/
open-government-licence/version/1/).

[Original Eddie Van Halen image](https://
commons.wikimedia.org/wiki/File:Eddie_Van_Halen_(1993).jpg) by Alan Light,
licensed under the [Creative Commons Attribution 2.0 Generic license](https://
creativecommons.org/licenses/by/2.0/deed.en)
