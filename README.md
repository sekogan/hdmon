# Hard Disk Monitor

Monitors hard disk activities and spins down idle disks.

**BEWARE. This software is currently being tested. DO NOT USE if this notice is still here.**


## Motivation

[hd-idle](http://hd-idle.sourceforge.net/) is excellent but it doesn't work well
on my system that has several HDDs in USB enclosures. These enclosures apparently
spin up disks almost immediately after they have been spun down. Not sure, but this is
the most plausible explanation that I came up with. Another problem is that if a disk
has been spun down by `hd-idle` it doesn't return its status anymore (for example
to `hdparm -C` command). So `smartd` service doesn't get status of spun down disks
and wakes them up. On the other hand I found that `hdparm -y` command spins down
my disks without any issues, except that spun down and rotating disks have
the same status ("standby").

So the idea of hdmon was to write a service that can monitor disk activities
and spin down the disks without querying their status. Other design goals were:

- rely on well known tools like `hdparm` to spin down disks;
- periodically run SMART diagnostic tools when a disk is active (TODO);
- experiment with different strategies to minimize number of spin up/spin down cycles (TODO).

Note that unlike `hd-idle` `hdmon` produces some disk activities on its own, by writing
messages to the system journal and executing shell commands. But it seems like everybody
has system partitions on SSDs these days, so being completely silent might be
not that important anymore.


## Installation

```
sudo pip3 install https://github.com/sekogan/hdmon
sudo hdmon-install
```

Edit `/etc/hdmon.yml` to your preference.

```
sudo systemctl enable hdmon
sudo systemctl start hdmon
```


## Credits

Inspired by:

- [hd-idle](http://hd-idle.sourceforge.net/)
- [another hd-idle](https://github.com/adelolmo/hd-idle)
- [amdgpu-fan](https://github.com/chestm007/amdgpu-fan)
