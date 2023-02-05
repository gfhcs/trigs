# Trigs

Trigs is a Python package that controls media playback via simple hardware input devices ("triggers"). The idea is for a playlist of media files to be playing while the triggers pause/resume the playback or skip/repeat entries of the playlist.

Trigs is being developed for a simple on-stage performance: An actor hiding two small Bluetooth-based trigger devices in their costume is performing a pantomime act on stage. By using the trigger devices, the actor can synchronize the sound track with their performance. However, with minor modifications, Trigs can also be used for other scenarios, as it supports an arbitrary number of trigger devices and sound tracks.

Trigs is being developed for [Thunis](https://www.thunis.eu/).

The trigger devices supported by Trigs are tiny Bluetooth dongles, originally designed for remotely triggering the shutter of a smartphone camera (search "remote bluetooth shutter"). These dongles come in all shapes and (small) sizes, but the underlying electronics seems to often be the same. Trigs uses [evdev](https://python-evdev.readthedocs.io/en/latest/) to communicate with the triggers, as [demonstrated on YouTube](https://www.youtube.com/watch?v=ZKjA0RSlZSA).


Trigs controls [VLC media player](https://www.videolan.org/vlc/), but should easily be portable to other media player software, as it makes use of [playerctl](https://github.com/altdesktop/playerctl).

For simple graphical feedback, Trigs uses [tkinter](https://docs.python.org/3/library/tkinter.html).
