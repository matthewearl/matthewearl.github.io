---
layout: default
title: Re-projecting the Mars 2020 landing footage onto satellite imagery
thumbimage: /assets/mars2020-reproject/thumb.jpg
#reddit-url: https://www.reddit.com/r/programming/comments/8us6jx/how_i_extracted_super_mario_bros_level_data_using/
excerpt:
  Using Python, OpenCV, and PyTorch to reproject the Mars 2020 / Perserverance
  descent and landing footage onto satellite imagery of the area.
---


{% include post-title.html %}

{% include img.html src="/assets/mars2020-reproject/title.jpg" alt="Header pic" %}

## Introduction

The landing of the Mars 2020 Perserverance rover last month amazed the world.
The stunning footage of the descent shows each stage of the thrilling sequence.
If you haven't seen it already
[watch it here](https://www.youtube.com/watch?v=4czjS9h4Fpg).

One thing that I found remarkable was the self-similarity of the martian
terrain.  As the lander descends towards the ground it's hard to get a
sense of scale, since there is no familiar frame of reference to tell us how far
away the ground is.  This inspired me to embark on this project in which I
reproject the footage onto a satellite image obtained from the
[Mars Express](https://en.wikipedia.org/wiki/Mars_Express),
along with a scale to tell us how large features on the ground are:

<iframe width="560" height="315"
src="https://www.youtube.com/embed/7kflC1nU0OM" frameborder="0"
allowfullscreen></iframe>

In this post I'm going to explain how I used Python, OpenCV, PyTorch, and
Blender to make the above footage.

## Keypoints and correspondences

Producing the video involves distorting the frames of the video so that each
frame lines up with the satellite image.  The usual way of doing this is to
produce some salient keypoints from each image, find correspondences between the
points, and then find a mathematical function that maps points in the first
image to those in the second image.

Let's break this down.  Here's a frame from the video that we wish to along on
the left, with the reference satellite image on the right:

{% include img.html src="/assets/mars2020-reproject/kp-blank.png" alt="images to align" %}

First of all, we use OpenCV's
[Scale Invariant Feature Transform](https://en.wikipedia.org/wiki/Scale-invariant_feature_transform) (SIFT) keypoint
detector to pull out salient keypoints from the image:

{% include img.html src="/assets/mars2020-reproject/kp-points.png" alt="images with keypoints indicated" %}

Each red cross here marks a potentially "interesting" point as determined by the
SIFT algorithm.  Associated with each point (but not shown) is a vector of 128
values which describes the part of the image that surrounds the keypoint.  The
idea is that this descriptor is invariant to things like scale (as the name
implies), rotation, and lighting differences.  We can then pair up points in our
pair of images with similar descriptors:

{% include img.html src="/assets/mars2020-reproject/kp-correspondences.png" alt="images with lines between corresponding keypoints" %}

## Projective transformations

The next step is to find a transformation that maps the keypoints from the video
frame onto the corresponding keypoints of the satellite image.  To do this we
make use of a class of transformations known as projective transformations.
Projective transformations can be used to describe how fixed points on a flat
plane change apparent position when viewed from a different position and angle.
This is appropriate in this context since the surface of Mars can be well
approximated by a flat plane at these distances.  The theory also assumes that
the camera conforms to an idealisted perspective projection, without any kind of
lens distortion.

A projective transformation is represented by a 3x3 matrix.  To apply such a
transformation to a 2D point we first append a one to give a 3-vector, then
multiply by the matrix.  To get back to a 2D point the result is divided by its
3rd element, and truncated back to a 2-vector.  This can be visualized by
plotting the points on the z=1 plane,  applying the transformation, and then
projecting each point towards the origin, back onto the z=1 plane:

{% include vid.html src="/assets/mars2020-reproject/diagram.webm" %}

Projective transforms have the property that the composition of two transforms
is equal to the projective transform given by the matrix product of their
respective matrices:

$$ \forall x \in \mathbb{R}^2 \ \colon \ p_{M_1} ( p_{M_2} (x) ) =
    p_{M_1 M_2} (x) $$

Where $$ p_{M} $$ denotes the projective transform associated with the 3x3
matrix $$ M $$.  When we talk about composing projective transforms, really what
we're doing is multiplying the underlying matrices.

Finding the transformation is done using a
[RANSAC](https://en.wikipedia.org/wiki/Random_sample_consensus) approach. I've
previously described RANSAC in a similar context in
[my pluto flyby post]({% post_url 2015-08-11-pluto-flyby %}). The process of
finding the keypoints, correspondences, and projective transforms using OpenCV
is described in
[this OpenCV tutorial](https://docs.opencv.org/master/d1/de0/tutorial_py_feature_homography.html).

Once we have a transform for each frame, we can reproject each video frame into
the frame of reference of the satellite image, thus obtaining the stablized
view.

## Finding transforms for each frame

If we had good correspondences between each frame and the satellite imagery,
then we'd have the required transforms to produce the video.  Unfortunately many
frames have no such correspondence.  To resolve this we also look for
transforms between video frames.  The idea being that if a frame has no direct
transform linking it to a satellite image, but we do have a transform linking it
to another frame that is itself connected to the satellite image, then we can
simply compose the two transforms to map the original frame onto the satellite
view.

In my scheme I label every 30th frame (ie. one frame per second) as a
"keyframe".  I then exhaustively search for transforms between each pair of
keyframes.  For the remaining frames I search for transforms to the nearest
keyframe.

This gives a fairly dense graph with one node per frame, and one edge per
transform found.  Here's a simple example, with keyframes at every 5 frames
rather than every 30:

{% include img.html src="/assets/mars2020-reproject/graph.svg" alt="graph showing connections between frames" %}

Any path from the satellite node to a particular frame's node represents a chain
of transformations that when composed will map the frame onto the satellite
view.

For now we'll just select one path for each node.  Doing a [breadth-first
search](https://en.wikipedia.org/wiki/Breadth-first_search)
from the satellite node will give us a path to each frame while also
guaranteeing that it is the shortest possible:

{% include img.html src="/assets/mars2020-reproject/bfs.svg" alt="previous graph but with shortest paths highlighted" %}

Having the shortest path is desirable since with each extra transformation a
little extra error will accumulate.

Here's the first few frames of the animation:

{% include vid.html src="/assets/mars2020-reproject/pre-opt.webm" %}

## Optimization
  
While the above method yields a decent reprojection, it's not perfect.  There
are clear mode switches around when the shortest path switches.  It would be
nice to incorporate information from the remaining image correspondences, that
is to say, the edges on the graph not on the shortest path.

To do this I wrote a loss function which returns the total reprojection error
given a satellite-relative transformation for each image:

{% highlight python %}
    def project(v):
        # Project onto the plane z=1
        return v / v[..., -1][..., None]

    def loss(frame_transforms, src_pts, dst_pts, src_idx, dst_idx):
        M_src_inv = torch.inverse(frame_transforms)[src_idx]
        M_dst = frame_transforms[dst_idx]
        ref_pts = torch.einsum('nij,nj->ni', M_src_inv, src_pts)
        reprojected_dst_pts = project(torch.einsum('nij,nj->ni', M_dst, ref_pts))

        return torch.dist(reprojected_dst_pts, dst_pts)
{% endhighlight %}

`src_pts` and `dst_pts` are both `N x 3` arrays, representing every pair of
points in the dataset.  `frame_transforms` is an `M x 3 x 3` array representing
the candidate transformations, `M` being the number of frames in the video.
`frame_transforms` are relative to the satellite image, which is to say a point
in the satellite image when transformed with `frame_transforms[i]` should
give the corresponding point in frame `i`.

Since there are multiple point-pairs per frame, `src_idx` and `dst_idx` are used
to map each half of each point pair to the corresponding video frame.

The `loss` function proceeds by taking the first points from each pair, mapping
them back into the satellite image's frame of reference, then mapping them into
the frame of reference of the second image.  With accurate frame transforms and
perfect correspondences these transformed points should be very close to the
corresponding set of second points.  The final line of the `loss` function then
just measures the euclidean (sum of squares) distance between the reprojected
points first points and the (unmodified) second points.  The idea is that if we
find a set of `frame_transforms` with a lower loss, then we'll have a more
accurate set of transformations.

`loss` is written using [Torch](https://pytorch.org/). Torch is an automatic
differentiation framework with functionality for applying [gradient
descent](https://en.wikipedia.org/wiki/Gradient_descent) (amongst other things).
As such we can use it to iteratively improve our `frame_transforms`:

{% highlight python %}

    src_pts, dst_pts, src_idx, dst_idx = dataset
    frame_transforms = initial_frame_transforms

    optim = torch.optim.Adam([frame_transforms], lr=1e-5)
    while True:
        optim.zero_grad()
        l = loss(frame_transforms, src_pts, dst_pts, src_idx, dst_idx)
        l.backward()
        optim.step()

{% endhighlight %}

`dataset` is constructed from the set of correspondences, and the
`initial_frame_transforms` are those derived from composing the transformations
along the shortest paths.

After running this loop for a while we obtain the final set of transformations
for each frame.

This produces a more stable set of transformations:

{% include vid.html src="/assets/mars2020-reproject/post-opt.webm" %}

## Rendering

To produce the final video I used the 3D modelling and rendering application
[Blender](https://en.wikipedia.org/wiki/Blender_(software)).  I used Blender's
rich Python scripting interface to animate a quad whose corners follow the
reprojected video's corners.

To get the right texture for the quad I took advantage of Blender's shader
system:

{% include img.html src="/assets/mars2020-reproject/shader.png" alt="screenshot
of blender shader" %}

In general, the shader system decides how a particular point on a surface should
be shaded, which is typically a function of incoming light, view direction, and
properties of the surface.  Here I'm using it in a very simple way which
calculates what colour the point on the quad should appear as given the point's
coordinates in 3D space.

Here's a breakdown of the various stages:

1. Take the location of the point to be coloured, and replace the Z component
   with a 1.  This is the first stage of the projective transform where we turn
   the 2-vector into a 3-vector by appending a one.
2. Multiply this 3-vector by a matrix defined by the constants shown here. These
   constants are in fact animated so that on any given frame these display
   `frame_transforms[frame_num]`.
3. Divide through by z (project onto the z=1 plane).
4. At this point the coordinates are in terms of pixels in the video frame.
   However the next stage needs them to be in the range 0 to 1, so divide by the
   video width and height here.
5. Look up the given coordinates in the video, and output the corresponding
   colour.

## Extra details

Here are some extra details omitted in the above:
 - I didn't just use one satellite image, but many.  However, I designate one as
   the "reference frame" (ie. the frame with the identity transform) and treat
   the rest as if they were video key frames.
 - During the early part of the video the heatshield is visible. Without any
   extra intervention, some frame correspondences end up tracking the heatshield
   (which is itself moving) rather than the terrain, causing bad tracking.  To
   deal with this I manually extracted some keypoints from near the heatshield
   on a particular frame, and ignore all keypoints that are similar to one of
   the heatsheid's keypoints.
 - Rarely degenerate frame correspondences are found. When all matching
   keypoints are in a line you get multiple solutions corresponding to rotations
   about that line.  Even if matching keypoints aren't exactly in a line but are
   close, the transformation found can be inaccurate.  There was one such image
   pair that caused this issue in my video, which I manually excluded.

## Conclusion

Potential improvements:
 - During the early part of the video there aren't many keypoints found by SIFT.
   This manifests itself as inaccuracy in the tracking.  Perhaps experimenting
   with different keypoint algorithms would help here?

