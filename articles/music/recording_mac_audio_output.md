---
title: "Recording Mac audio out"
description: "Quick recording from logic+an audio source"
date: 2025-07-12
tags: [music, guitar, logic pro]
draft: false
---

## Scenario

You're playing guitar through Logic/Garage band, playing along with a backing track or other music and you want to record yourself playing guitar along with the background audio.

## How to

1. [Install backhole from here](https://existential.audio/blackhole/). It will set itself up as a virtual audio device on your mac. I use the 2-channel version
1. Open Audio Midi Setup (it's under Applications/Utlities)
1. Create Multi-Output Device
1. Select Blackhole plus the device you output audio to (likely an audio interface)
1. Tick the "Drift Correction" box
1. Right-click on your Multi-Output device and select Use This Device For Sound Output. Audio should now be playing through your speakers and through BlackHole.
1. Open Quicktime Player and choose New Movie Recording
1. For Microphone, select the Blackhole device
