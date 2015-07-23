---
layout: default
title: Face swapping with The Gimp
---

# Face Swapping with The GIMP

![Face swap Header](/assets/face-swap/header.jpg)

## Introduction

I've discovered a pretty quick and easy way to do face swaps such as the above,
using [The GIMP](http://www.gimp.org/). Here's how:

## 1. Obtaining images.

Obtain images of the subjects whose faces you wish to swap. For best results
the faces should be looking in the same direction, and be of reasonable
resolution:

![Ed](/assets/face-swap/ed.jpg)
![Dave](/assets/face-swap/dave.jpg)

## 2. Aligning the images

Load both images into The GIMP and then decide which face you'd like to swap
onto which head. In my case I chose
[Ed](https://en.wikipedia.org/wiki/Ed_Miliband)'s face on
[Dave](https://en.wikipedia.org/wiki/David_Cameron)'s body.

Use the measure tool (**Shift-M**) to measure the angle and distance between
each image's left and right eye, noting down as you go. You'll also need to
take note of whether The GIMP is measuring the angle above the horizontal axis
or below; record the angle as negative for above the line and positive
otherwise.

![Eye measure](/assets/face-swap/eye-measure.jpg)

Break out a calculator and divide the head image's eye distance by the face
image's eye distance, and scale the face image by this factor:

![Scale image](/assets/face-swap/scale-image.jpg)

Now rotate the face image by the difference between the two eye-angles:

![Rotate image](/assets/face-swap/rotate-image.jpg)

Copy the result, and paste it onto the head image as a new layer. Halve the new
layer's opacity and line up the two faces using the Move tool (M):

![Align image](/assets/face-swap/align-image.jpg)

Return the top layer's opacity to 100%.

## 3. Adjust the colour balance of the face layer

Make a copy of both layers, with the face copy on top and the head copy just
below:

![layers](/assets/face-swap/layers.png)

Now apply a gaussian blur to both. The blur amount should be as high as
you can get without non-flesh tones from hair or background interfering with
areas you want to transfer to the head image. About 2/3 of the head image
eye-distance has worked well for me:

![Face blur](/assets/face-swap/face-blur.jpg)
![Head blur](/assets/face-swap/head-blur.jpg)

Now set the new face layer to divide, and the new head layer to multiply. The
face image should now be shining through, but with the right lighting and
fleshtones around the facial area:

![Colour adjusted face image](/assets/face-swap/colour-adjusted-face-image.jpg)

At this point select *Copy Visible* from the *Edit* menu, and paste as a new
layer.Move the new layer to second from bottom (right above the bottom head
layer), and make all layers above it invisible.

## 4. Select facial features with a Layer Mask

Add a layer mask to the newly pasted, colour-corrected face layer. Initialise
it to black (fully transparent). Now with the brush tool draw over the eye,
nose and mouth area in white (opaque):

![Pre-blurred mask](/assets/face-swap/pre-blurred-mask.jpg)

Apply a gaussian blur to the layer mask, *et voila*:

![Camerband](/assets/face-swap/camerband.jpg)

