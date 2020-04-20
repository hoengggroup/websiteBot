# -*- coding: utf-8 -*-

import pushbullet

import sys


filterset = {
"17.515.2",
"17.515.3",
"515",
"17.509.2", 
"17.509.3",
"13.619.2"}


def send_push(header, msg):
    pb = pushbullet.Pushbullet("***REMOVED***")
    pb.push_note(header, msg)


def process_bullet(roomfield):
    try:
        pb = pushbullet.Pushbullet("***REMOVED***")
        for filter in filterset:
            for room in roomfield:
                if filter == room.text:
                    pbpush = pb.push_note("!!", "ON!!LINE!!!")
                    # NOT desired roomfield.remove(room)
    except:
        # DON'T DO ANYTHING
        # print(str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
        pass
