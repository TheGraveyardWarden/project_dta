#!/usr/bin/python

from utils import *
from core import *

import logging

#logging.basicConfig(level=logging.DEBUG)

OUT_DIR = "/home/ricky/dta_out"

DEBUG = True

import time

track = SCTrack.from_url("https://soundcloud.com/drewthearchitect/anothertear")
start = time.perf_counter()
handle = track.download_parallel(OUT_DIR, 10, 10)
handle.join_all()
end = time.perf_counter()
elapsed = end - start

print(elapsed)

import sys
sys.exit(0)

user = SCUser("drewthearchitect")
for track in user.get_tracks(5):
    track.download(OUT_DIR)
