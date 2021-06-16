
## Introduction

Quake, released in 1996 broke new ground in game engine realism.  For the first
time, fully texture mapped 3D scenes were rendered in real-time in a commercial
game,  with pre-computed lightmaps adding an extra layer of atmosphere.

Still, the requirement that the game run in real time on the meagre hardware of
25 years ago, places massive constraints on graphical realism.  In this post I
want to explore just how good the game can be made to look, with modern
hardware, and offline rendering.

More specifically, I'm going to talk about how I wrote a script for converting
Quake demo files into Blender scenes.  Blender is a free and open source 3D
modelling and rendering application. Its renderer, Cycles, is a path-tracer
capable of producing photo-realistic imagery, supporting features such as motion
blur, depth of field, a comprehensive shader system, and much more.  By
exporting to Blender we get to use all of these features for free, without
having to write a new renderer.  My objective is to use the original game assets
as much as possible, while relying on Blender's accurate lighting simulation to
improve realism.


## Parsing demos

A demo file is a compact recording of a Quake game, for the purposes of sharing
with other players, or for personal review.  Being a multiplayer game, the game
is split into client and server components.  The demo is essentially a recording
of the traffic that goes from server to client during the game.  Given a demo,
and an installation of Quake, it's then possible to reproduce exactly what the
player saw at the time of recording:

[Clip of demo explain vid]

Note that even in single player mode, internally there are still client and
server components in the code (with the network layer replaced by a simple
memory transfer) which means demos can be recorded in this setting too.

Since the demo file format is closely related to the Quake networking code it
can be understood by reading the appropriate layer of Quake's networking code.
It's then relatively straightforward, if a little laborious, to write a parser
for the demo file format in Python.  

When parsed, the demo file can be read a little like a script for a play.  The
initial commands set the scene, saying which level is being played, along with
what assets --- models and sounds --- will be used throughout the demo.

[Parsed demo code for intro section]

Next comes a series of baseline commands, which define a set of entities, each
of which is associated with one of the aforementioned models, like a cast list
in a play.  Entities represent all objects in the game.  An entity might be a
monster, the player, a health pack, a lift, a button.  Everything except for the
static parts of the level.

[Baseline commands]

Finally, a series of update and time commands given the entities' position,
angle, and pose at the given time, a series of stage directions in the analogy.

[update commands]

My Python code for parsing demo files can
be found [here](https://github.com/matthewearl/pyquake/blob/master/pyquake/proto.py).

## Parsing assets

The level itself is defined in a .bsp file.  This gives the geometry and texture
information, for the level, along with some other data structures which we'll
come onto later.  The file format is
[well documented](https://www.gamers.org/dEngine/quake/spec/quake-spec34/qkspec_4.htm)
and with a little effort can be parsed into Python classes.  My Python code for
parsing BSP files can be found
[here](https://github.com/matthewearl/pyquake/blob/master/pyquake/bsp.py)

[fly-through of level?]

Similarly, the models defined in .mdl files, which represent things like
monsters, weapon models, and so on, are in a
[well documented format](https://www.gamers.org/dEngine/quake/spec/quake-spec34/qkspec_5.htm)

My Python code for parsing MDL files can be found
[here](https://github.com/matthewearl/pyquake/blob/master/pyquake/mdl.py).

[rotating shot of monster?]

## Loading into Blender

[Blender](https://www.blender.org/) is a free and open-source 3D graphics and
modelling application, with a realistic path-tracing renderer.  Furthermore, it
is highly scriptable with Python.  Using this interface, I made a script to
convert the BSP files and models parsed above into Blender.  For most of the
concepts in the Quake assets there are direct analogues Blender's representation
of the scene:

- Quake models and map geometry can be represented as Blender meshes.
- Animation frames in Quake models can be represented with shape keys in Blender.
- Quake texture data can be represented as images and shaders in Blender.
[...anything else?]

My code for importing models into blender is
[here](https://github.com/matthewearl/pyquake/blob/master/pyquake/blendmdl.py)
and code for importing BSP files is
[here](https://github.com/matthewearl/pyquake/blob/master/pyquake/blenddemo.py).

Loading a demo then, consists of reading the intro section to tell us which
game assets (models and map) to convert into Blender assets, and then animating
them according to the baseline / update sections.  I make use of Blender's rich
animation support to do this, in particular, keyframing.

[clip of panning around a demo file?]

My code for converting demos files into Blender can be found
[here](https://github.com/matthewearl/pyquake/blob/master/pyquake/blenddemo.py#L673).


## Lighting

At this point we have our geometry loaded, animated, with some textures applied.
Still, we're missing light sources.  When the Quake levels were designed, lights
were defined as point light sources scattered throughout the level.  A
compilation process then converts these point light sources into light maps.
This process works by assigning a low resolution texture to each surface in the
level, and calculating how much each texel is directly illuminated by these
point light sources.  Since this process only measures direct illumination,
level designers included secondary light sources to fake the effects of bounced
light.

Since the original map sources are available, I *could* use these lights to
illuminate my scene.  However, because Blender can do accurate multi-bounce
illumination by itself including all these lights would mean doubling up on
bounced lights, and would give an over illuminated scene.

[View of a light texture on LHS with palette on RHS]

Instead, I'm going to illuminate the scene directly from the texture
information.  All textures in Quake are composed using a 256 colour palette.
The last 32 colours in this palette are special in that they always appear as
fullbright, that is to say, even when in shadow they still appear fully
illuminated.

[Shot of light in a render showing emissiveness]

In my system, I treat these fullbright colours as being emissive,
so that they illuminate the space around them as well as appearing bright to the
camera.  In addition, I treat select models as being emissive, for example the
flame models that are used in the non-tech levels.

So our scene is now set --- our geometry is in place, textures are applied, and
lighting is defined.  Let's render an image and see what we get:

[image of noisy image produced with all lights on e1m1 set as sample_as_light]

Oh dear!  This single frame took around 20 seconds to render on my reasonably
powerful graphics card, and it is still incredibly grainy!  Even applying
Blender's bundled denoiser can't recover a clean image.  Blender can normally
handle scenes of this complexity with no issues, so what's going on?


## Reducing noise

When Blender wishes to work out how well a point is illuminated, it (by default)
randomly samples from all light sources in the scene and averages the
contribution from each light source sampled.   For most levels, there are way
more light sources in the scene than are visible at any given time.  This means
that the contribution from most light sources is zero, and so the result is
highly noisy, depending on whether a visible light happened to be sampled.

Fortunately, Blender allows us to control which lights are sampled by setting
the `sample_as_light` flag (referred to as Multiple Importance Sampling in the
UI) on textures.  This flag can be animated with keyframes, so we can make it
change depending on the current player position.

## BSP visibility

The BSP file divides the level into a set of disjoint volumes called leaves.
Each leaf contains a handful of faces.

[leaf bitmap image]

The visibility information in the BSP is a large 2D bitmap telling us which
leaves can *potentially* see each other.  The set of leaves that a given leaf
can potentially see is known as its potentially visible set, or PVS.

As a first approximation, we can simply sample a light if and only if the
camera's PVS has any leaves in common with the light's PVS. For example, here
you can see the light PVS intersects with the camera's and so we enable
importance sampling on this light.  This distant light however would not be
drawn.

[Highlight sampled lights in green, and non-sampled lights in red]

This works well, and does improve the situation a little, however, there's a
couple more things we can do.

Again taking inspiration from Quake's visibility calculations we can apply
what's known as frustum culling.  With the camera we can associate a viewing
frustum, that is to say, a volume whose faces correspond with the edges of the
screen projected out from the camera's origin.  Any point lying outside of the
viewing frustum will be invisible to the camera.

[Draw camera PVS intersected with viewing frustum]

A similar concept can be applied to the light's PVS --- practically a light's
sphere of influence is bounded by the inverse square law, and so we can place a
bounding box around each light,  whose size is determined by how bright the
light is.  We can therefore reduce the light's PVS by intersecting with this
bounding box.

The final system I use then is based on seeing whether these two reduced PVS
volumes intersect.  As you can see, it works better than the unreduced system,
and a lot better than the system that simply samples all lights.  Applying
Blender's noise reduction system yields a pretty smooth looking image.

[image]


