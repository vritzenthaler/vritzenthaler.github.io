---
title: Are two simulations better than one?
date: 2026-05-12
ref: two-simulations
summary: A seductive intuition about meshes, a small 1D experiment, and the lesson it taught me about the difference between information and accuracy.
image: /assets/images/blog/two-simulations.webp
image_alt: Blue ink sketch of a curve approximated by two offset meshes, one drawn with solid dots, the other with terracotta circles.
image_caption: Two meshes that never touch, one solution to approximate.
published: true
---

A few months ago, an idea kept me up longer than planned. It had everything going for it: simple, elegant, and slightly subversive with respect to what we learn in numerical analysis.

## Physical laws don’t care about shape

When you write Faraday’s law on a face, it holds whatever the shape of that face: square, twisted, triangular. It only depends on its boundary, and even the connectivity of that boundary barely matters. This is what we call a *topological* law.

Take this remark seriously and you can see physical quantities as things you evaluate on geometric entities: vertices, edges, faces, cells. A mesh is then just a particular choice of entities, a bit like choosing where to place sensors in a lab.

## The intuition

In a lab, if I double the number of sensors without ever placing two at the same spot, I double the information I have about the field I am measuring.

So why not do the same in simulation? Two meshes that coincide nowhere, two independent simulations, and a field known “twice as well”. Yet classical theory is clear: the error is measured by the mesh size $$h$$,

$$
\| u - u_h \| \leq C \, h,
$$

and two simulations with the same mesh size remain $$\mathcal{O}(h)$$. Nothing gained, on paper.

One of the two views had to be wrong. I was secretly hoping it would be the classical one.

## The experiment

Rather than theorising for weeks, I took the simplest possible case: the equation $$-u'' = f$$ on the segment $$[0, 1]$$. Two offset meshes, two approximate solutions, then a form that coincides with each of them on its own points.

The result: in the middle of the segment, the scheme gets it right. But as soon as I move the evaluation point, the value does not move the way it should. The physical law is satisfied on each of the two meshes… and yet combining them gets no closer to the exact solution than a single finer mesh.

> I really had two independent measurements. I did not have half the error.

## Where was the mistake?

It took me a while to see it. The topological part of the model, the one that says how quantities relate to each other, is exact. But a numerical scheme also needs a *metric* part: lengths, areas, the way the medium links a flux to a circulation. That is where the error is born.

And that error has nothing to do with the number of entities you use. It depends on the shape of the cells. Adding a second mesh adds topological information, but does not fix the metric of either one.

I like to put it this way: topology tells you which paths are possible, the metric tells you how you travel them. Multiplying paths does not make each step more accurate.

## What I take away

- **Information is not accuracy.** Two datasets only combine well if you know where the error of each comes from.
- **A small experiment beats a long theory.** The 1D case put my intuition to the test in a single afternoon.
- **A wrong idea can be fertile.** It forced me to separate clearly what, in a scheme, belongs to structure and what belongs to measurement.

The question is still open, by the way: are there metrics for which two simulations really are better than one? I have no idea. But I now know where to look.
