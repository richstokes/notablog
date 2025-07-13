
> Tart Cheatsheet

### Install
brew install cirruslabs/cli/tart


### Pull an image / create the VM
tart clone ghcr.io/cirruslabs/macos-tahoe-base:latest tahoe-base


### Launch while mounting apps folder in VM
tart run --dir=MyApps:/Applications:ro tahoe-base


### If you want it to share your wifi network
tart run --dir=MyApps:/Applications:ro --net-bridged=en0 tahoe-base
