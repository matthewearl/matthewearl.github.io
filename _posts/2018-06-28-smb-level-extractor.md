---
layout: default
title: Extracting Super Mario Bros levels with Python
thumbimage: /assets/smb-level-extractor/thumb.png
excerpt:
  A script for extracting level data from the Super Mario Bros ROM, using a 6502
  emulator and Python.
noindex: 1
---

{% include post-title.html %}

{% include img.html src="/assets/smb-level-extractor/output.png" alt="SMB Header" %}

## Introduction

For an upcoming project a need arose to extract level data from the classic 1985
video game, [Super Mario Bros](https://en.wikipedia.org/wiki/Super_Mario_Bros.).
More precisely, I want to extract the background imagery for each stage of the
game, excluding HUD elements, and moving sprites, etc.

To do this I decided to reverse engineer the level format used by SMB, by
inspecting the source code.

In this post I'll talk about my journey towards this goal touching on 6502
assembly and an emulator written in Python.


## Source code analysis

Reverse engineering any program is a lot easier if you have the source code
available.  In this case the source code is available in the form of 17,000
lines of 6502 (the NES CPU) assembly code, [put together by doppelganger](https://gist.github.com/1wErt3r/4048722).
Because Nintendo has never made an official source release, the assembly was put
together by disassembling the SMB ROM data, and painstakingly deciphering what
each part means, inserting comments and meaningful symbol names along the way.

A quick search through the file and we find something that looks a lot like it
might be the level data we seek:

```
;level 1-1
L_GroundArea6:
      .db $50, $21
      .db $07, $81, $47, $24, $57, $00, $63, $01, $77, $01
      .db $c9, $71, $68, $f2, $e7, $73, $97, $fb, $06, $83
      .db $5c, $01, $d7, $22, $e7, $00, $03, $a7, $6c, $02
      .db $b3, $22, $e3, $01, $e7, $07, $47, $a0, $57, $06
      .db $a7, $01, $d3, $00, $d7, $01, $07, $81, $67, $20
      .db $93, $22, $03, $a3, $1c, $61, $17, $21, $6f, $33
      .db $c7, $63, $d8, $62, $e9, $61, $fa, $60, $4f, $b3
      .db $87, $63, $9c, $01, $b7, $63, $c8, $62, $d9, $61
      .db $ea, $60, $39, $f1, $87, $21, $a7, $01, $b7, $20
      .db $39, $f1, $5f, $38, $6d, $c1, $af, $26
      .db $fd
```

If you're not familiar with assembly, this is just saying insert these bytes
verbatim into the compiled program, and then allow other parts of the program to
refer to it via the symbol `L_GroundArea6`.  You can think of it as an array
where each element is a single byte.

First thing to note is that this is a very small amount of data (about 100
bytes).  This almost certainly rules out any sort of encoding which allows
arbitrary placement of blocks in the level.  After a bit of searching I found
that this data is actually read (after some indirection) in
[AreaParserCore](https://gist.github.com/1wErt3r/4048722#file-smbdis-asm-L3154).
This subroutine in turn calls lots of other subroutines, eventually calling a
special subroutine for each type of object that can be in a scene (eg.
`StaircaseObject`, `VerticalPipe`, `RowOfBricks`) for a total of over 40
different objects:

{% include img.html src="/assets/smb-level-extractor/call-graph.png" alt="Call graph" %}

<sup>Abbreviated call graph for `AreaParserCore`</sup>

The routine writes into a `MetatileBuffer`, which is a 13-byte long section of
memory representing a single column of blocks in a level, each byte representing
a single block. A metatile is a 16x16 block that make up the backgrounds in SMB:

{% include img.html src="/assets/smb-level-extractor/metatiles.png" alt="Metatiles" %}

<sup>Level with boxes drawn around the metatiles</sup>

They're called metatiles because each one actually consists of four 8x8 pixel
tiles, but more on this later.

The fact that the decoder works in terms of predefined objects explains the
small level size: The level data just needs to refer to object types and
locations, for example, "place a pipe at location (20, 16), a row of blocks at
location (10, 5), ...", however it does mean that there is a lot of code required to
turn the raw level data into metatiles.

I didn't feel like porting this amount of code into Python in order to write my
level extractor, so I tried a different approach.

## py65emu

At this point I had decided that porting all of the level parsing code would be
extremely labourious.  But do I really need to?  I have the parsing code
available, it just happens to be written in 6502 assembly language.  If I had an
interface between Python and 6502 I could call the `AreaParserCore` subroutine
for each column of the level, and then use the conciseness of Python to convert
the block information into the image I desired.

Enter [py65emu](https://github.com/docmarionum1/py65emu), a concise 6502
emulator with a programmatic Python interface.  Here's how to set up py65emu to
start emulating some 6502 machine code, with the memory map set up to match that
of the NES:
{% highlight python %}
    from py65emu.cpu import CPU
    from py65emu.mmu import MMU

    # Load in the program ROM (ie. the compiled assembly)
    with open("program.bin", "rb") as f:
        prg_rom = f.read()

    # Define the memory mapping.
    mmu = MMU([
        # Create 2K RAM, mapped to address 0x0.
        (0x0, 2048, False, []),

        # Map the program ROM to 0x8000.
        (0x8000, len(prg_rom), True, list(prg_rom))
    ])

    # Create the CPU, telling it to start executing at location 0x1000
    cpu = CPU(mmu, 0x8000)
{% endhighlight %}

After this we can execute a single instruction with the `cpu.step()` method, and
at any point we can inspect the memory with `mmu.read()`, and check the
machine's registers with `cpu.r.a`, `cpu.r.pc`, etc.  In addition we can write
to the memory at any point too with `mmu.write()`.

It should be noted that this is only an emulator for the CPU of the NES: It
doesn't emulate other parts of the hardware such as the PPU, so it can't be used
to emulate the entire game.  It should however be sufficient for calling the
parsing subroutine which doesn't rely on any hardware beyond the CPU and memory.

The plan is to set up the CPU as above,  then for each column of the level
initialize sections of the memory with the inputs that `AreaParserCore` needs,
call `AreaParserCore`, and then read back the column data.  Once this is done
we'll use Python to compose the result into an image.

But before we do this we'll actually need to compile the assembly listing into
machine code.

## x816

As noted in the source the assembly compiles with x816. x816 is an MS-DOS based
6502 assembler used by the NES homebrew and ROM hacking community, which works
great in [DOSBox](https://en.wikipedia.org/wiki/DOSBox).

Along with the program ROM that's required by py65emu, x816 produces a symbol
file which maps symbols to their memory locations in the CPU's address space.
Here's an excerpt:
```
AREAPARSERCORE                   = $0093FC   ; <> 37884, statement #3154
AREAPARSERTASKCONTROL            = $0086E6   ; <> 34534, statement #1570
AREAPARSERTASKHANDLER            = $0092B0   ; <> 37552, statement #3035
AREAPARSERTASKNUM                = $00071F   ; <> 1823, statement #141
AREAPARSERTASKS                  = $0092C8   ; <> 37576, statement #3048
```
Here we can see the `AreaParserCore` function will be accessible at address
0x93fc in the source.

For convenience I put together a parser for the symbol file, which maps
between symbol names and addresses:

{% highlight python %}
sym_file = SymbolFile('SMBDIS.SYM')
print("0x{:x}".format(sym_file['AREAPARSERCORE'])) # prints 0x93fc
print(sym_file.lookup_address(0x93fc)) # prints "AREAPARSERCORE"
{% endhighlight %}

## Subroutines

As mentioned in the plan above, we want to be able to call the `AreaParserCore`
subroutine programmatically. 

To understand the mechanics of a subroutine lets look at a short subroutine and
its corresponding call:

{% highlight python %}
WritePPUReg1:
               sta PPU_CTRL_REG1         ;write contents of A to PPU register 1
               sta Mirror_PPU_CTRL_REG1  ;and its mirror
               rts

...

jsr WritePPUReg1
{% endhighlight %}

The `jsr` (jump to subroutine) instruction pushes the PC register onto the
stack, and sets the PC register to the address referred to by `WritePPUReg1`.
The PC register tells the CPU of the address of the next instruction to load, so
the next instruction executed after the `jsr` instruction will be the first line
of `WritePPUReg1`. 

At the end of the subroutine an `rts` (return from subroutine) instruction is
executed.  This command pops the saved value from the stack and stores it in the
PC register, which makes the CPU execute the instruction following the `jsr`
call.

The great thing about subroutines is you can have nested calls; calls to
subroutines within subroutines. Return addresses will be pushed onto the stack
and then popped off in the correct order, in the way you'd expect of function
calls in a high level language.

Here then is the code for executing a subroutine from Python:
{% highlight python %}
def execute_subroutine(cpu, addr):
    s_before = cpu.r.s
    cpu.JSR(addr)
    while cpu.r.s != s_before:
        cpu.step()

execute_subroutine(cpu, sym_file['AREAPARSERCORE'])
{% endhighlight %}

This works by saving the current value of the stack pointer register (`s`),
emulating a `jsr` call, and then executing instructions until the stack has
returned to its initial height, which will only happen when the first subroutine
has returned.

This is great, as we've now got a way of directly calling 6502 subroutines from
within Python, however there is something I've glossed over thus far.  More
specifically, I haven't been clear on how to provide inputs to this subroutine.
We need a way to tell the routine what level we're trying to render, or which
particular column we want to parse.

Unlike a high-level language such as C or Python, subroutines in 6502 assembly
don't take explicit arguments.  Rather inputs are passed by setting memory
locations at some point prior to the call, which are then read anywhere within
the subroutine call.  Given the size of `AreaParserCore` reverse engineering the
required arguments purely by looking at the source would be difficult and
error-prone.

## Valgrind for NES?

To work out what the inputs to `AreaParserCore` were, I drew inspiration from
the [memcheck](http://valgrind.org/docs/manual/mc-manual.html) tool for
Valgrind.  Memcheck detects accesses to uninitialized memory by storing "shadow"
memory alongside every piece of actual memory that is allocated.  The shadow
memory indicates whether the corresponding "real" memory has ever been written
to.  If the program reads from an address that has never been written to, an
uninitialized memory error is printed.  If I could run `AreaParserCore` with
such a tool it would tell me the inputs to the subroutine that should be set
before being called.

It's actually very easy to write a simple version of memcheck for py65emu:
{% highlight python %}
def format_addr(addr):
    try:
        symbol_name = sym_file.lookup_address(addr)
        s = "0x{:04x} ({}):".format(addr, symbol_name)
    except KeyError:
        s = "0x{:04x}:".format(addr)
    return s

class MemCheckMMU(MMU):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._uninitialized = array.array('B', [1] * 2048)

    def read(self, addr):
        val = super().read(addr)
        if addr < 2048:
            if self._uninitialized[addr]:
                print("Uninitialized read! {}".format(format_addr(addr)))
        return val

    def write(self, addr, val):
        super().write(addr, val)
        if addr < 2048:
            self._uninitialized[addr] = 0
{% endhighlight %}

Here I've wrapped the py65emu's memory management object.  This class maintains
an array `_uninitialized` whose entries tell us whether the corresponding byte
of the emulated RAM has ever been written to.  When an uninitialized read occurs
the address of the invalid read and the corresponding symbol name is printed.

Here's what `execute_subroutine(sym_file['AREAPARSERCORE'])` gives with the
wrapped MMU:
```
Uninitialized read! 0x0728 (BACKLOADINGFLAG):
Uninitialized read! 0x0742 (BACKGROUNDSCENERY):
Uninitialized read! 0x0741 (FOREGROUNDSCENERY):
Uninitialized read! 0x074e (AREATYPE):
Uninitialized read! 0x075f (WORLDNUMBER):
Uninitialized read! 0x0743 (CLOUDTYPEOVERRIDE):
Uninitialized read! 0x0727 (TERRAINCONTROL):
Uninitialized read! 0x0743 (CLOUDTYPEOVERRIDE):
Uninitialized read! 0x074e (AREATYPE):
...
```

Searching around the code I see that many of these values are set by the
subroutine `InitializeArea`, so I re-run the script with a call to this function
first.  Repeating this process I end up with the following arrangement of calls
which just needs the world number and area number to be set:

{% highlight python %}
mmu.write(sym_file['WORLDNUMBER'], 0)    # World number, minus 1
mmu.write(sym_file['AREANUMBER'], 0)     # Level number, minus 1
execute_subroutine(sym_file['LOADAREAPOINTER'])
execute_subroutine(sym_file['INITIALIZEAREA'])

l = []
for column_pos in range(48):
    execute_subroutine(sym_file['AREAPARSERCORE'])
    l.append([mmu.read_no_debug(sym_file['METATILEBUFFER'] + i)
                for i in range(13)])
    execute_subroutine(sym_file['INCREMENTCOLUMNPOS'])
{% endhighlight %}

This reads the first 48 columns of world 1-1 into `l`, using the subroutine
`IncrementColumnPos` to increment the internal variables used to track the
current column.

And here is the contents of `l`, overlaid onto some screenshots from the game
(0 bytes are not shown):

{% include img.html src="/assets/smb-level-extractor/output.png" alt="Output" %}

Looking good: The data in `l` clearly corresponds with the background
information.

## Metatile imagery

In this section I'll talk about how we turn the metatile numbers fetched above
into actual images.  The steps here were worked out by analysing the source and
studying the documentation on the excellent [Nesdev Wiki](https://wiki.nesdev.com/).

To understand how to render each metatile we first need to talk about palettes
on the NES.  The NES PPU has the ability to render 64 different colours in
total:

{% include img.html src="/assets/smb-level-extractor/nespal.png" alt="Output" %}

However, a single mario level only has the ability to render 16 colours, divided
into 4 four colour palettes. Here are the 4 palettes for world 1-1:

{% include img.html src="/assets/smb-level-extractor/w11pal.png" alt="Output" %}

Now, let's take a look at an example metatile number decomposed into binary.
Here's the metatile number for the cracked rock tile that runs along the ground
of world 1-1:

{% include img.html src="/assets/smb-level-extractor/mtile-bits.png" alt="Metatile Bits" %}

The palette index tells us which palette to use when rendering the metatile, in
this case palette 1.  In addition, the palette index is also an index into these
two arrays:

```
MetatileGraphics_Low:
  .db <Palette0_MTiles, <Palette1_MTiles, <Palette2_MTiles, <Palette3_MTiles

MetatileGraphics_High:
  .db >Palette0_MTiles, >Palette1_MTiles, >Palette2_MTiles, >Palette3_MTiles
```

These arrays combined give a 16 bit address, which for our example points us at
`Palette1_Mtiles`:
```
Palette1_MTiles:
  .db $a2, $a2, $a3, $a3 ;vertical rope
  .db $99, $24, $99, $24 ;horizontal rope
  .db $24, $a2, $3e, $3f ;left pulley
  .db $5b, $5c, $24, $a3 ;right pulley
  .db $24, $24, $24, $24 ;blank used for balance rope
  .db $9d, $47, $9e, $47 ;castle top
  .db $47, $47, $27, $27 ;castle window left
  .db $47, $47, $47, $47 ;castle brick wall
  .db $27, $27, $47, $47 ;castle window right
  .db $a9, $47, $aa, $47 ;castle top w/ brick
  .db $9b, $27, $9c, $27 ;entrance top
  .db $27, $27, $27, $27 ;entrance bottom
  .db $52, $52, $52, $52 ;green ledge stump
  .db $80, $a0, $81, $a1 ;fence
  .db $be, $be, $bf, $bf ;tree trunk
  .db $75, $ba, $76, $bb ;mushroom stump top
  .db $ba, $ba, $bb, $bb ;mushroom stump bottom
  .db $45, $47, $45, $47 ;breakable brick w/ line 
  .db $47, $47, $47, $47 ;breakable brick 
  .db $45, $47, $45, $47 ;breakable brick (not used)
  .db $b4, $b6, $b5, $b7 ;cracked rock terrain <--- This is the 20th line
  .db $45, $47, $45, $47 ;brick with line (power-up)
  .db $45, $47, $45, $47 ;brick with line (vine)
  .db $45, $47, $45, $47 ;brick with line (star)
  .db $45, $47, $45, $47 ;brick with line (coins)
  ...
```

The metatile index multipled by 4 is an index into this array.  The data is
formatted with 4 entries per line, so the line referred to by the example is the
20th (reassuringly commented as `cracked rock terrain`).

The four entries on this line are in fact tile IDs:  Each metatile consists of
four 8x8 pixel tiles, top-left, bottom-left, top-right, bottom-right
respectively.  These IDs are sent directly to the NES's PPU and the ID refers to
16 bytes of data in the NES's CHR-ROM:


```
0x1000 + 16 * 0xb4 +  0:   0b01111111             0x1000 + 16 * 0xb5 +  0:   0b11011110
0x1000 + 16 * 0xb4 +  1:   0b10000000             0x1000 + 16 * 0xb5 +  1:   0b01100001
0x1000 + 16 * 0xb4 +  2:   0b10000000             0x1000 + 16 * 0xb5 +  2:   0b01100001
0x1000 + 16 * 0xb4 +  3:   0b10000000             0x1000 + 16 * 0xb5 +  3:   0b01100001
0x1000 + 16 * 0xb4 +  4:   0b10000000             0x1000 + 16 * 0xb5 +  4:   0b01110001
0x1000 + 16 * 0xb4 +  5:   0b10000000             0x1000 + 16 * 0xb5 +  5:   0b01011110
0x1000 + 16 * 0xb4 +  6:   0b10000000             0x1000 + 16 * 0xb5 +  6:   0b01111111
0x1000 + 16 * 0xb4 +  7:   0b10000000             0x1000 + 16 * 0xb5 +  7:   0b01100001
0x1000 + 16 * 0xb4 +  8:   0b10000000             0x1000 + 16 * 0xb5 +  8:   0b01100001
0x1000 + 16 * 0xb4 +  9:   0b01111111             0x1000 + 16 * 0xb5 +  9:   0b11011111
0x1000 + 16 * 0xb4 + 10:   0b01111111             0x1000 + 16 * 0xb5 + 10:   0b11011111
0x1000 + 16 * 0xb4 + 11:   0b01111111             0x1000 + 16 * 0xb5 + 11:   0b11011111
0x1000 + 16 * 0xb4 + 12:   0b01111111             0x1000 + 16 * 0xb5 + 12:   0b11011111
0x1000 + 16 * 0xb4 + 13:   0b01111111             0x1000 + 16 * 0xb5 + 13:   0b11111111
0x1000 + 16 * 0xb4 + 14:   0b01111111             0x1000 + 16 * 0xb5 + 14:   0b11000001
0x1000 + 16 * 0xb4 + 15:   0b01111111             0x1000 + 16 * 0xb5 + 15:   0b11011111

0x1000 + 16 * 0xb6 +  0:   0b10000000             0x1000 + 16 * 0xb7 +  0:   0b01100001
0x1000 + 16 * 0xb6 +  1:   0b10000000             0x1000 + 16 * 0xb7 +  1:   0b01100001
0x1000 + 16 * 0xb6 +  2:   0b11000000             0x1000 + 16 * 0xb7 +  2:   0b11000001
0x1000 + 16 * 0xb6 +  3:   0b11110000             0x1000 + 16 * 0xb7 +  3:   0b11000001
0x1000 + 16 * 0xb6 +  4:   0b10111111             0x1000 + 16 * 0xb7 +  4:   0b10000001
0x1000 + 16 * 0xb6 +  5:   0b10001111             0x1000 + 16 * 0xb7 +  5:   0b10000001
0x1000 + 16 * 0xb6 +  6:   0b10000001             0x1000 + 16 * 0xb7 +  6:   0b10000011
0x1000 + 16 * 0xb6 +  7:   0b01111110             0x1000 + 16 * 0xb7 +  7:   0b11111110
0x1000 + 16 * 0xb6 +  8:   0b01111111             0x1000 + 16 * 0xb7 +  8:   0b11011111
0x1000 + 16 * 0xb6 +  9:   0b01111111             0x1000 + 16 * 0xb7 +  9:   0b11011111
0x1000 + 16 * 0xb6 + 10:   0b11111111             0x1000 + 16 * 0xb7 + 10:   0b10111111
0x1000 + 16 * 0xb6 + 11:   0b00111111             0x1000 + 16 * 0xb7 + 11:   0b10111111
0x1000 + 16 * 0xb6 + 12:   0b01001111             0x1000 + 16 * 0xb7 + 12:   0b01111111
0x1000 + 16 * 0xb6 + 13:   0b01110001             0x1000 + 16 * 0xb7 + 13:   0b01111111
0x1000 + 16 * 0xb6 + 14:   0b01111111             0x1000 + 16 * 0xb7 + 14:   0b01111111
0x1000 + 16 * 0xb6 + 15:   0b11111111             0x1000 + 16 * 0xb7 + 15:   0b01111111
```

The CHR-ROM is a piece of read-only memory that can be accessed only by the PPU
and is separate to the PRG-ROM where the program code is stored.  As such the
above data isn't available in the source code and needs to be retrieved from a
ROM dump of SMB.

The 16 bytes for each tile actually make up a 2-bit 8x8 tile (the first bit is
the first 8 bytes, and the second bit is the second 8 bytes):

```
21111111  13211112
12222222  23122223
12222222  23122223
12222222  23122223
12222222  23132223
12222222  23233332
12222222  23111113
12222222  23122223

12222222  23122223
12222222  23122223
33222222  31222223
11332222  31222223
12113333  12222223
12221113  12222223
12222223  12222233
23333332  13333332
```

Map this through palette 1:

{% include img.html src="/assets/smb-level-extractor/mapped-tiles.png" alt="Mapped tiles" %}

...and join together:

{% include img.html src="/assets/smb-level-extractor/final-tile.png" alt="Mapped tiles" %}

And finally we have our rendered tile.  Repeat this routine for each metatile
and we get the fully rendered level:

{% include img.html src="/assets/smb-level-extractor/w11.png" alt="World 1-1" %}


