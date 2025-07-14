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

### Launch VM & Mount Apps Folder (Read-Only)

```sh
tart run --dir=MyApps:/Applications:ro tahoe-base
```

### Launch VM with Bridged Wi-Fi Networking

```sh
tart run --dir=MyApps:/Applications:ro --net-bridged=en0 tahoe-base
```
