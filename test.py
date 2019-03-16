import sys

try:
    raise Exception("hi")
except:
    print("An unknown exception has occured in the main loop. Error: ", sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2],"end")