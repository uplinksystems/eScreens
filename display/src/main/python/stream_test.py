#!/usr/bin/env python
import subprocess
import sys
import time

if __name__ == "__main__":
    #streamlink -np "omxplayer --adev hdmi" https:/.twitch.tv/drdisrespect best
    proc = subprocess.Popen(['streamlink', '-np', 'omxplayer --adev hdmi', 'https://twitch.tv/drdisrespect', 'best'], shell=False)
    time.sleep(30)
    proc.kill()