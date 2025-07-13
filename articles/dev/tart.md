
> Tart Cheatsheet

### Pull an image / create the VM
tart clone ghcr.io/cirruslabs/macos-tahoe-base:latest tahoe-base


### Launch while mounting apps folder in VM
tart run --dir=MyApps:/Applications:ro tahoe-base
