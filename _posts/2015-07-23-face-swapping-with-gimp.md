---
layout: default
title: Face swapping with The GIMP
thumbimage: /assets/face-swap/thumb.jpg
excerpt:
  A methodical technique for face swapping in the GIMP. The approach replaces
  the face of a person in one image with the face of a person in another image. 
---

{% include post-title.html %}

{% include img.html src="/assets/face-swap/header.jpg" alt="Face swap Header" %}

<sup>[Image credit](#image_credits)</sup>

## Introduction

I've discovered a pretty quick and easy way to do face swaps such as the above
using [The GIMP](http://www.gimp.org/). Here's how:

## 1. Obtaining images

Obtain images of the subjects whose faces you wish to swap. For best results
the faces should be looking in the same direction, and be of reasonable
resolution:

{% include img.html src="/assets/face-swap/ed.jpg" alt="Ed" %}
{% include img.html src="/assets/face-swap/dave.jpg" alt="Dave" %}

<sup>[Image credit](#image_credits)</sup>

## 2. Aligning the images

Load both images into The GIMP and then decide which face you'd like to swap
onto which head. In my case I chose
[Ed](https://en.wikipedia.org/wiki/Ed_Miliband)'s face on
[Dave](https://en.wikipedia.org/wiki/David_Cameron)'s body.

Use the *Measure* tool (**Shift-M**) to measure the angle and distance between
each image's left and right eye, noting down as you go. You'll also need to
take note of whether The GIMP is measuring the angle above the horizontal axis
or below; record the angle as negative for above the line and positive
otherwise.

{% include img.html src="/assets/face-swap/eye-measure.jpg" alt="Eye measure" %}

<sup>[Image credit](#image_credits)</sup>

Break out a calculator and divide the head image's eye distance by the face
image's eye distance, and scale the face image by this factor:

{% include img.html src="/assets/face-swap/scale-image.jpg" alt="Scale image" %}

Now rotate the face image by the difference between the two eye-angles:

{% include img.html src="/assets/face-swap/rotate-image.jpg" alt="Rotate image" %}

<sup>[Image credit](#image_credits)</sup>

Copy the result, and paste it onto the head image as a new layer. Halve the new
layer's opacity and line up the two faces using the *Move* tool (**M**):

{% include img.html src="/assets/face-swap/align-image.jpg" alt="Align image" %}

<sup>[Image credit](#image_credits)</sup>

Return the top layer's opacity to 100%.

## 3. Adjust the colour balance of the face layer

Make a copy of both layers, with the face copy on top and the head copy just
below:

{% include img.html src="/assets/face-swap/layers.png" alt="layers" %}

<sup>[Image credit](#image_credits)</sup>

Now apply a gaussian blur to both. The blur amount should be as high as
you can get without non-flesh tones from hair or background interfering with
areas you want to transfer to the head image. About 2/3 of the head image
eye-distance has worked well for me:

{% include img.html src="/assets/face-swap/face-blur.jpg" alt="Face blur" %}

<sup>[Image credit](#image_credits)</sup>

{% include img.html src="/assets/face-swap/head-blur.jpg" alt="Head blur" %}

<sup>[Image credit](#image_credits)</sup>

Now set the blurred face layer to divide, and the blurred head layer to
multiply. The face image should now be shining through, but with the right
lighting and fleshtones around the facial area:

{% include img.html src="/assets/face-swap/colour-adjusted-face-image.jpg" alt="Colour adjusted face image" %}

<sup>[Image credit](#image_credits)</sup>

At this point select *Copy Visible* from the *Edit* menu, and paste as a new
layer.Move the new layer to second from bottom (right above the bottom head
layer), and make all layers above it invisible.

## 4. Select facial features with a Layer Mask

Add a layer mask to the newly pasted, colour-corrected face layer. Initialise
it to black (fully transparent). Now with the *Brush* tool draw over the eye,
nose and mouth area in white (opaque):

{% include img.html src="/assets/face-swap/pre-blurred-mask.jpg" alt="Pre-blurred mask" %}

<sup>[Image credit](#image_credits)</sup>

Apply a gaussian blur to the layer mask, *et voila*:

{% include img.html src="/assets/face-swap/camerband.jpg" alt="Camerband" %}

<sup>[Image credit](#image_credits)</sup>

## Addendum

By swapping layers and re-doing the *Copy Visible* layer from step 3 one can
easily get the reverse image:

{% include img.html src="/assets/face-swap/milliron.jpg" alt="Milliron" %}

<sup>[Image credit](#image_credits)</sup>

## Credits

<a id="image_credits" />
[Original Ed Miliband image](https://commons.wikimedia.org/
wiki/File:Ed_Miliband.jpg) by the Department of Energy, licensed under the 
[Open Government License v1.0](https://www.nationalarchives.gov.uk/doc/
open-government-licence/version/1/).

[Original David Cameron image](https://commons.wikimedia.org/wiki/
File:Davidcameron.jpg) by [Land of Hope and Glory](https://en.wikipedia.org/
wiki/User:Land_of_Hope_and_Glory), released into the public domain.

