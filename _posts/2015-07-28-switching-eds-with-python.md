---
layout: default
title: Switching Eds Face swapping with Python, dlib, and OpenCV
---

# Switching Eds: Face swapping with Python, dlib, and OpenCV

![Header](/assets/switching-eds/header.jpg)

## Introduction

In this post I'll describe how I wrote a short (200 line) Python script to
automatically replace facial features on an image of a face, with the facial
features from a second image of a face.

The process breaks down into four steps:

* Detecting facial landmarks.
* Rotating, scaling, and translating the second image to fit over the first.
* Adjusting the colour balance in the second image to match that of the first.
* Blending features from the second image on top of the first.

## 1. Using dlib to extract facial landmarks.

The script uses [dlib](http://dlib.net/)'s Python bindings to extract facial
landmarks:

![Landmarks](/assets/switching-eds/landmarks.jpg)

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

##2. Aligning faces with a procrustes analysis.

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

![Aligned faces](/assets/switching-eds/aligned-faces.jpg)

