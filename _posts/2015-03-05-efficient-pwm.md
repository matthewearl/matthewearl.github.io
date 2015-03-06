---
layout: default
title: Efficient Pulse-Width Modulation
---

# Efficient Pulse-Width Modulation

## Introduction

I've recently been working on a telescope clock-drive project. I'll (hopefully)
post more on this soon, but in this post I'll discuss an algorithm I stumbled
across for implementing a DAC with pulse-width modulation.

My algorithm produces a much more stable output than the naive approach for the
same amount of MCU resource usage.

## The Problem

My problem was to generate an output voltages to use as a reference for driving
the DC motor attached to the telescope. The voltage would be determined by some
logic in an AVR on the control board. The output voltage would not have to
change rapidly.

My plan was to attach a low-pass RC filter to one of the digital output pins,
and set up one of the AVR's timers to regularly fire. The timer ISR would set
the state of the output pin either high or low in order to attain the required
output voltage after the filter stage. This post discusses the algorithm to use
in the ISR.

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

Note that there are lots of points where the ISR is invoked and the filtered
signal is below the target voltage, yet the output signal remains low, and
vice-versa. 

## Something better

Let's derive an algorithm which seeks to maintain a running average as close to
the target voltage as possible. That is, generate a sequence \\( o_i \\) such
that:

$$\frac{T}{P} - \sum_{i=0}^{N} \frac{o_i}{N}$$

is minimized for all \\( N \in \\mathbb{N} \\).

Here's a first stab:

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

Much better! Note how the filtered signal deviates less from the target voltage
(after stabilization).

The only problem is one of efficiency. There are a few problems with the above
routine:

* Use of division. This isn't necessarily going to be feasible, or even
  possible on your embedded system.
* Use of two variables. Again, this could be an issue on an embedded system.
* Unbounded integers. `time` and `sum` will increase indefinitely.

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

Brilliant. Still though, multiplication is kind of expensive. Let's perform a
change of variables to eliminate it:

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

## Caveats

The above assumes the routine can only be invoked at a pre-determined regular
interval. This won't always be the case. If it's not the naive approach becomes
more attractive: Simply program the timer to fire exactly when the next
transition is due to occur.
