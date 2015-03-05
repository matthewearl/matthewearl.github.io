---
layout: default
title: Efficient Pulse-Width Modulation
---

# Efficient Pulse-Width Modulation

## Introduction

I've recently been working on a telescope clock-drive project. I'll (hopefully)
post more on this in the future, but in this post I'll discuss an algorithm I
stumbled across for performing pulse-width modulation.

My algorithm uses as much memory as the naive approach, but with much faster
convergence.  

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

Before I discuss my algorithm, let's look at a naive scheme for generating a
PWM signal:

{% highlight python %}
P = 0      # Number of interrupts in a PWM period.
T = 0      # Number of interrupts in a PWM period where the output is 1.
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

## An Ideal Implementation

$$\lim_{N \to \infty}\sum_{i=0}^{N} \frac{o_i}{N} = \frac{T}{P}$$

## Other applications

