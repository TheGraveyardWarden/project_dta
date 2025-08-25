#!/usr/bin/python

from utils import *
from core import *

import logging

#logging.basicConfig(level=logging.DEBUG)

OUT_DIR = "/home/ricky/dta_out"

DEBUG = True

track = SCTrack.from_url("https://soundcloud.com/drewthearchitect/sofarnogood")
track.download(OUT_DIR)

import sys
sys.exit(0)

user = SCUser("drewthearchitect")
for track in user.get_tracks(5):
    track.download(OUT_DIR)
