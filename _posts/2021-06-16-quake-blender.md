---
layout: default
title: 
thumbimage: /assets/quake-blender/thumb.jpg
#reddit-url: https://www.reddit.com/r/space/comments/m4a6jm/perseverance_rover_landing_footage_stabilized/
excerpt:
  Using Python and Blender I produce a tool for converting Quake demo files into
  a path-traced scene.
---

{% include post-title.html %}

{% include img.html src="/assets/quake-blender/title.jpg" alt="Header pic" %}

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

{% include vid.html src="/assets/quake-blender/demo_record.webm" %}

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

<div class="code-vertical-scroll">
{% highlight python %}
ServerMessagePrint(string='\x02\nVERSION 1.09 SERVER (5336 CRC)')
ServerMessageServerInfo(
    protocol=Protocol(version=<ProtocolVersion.NETQUAKE: 15>,
                      flags=<ProtocolFlags.0: 0>),
    max_clients=1, game_type=0, level_name='the Slipgate Complex',
    models=['maps/e1m1.bsp', '*1', '*2', '*3', '*4', '*5', '*6', '*7', '*8',
            '*9', '*10', '*11', '*12', '*13', '*14', '*15', '*16', '*17', '*18',
            '*19', '*20', '*21', '*22', '*23', '*24', '*25', '*26', '*27',
            '*28', '*29', '*30', '*31', '*32', '*33', '*34', '*35', '*36',
            '*37', '*38', '*39', '*40', '*41', '*42', '*43', '*44', '*45',
            '*46', '*47', '*48', '*49', '*50', '*51', '*52', '*53', '*54',
            '*55', '*56', '*57', 'progs/player.mdl', 'progs/eyes.mdl',
            'progs/h_player.mdl', 'progs/gib1.mdl', 'progs/gib2.mdl',
            'progs/gib3.mdl', 'progs/s_bubble.spr', 'progs/s_explod.spr',
            'progs/v_axe.mdl', 'progs/v_shot.mdl', 'progs/v_nail.mdl',
            'progs/v_rock.mdl', 'progs/v_shot2.mdl', 'progs/v_nail2.mdl',
            'progs/v_rock2.mdl', 'progs/bolt.mdl', 'progs/bolt2.mdl',
            'progs/bolt3.mdl', 'progs/lavaball.mdl', 'progs/missile.mdl',
            'progs/grenade.mdl', 'progs/spike.mdl', 'progs/s_spike.mdl',
            'progs/backpack.mdl', 'progs/zom_gib.mdl', 'progs/v_light.mdl',
            'progs/armor.mdl', 'progs/g_nail.mdl', 'progs/soldier.mdl',
            'progs/h_guard.mdl', 'maps/b_nail0.bsp', 'progs/quaddama.mdl',
            'maps/b_bh100.bsp', 'maps/b_shell0.bsp', 'maps/b_bh10.bsp',
            'maps/b_bh25.bsp', 'maps/b_nail1.bsp', 'progs/h_dog.mdl',
            'progs/dog.mdl', 'progs/suit.mdl', 'progs/g_shot.mdl',
            'maps/b_explob.bsp'], sounds=['weapons/r_exp3.wav',
            'weapons/rocket1i.wav', 'weapons/sgun1.wav', 'weapons/guncock.wav',
            'weapons/ric1.wav', 'weapons/ric2.wav', 'weapons/ric3.wav',
            'weapons/spike2.wav', 'weapons/tink1.wav', 'weapons/grenade.wav',
            'weapons/bounce.wav', 'weapons/shotgn2.wav', 'items/damage2.wav',
            'demon/dland2.wav', 'misc/h2ohit1.wav', 'items/itembk2.wav',
            'player/plyrjmp8.wav', 'player/land.wav', 'player/land2.wav',
            'player/drown1.wav', 'player/drown2.wav', 'player/gasp1.wav',
            'player/gasp2.wav', 'player/h2odeath.wav', 'misc/talk.wav',
            'player/teledth1.wav', 'misc/r_tele1.wav', 'misc/r_tele2.wav',
            'misc/r_tele3.wav', 'misc/r_tele4.wav', 'misc/r_tele5.wav',
            'weapons/lock4.wav', 'weapons/pkup.wav', 'items/armor1.wav',
            'weapons/lhit.wav', 'weapons/lstart.wav', 'items/damage3.wav',
            'misc/power.wav', 'player/gib.wav', 'player/udeath.wav',
            'player/tornoff2.wav', 'player/pain1.wav', 'player/pain2.wav',
            'player/pain3.wav', 'player/pain4.wav', 'player/pain5.wav',
            'player/pain6.wav', 'player/death1.wav', 'player/death2.wav',
            'player/death3.wav', 'player/death4.wav', 'player/death5.wav',
            'weapons/ax1.wav', 'player/axhit1.wav', 'player/axhit2.wav',
            'player/h2ojump.wav', 'player/slimbrn2.wav', 'player/inh2o.wav',
            'player/inlava.wav', 'misc/outwater.wav', 'player/lburn1.wav',
            'player/lburn2.wav', 'misc/water1.wav', 'misc/water2.wav',
            'ambience/buzz1.wav', 'doors/basetry.wav', 'doors/baseuse.wav',
            'doors/hydro1.wav', 'doors/hydro2.wav', 'misc/null.wav',
            'ambience/fl_hum1.wav', 'buttons/switch21.wav', 'plats/plat1.wav',
            'plats/plat2.wav', 'doors/stndr1.wav', 'doors/stndr2.wav',
            'doors/basesec1.wav', 'doors/basesec2.wav', 'misc/trigger1.wav',
            'soldier/death1.wav', 'soldier/idle.wav', 'soldier/pain1.wav',
            'soldier/pain2.wav', 'soldier/sattck1.wav', 'soldier/sight1.wav',
            'items/damage.wav', 'buttons/airbut1.wav', 'ambience/hum1.wav',
            'items/r_item2.wav', 'items/r_item1.wav', 'items/health1.wav',
            'doors/drclos4.wav', 'doors/doormv1.wav', 'dog/dattack1.wav',
            'dog/ddeath.wav', 'dog/dpain1.wav', 'dog/dsight.wav',
            'dog/idle.wav', 'items/suit.wav', 'items/suit2.wav',
            'misc/secret.wav', 'ambience/comp1.wav', 'ambience/drone6.wav'])
ServerMessageCdTrack(track=6, loop=6)
ServerMessageSetView(viewentity=1)
{% endhighlight %}
</div>

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


