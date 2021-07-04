# IMGeotaggerV3, xplat edition

Possibly the only geotagger that works in Linux and Mac!

Very simple project, heavily inspired in pictag: you get a list of pictures and a map. Select a location in the map then click "tag" to record the location in your picture's exif data.

Other programs (Pictag, IMGeotagger, Digikam) should be able to do the same but they are either broken, unsupported or use a crappy map (because of licensing, of course). IMGeotaggerV3 uses a good map provider, and it seems to work in Ubuntu and Mac. Not sure if this breaks the service TOS or not, but if it does please let me know. IMGeotaggerV3 is a copy of IMGeotaggerV2, but ported for a newer version of CEFPython and using wx instead of GTK. This should make it run in any platform supported by CEF and wx (Windows, Linux and OSX). I've only tested it in Linux and OSX.



# Running

You'll need to install pip, pipenv and python3 using whatever mechanism your platform requires. Then:

1. Clone this repo `https://github.com/nicolasbrailo/IMGeotaggerV2.git`
1. Install dependencies: `python3 -m pipenv install`
1. Fight to install pygtk. In Linux, `python3 -m pipenv install pygtk` should work. In Mac, you may need `brew install pygobject3 gtk+3`. In other platforms, you're on your own.
1. Run with ./run.sh (which just calls `python3 -m pipenv run python ./main.py`)


