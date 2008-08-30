#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import pickle, os

# This is just to be used to convert old presets.gwrp files so that they can work with new gwinwrap. Use if
# you get an error on trying to run an effect. This will not cause a problem if run on already converted files.

picklefile = "presets.gwrp"
string = ""
newlist = []

if os.path.exists(picklefile):
	pickleRead = open(picklefile,"r")
	settinglist = pickle.load(pickleRead)
	pickleRead.close()
	if len(settinglist[0]) == 10:
		string = "\n\n *** WARNING: it looks like you are either using a new %s or you have already converted it. This will overwrite any video's Loop or Sound settings to default.\n"%picklefile

	print "\nconverter.py will convert all presets in \"%s\".%s"%(picklefile,string)
	confirm = raw_input(">>> Continue? (y/n) > ")
	if confirm == "y" or confirm == "Y":
		print "\n"
		for index in range(len(settinglist)):
			newlist.append([])
			newlist[index] = settinglist[index][:8] + [True,False]
			print "Converted:", settinglist[index][0]

		pickleWrite = open(picklefile,"w")
		pickle.dump(newlist,pickleWrite)
		pickleWrite.close()

		print "\nDone. Your %s file is now ready to be used with the latest version of gwinwrap."%picklefile
	
	else:
		print "Quitting."

else:
	print "You do not have a %s file."%picklefile
