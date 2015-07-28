---
layout: default
title: Switching Eds: Face swapping with Python, dlib, and OpenCV
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

Dlib implements the algorithm described in the paper (One Millisecond Face
Alignment with an Ensemble of Regression Trees)
[http://www.csc.kth.se/~vahidk/papers/KazemiCVPR14.pdf], by Vahid Kazemi and
Josephine Sullivan. The algorithm itself is very complex, but dlib's interface
for using it is incredibly simple:

{% highlight python %}
PREDICTOR_PATH = "/home/matt/dlib-18.16/shape_predictor_68_face_landmarks.dat"

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_PATH)

class TooManyFaces(Exception):
    pass

class NoFaces(Exception):
    pass

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


