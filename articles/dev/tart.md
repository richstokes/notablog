---
title: "Tart Cheatsheet"
description: "Easy macOS VMs"
date: 2025-07-13
tags: [macos, vms, tart]
---

## Tart Cheatsheet

### Installation

```sh
brew install cirruslabs/cli/tart
```

### Pull an Image & Create a VM

```sh
tart clone ghcr.io/cirruslabs/macos-tahoe-base:latest tahoe-base
```

To download the vanilla macOS Golden Gate image and name the VM `gg`:

```sh
tart clone ghcr.io/cirruslabs/macos-golden-gate-vanilla:latest gg
```

See Tart's [VM image documentation](https://tart.run/quick-start/#vm-images) for other available images.

### Launch VM & Mount Apps Folder (Read-Only)

```sh
tart run --dir=MyApps:/Applications:ro tahoe-base
```

### Launch VM with Bridged Wi-Fi Networking

```sh
tart run --dir=MyApps:/Applications:ro --net-bridged=en0 tahoe-base
```
