---
layout: default
title: Bresenham and Efficient Pulse-Width Modulation
---

# Bresenham and Efficient Pulse-Width Modulation

## Introduction

I've recently been working on a telescope clock-drive project. The idea is that
I attach a motor to a telescope to make it turn at the same rate as the earth
so that long exposure photographs don't come out blurred. I'll (hopefully)
post more on this soon, but in this post I'll discuss an algorithm I stumbled
across while designing a DAC as part of the clock-drive project.

## The Problem

My problem was to generate an output voltage to use as a reference for driving
the DC motor attached to the telescope. The voltage would be determined by some
logic in an AVR on the control board, and a low-pass RC filter would be
attached to one of the digital output pins. A timer would be running on the AVR
triggering an interrupt service routine (ISR) at regular intervals. The timer
ISR would set the state of the output pin either high or low in order to attain
the required output voltage after the filter stage. This post discusses the
algorithm to use in the ISR.

## The Naive Solution

Before I discuss my algorithm, let's look at the naive scheme for generating a
PWM signal:

{% highlight python %}
P = 20     # Number of interrupts in a PWM period.
T = 32     # Number of interrupts in a PWM period where the output is 1.
phase = 0  # Current phase.
def timer_interrupt():
    if phase < T:
        output = 1
    else:
        output = 0
    if phase < T - 1:
        phase += 1
    else:
        phase = 0

{% endhighlight %}

...and here's the result, for `P = 32` and `T = 20`.

![Naive plot](/assets/efficient-pwm/naive.svg)

The green line is the unfiltered output, the red line is the filtered output
(with an RC time period of 16) and the blue line is the target voltage (`20. /
32 == 0.625`).

As expected the filtered curve follows the green curve, according to the
equations of capacitor discharge in an RC circuit.

Note that there are lots of points where the ISR is invoked and the filtered
signal is below the target voltage, yet the output signal remains low, and
vice-versa. It would seem that a better algorithm would set the output high
when the filtered output is below the target voltage, and low when the filtered
output is above the target voltage.

## Something better

Intuitively, it would seem that an algorithm which seeks to maintain a running
average as close to the target voltage as possible would work well. That is,
generate a sequence \\( o_i \\) such that:

$$\frac{T}{P} - \sum_{i=0}^{N} \frac{o_i}{N}$$

is minimized for all \\( N \in \\mathbb{N} \\).

Let's give this a go:

{% highlight python %}
P = 20     # Number of interrupts in a PWM period.
T = 32     # Number of interrupts in a PWM period where the output is 1.
sum = 0    # Total number of 1's output so far.
time = 0
def timer_interrupt():
    if time > 0 and sum / time < T / P:
        output = 1
        sum += 1
    else:
        output = 0

    time += 1
{% endhighlight %}

...and here's the result, with the same parameters as the above plot:

![Efficient plot](/assets/efficient-pwm/efficient.svg)

Much better. Note how, once stabilized, whenever the ISR fires the output state
is adjusted to follow the target voltage. As a result the filtered signal
deviates much less from the target voltage.

However, there are a few problems with the above routine:

* Use of division. This isn't necessarily going to be feasible, or even
  possible on your MCU.
* Use of two variables. Again, this could be an issue on an embedded system
  where resources are right.
* Unbounded integers. `time` and `sum` will increase indefinitely, and will
  soon overflow.

## Optimizing

So what can we do? Well, firstly let's get rid of that division by multiplying
the condition by `P * time`:

{% highlight python %}
P = 20     # Number of interrupts in a PWM period.
T = 32     # Number of interrupts in a PWM period where the output is 1.
sum = 0    # Total number of 1's output so far.
time = 0
def timer_interrupt():
    if time > 0 and P * sum < T * time:
        output = 1
        sum += 1
    else:
        output = 0

    time += 1
{% endhighlight %}

The `time > 0 and ` check is now redundant, so let's get rid of it:

{% highlight python %}
P = 20     # Number of interrupts in a PWM period.
T = 32     # Number of interrupts in a PWM period where the output is 1.
sum = 0    # Total number of 1's output so far.
time = 0
def timer_interrupt():
    if P * sum < T * time:
        output = 1
        sum += 1
    else:
        output = 0

    time += 1
{% endhighlight %}

Still though, multiplication is relatively expensive. Let's perform a change of
variables to eliminate it:

* `sum2 == P * sum`
* `time2 == T * time`

{% highlight python %}
P = 20     # Number of interrupts in a PWM period.
T = 32     # Number of interrupts in a PWM period where the output is 1.
sum2 = 0
time2 = 0
def timer_interrupt():
    if sum2 < time2:
        output = 1
        sum2 += P
    else:
        output = 0

    time2 += T
{% endhighlight %}

This is good. But if you look closely the output of the routine depends only on
`sum2 - time2`. So let's trim the code down to just one variable, `h = sum2 -
time2`:

{% highlight python %}
P = 20     # Number of interrupts in a PWM period.
T = 32     # Number of interrupts in a PWM period where the output is 1.
h = 0
def timer_interrupt():
    if h < 0:
        output = 1
        h += P
    else:
        output = 0

    h -= T
{% endhighlight %}

Now substitute `h2 == h + T` in a bid to stop underflow, and move the
subtraction into the else block to avoid overflow:

{% highlight python %}
P = 20     # Number of interrupts in a PWM period.
T = 32     # Number of interrupts in a PWM period where the output is 1.
h2 = T
def timer_interrupt():
    if h2 < T:
        output = 1
        h2 += P - T
    else:
        output = 0
        h2 -= T
{% endhighlight %}

Some basic analysis shows that `h2` must be greater than or equal to `0`, but
less than or equal to `P`. As such, a full 8-bits of DAC accuracy can be
obtained with a single 8-bit variable (when `P = 256`), with a relatively low
RC time-constant.

## Bresenham

Wait a minute, this looks familiar:

{% highlight python %}
def bresenham(x0, x1, y0, y1):
    x, y = x0, y0
    dx = x1 - x0
    dy = y1 - y0
    y_err = 0

    while x <= x1:
        draw_pixel(x, y)
        y_err += dy
        if y_err > dx:
            y_err -= dx
            y++
        x++
{% endhighlight %}

This is a slightly simplified [Bresenham's Line
Algorithm](http://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm) for the
octant \\( \delta x, \delta y > 0 \land \delta x > \delta y \\). Note the
correspondence between variables:

* `h2` corresponds with `y_err`.
* `T` corresponds with `dx`.
* `P` corresponds with `dy`.
* `x` corresponds with `time`.
* `y` corresponds with `sum`.

This isn't too surprising when you notice the formula the algorithm was derived
from seeks to approximate the gradient of the line running through the origin
to \\( (\sum o_i, N) \\) as \\( \frac{T}{P} \\).

Just for fun let's plot the output of the algorithm (incrementing `x` at each
step, and incrementing `y` at each positive output) against the line running
though \\( \frac{T}{P} \\):

![Line plot](/assets/efficient-pwm/bresenham.svg)

## Conclusion

The new PWM algorithm is useful if both of the following are true:

* Your timer interrupt is constrained to run at a fixed interval. For example,
  if your timer is also used within the MCU for other periodic tasks.
* The timer interval cannot be set arbitrarily low. For example either because 
  the MCU is operating at a low clock frequency or there is CPU contention
  such that the ISR cannot complete before the next triggering.

If either of the above are false, then naive PCM can be used with a reduced
period. In the case where the timer period can be changed, it would be changed
to fire at alternating periods of `P` and `T - P`, flipping the output state
each time.

The main benefit of the new PWM algorithm is it can be coupled with an
RC-filter operating at a lower time constant to acheive a given voltage
stability. The knock-on benefits of this are:

* Lower output impedence.
* Faster convergence on the target voltage. (Important if your target voltage
  is changing.)

