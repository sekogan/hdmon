# Hard Disk Monitor

Monitors hard disk activities and spins down idle disks.

**BEWARE. This software is currently being tested. DO NOT USE if this notice is still here.**


## Motivation

[hd-idle](http://hd-idle.sourceforge.net/) is an excellent tool but it doesn't work well
on my system that has several HDDs in USB enclosures. These enclosures apparently
spin up disks almost immediately after they have been spun down. Not sure, but this is
the most plausible explanation that I came up with. Another problem is that if a disk
has been spun down by `hd-idle` it doesn't return its status anymore (for example
to `hdparm -C` command). So `smartd` service doesn't get status of spun down disks
and wakes them up. On the other hand I found that `hdparm -y` command spins down
my disks without any issues, except that spun down and rotating disks have
the same status ("standby").


## Features

- Monitors disk read/write activity.
- Spins down idle disks.
- Detects added/removed disks.
- Allows to use well known tools like `hdparm` to spin down disks.
- Doesn't rely on querying disk status.


## Limitations

- Does produce disk activities on system partition by writing messages to the system journal
  and executing shell commands. But it seems like everybody has system partitions on SSDs
  these days, so being completely "silent" might be not that important anymore.


## TODO

- Make "spin down" and "check up" functions generic.
- Periodically run SMART diagnostic tool for active disks.
- Experiment with different strategies to minimize number of spin up/spin down cycles.


## Installation

```
sudo pip3 install git+https://github.com/sekogan/hdmon.git
sudo hdmon-install
```

Edit `/etc/hdmon.yml` to your preference.

```
sudo systemctl daemon-reload
sudo systemctl enable hdmon
sudo systemctl start hdmon
```

To uninstall:

```
sudo systemctl stop hdmon
sudo systemctl disable hdmon
sudo hdmon-uninstall
sudo pip3 uninstall hdmon
sudo rm /etc/hdmon.yml
```


## Credits

Inspired by:

- [hd-idle](http://hd-idle.sourceforge.net/)
- [another hd-idle](https://github.com/adelolmo/hd-idle)
- [amdgpu-fan](https://github.com/chestm007/amdgpu-fan)
