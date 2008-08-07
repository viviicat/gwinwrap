#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Author: Gavin Langdon (fusioncast@gmail.com)
# Copyright (C) 2008 Gavin Langdon

import sys, subprocess, os, string
try:
 	import pygtk
  	pygtk.require("2.0")
except:
  	pass
try:
	import gtk
  	import gtk.glade
except:
	sys.exit(1)

from optparse import OptionParser

class gwinwrap:
	"""This is a GUI to xwinwrap...gwinrwap!"""

	print "\n== GWINWRAP VERSION 0.1-SVN -- Have fun with your animated desktop! =="
	def __init__(self):
		
		### ADJUSTABLE VARIABLES -- It won't hurt to edit these a bit
		# Directory for screensavers
		self.XSSDir = "/usr/lib/xscreensaver/" 
		# The nice command
		self.nice = "nice -n 15 "
		### END AJUSTABLE VARIABLES ###

		# Set the Glade file
		self.gladefile = "gwinwrap.glade"
		self.gladeXML = gtk.glade.XML(self.gladefile)

		# Initialize some program variables
		self.PreviewShowing = False
		self.selectedSaver = ""

		# Create our dictionary and connect it
		dic = {"on_Main_destroy" : self.Quit
			, "on_Close_clicked" : self.Quit 
			, "on_Apply_clicked" : self.Apply
			, "on_Refresh_clicked" : self.Refresh
			, "on_EffectList_cursor_changed" : self.ListItemChange
			, "on_Stop_clicked" : self.Stop
			, "on_Speed_value_changed" : self.SpeedChange
			, "on_Opacity_value_changed" : self.OptionChange
			, "on_CPUPriority_toggled" : self.OptionChange
			, "on_SpeedCheckBox_toggled" : self.ShowPreview
			, "on_XscreensaverClose_clicked" : self.Quit
			, "on_XwinwrapClose_clicked" : self.Quit
		}		
		self.gladeXML.signal_autoconnect(dic)

		# Check for Xwinwrap
		if not self.xwinwrap_installed():
			self.NoXwinwrap.show()
			print " ** You don't have Xwinwrap installed!"

	#	if startOptions.args:
			

		# Get the widgets we need
		self.Main = self.gladeXML.get_widget("Main")
		self.SpeedCheckBox = self.gladeXML.get_widget("SpeedCheckBox")
		self.Speed = self.gladeXML.get_widget("Speed")
		self.Opacity = self.gladeXML.get_widget("Opacity")
		self.Stop = self.gladeXML.get_widget("Stop")
		self.Apply = self.gladeXML.get_widget("Apply")
		self.Refresh = self.gladeXML.get_widget("Refresh")
		self.SpeedHBox = self.gladeXML.get_widget("SpeedHBox")
		self.SettingsHBox = self.gladeXML.get_widget("SettingsHBox")
		self.WelcomeBox = self.gladeXML.get_widget("WelcomeBox")
		self.Preview = self.gladeXML.get_widget("Preview")
		self.NoXscreensavers = self.gladeXML.get_widget("NoXscreensavers")
		self.NoXwinwrap = self.gladeXML.get_widget("NoXwinwrap")
		self.EffectList = self.gladeXML.get_widget("EffectList")
		self.Preview = self.gladeXML.get_widget("Preview")
		self.xscreensaverArgLabel = self.gladeXML.get_widget("xscreensaverArgLabel")
		self.CPUPriority = self.gladeXML.get_widget("CPUPriority")

		# Enable stopping the already running xwinwrap process
		if self.xwinwrap_running():
			self.Stop.set_sensitive(True)
			if startOptions.options.stop:
				self.KillXwinwrap()
				if not startOptions.args and not startOptions.options.window:
					quit()
		if startOptions.options.stop == True and not startOptions.args and not startOptions.options.window:
			print "No need to stop anything, nothing's running.\n"
			quit()

		self.SetUpTreeView()

		if startOptions.args:
			self.selectedSaver = startOptions.args[0]
			self.command = self.ComposeCommand("all")
			self.RunEffect()
			if not startOptions.options.window:
				quit()

		self.Main.show()

	def ShowPreview(self, widget):
		'Shows a preview of the selected xscreensaver within a gtk.Socket'
		self.Apply.set_sensitive(True)
		self.CleanUpPreview()
		self.SetUpSocket()
		self.SettingsHBox.set_sensitive(True)

		previewcommand = self.ComposeCommand("xscreensaver")

		self.previewShow = self.Run(previewcommand)
		self.PreviewShowing = True
		self.socket.show()

	def ApplyEffect(self, New=True):
		'If the effect is a new one, compose a new xwinwrap command. Then quit any currently running instances, then(finally), run the xwinwrap command.'
		if New:
			self.command = self.ComposeCommand()
			self.Refresh.set_sensitive(True)
		self.RunEffect()

	def RunEffect(self):
		self.KillXwinwrap()
		print " * GWINWRAP ** Running: " + self.command
		self.Run(self.command)

	def Refresh(self, widget):
		self.ApplyEffect(False)

	def Apply(self, widget):
		self.Apply.set_sensitive(False)
		self.Stop.set_sensitive(True)
		self.ApplyEffect()

	def Stop(self, widget):
		self.Stop.set_sensitive(False)
		self.Apply.set_sensitive(True)
		self.Refresh.set_sensitive(False)
		self.KillXwinwrap()

	def ListItemChange(self, widget):
		'Get the new label, check if it s the same as the old, and if not change the preview and buttons accordingly. Also, check for speed now so we don t need to so frequently.'
		oldrow = self.selectedSaver
		selectedRow, locInRow = self.EffectList.get_selection().get_selected()
		if locInRow:
			self.selectedSaver = selectedRow.get_value(locInRow,0)
			if oldrow != self.selectedSaver:
				self.Apply.set_sensitive(True)
				self.UsingSpeed = self.UsingSpeedCheck()
				self.ShowPreview(widget)

	def GetScreenSavers(self):
		'Get a list of the screensavers in the xscreensaver directory'
		self.ScreenSavers = os.listdir(self.XSSDir)
		if len(self.ScreenSavers) == 0:
			self.NoXscreensavers.show()
			print "You don't have any Xscreensavers in %s" %self.XSSDir
		self.ScreenSavers.sort()
		for item in self.ScreenSavers:
			self.liststore.append([item])

	def CleanUpPreview(self):
		'Clean up the old preview/welcome note in preparation for the new preview'
		if self.PreviewShowing:
			self.socket.destroy()
			self.Run("kill %s" %self.previewShow.pid)
		else:
			self.WelcomeBox.destroy()
			self.Preview.show()

	def OptionChange(self,widget):
		'This is in order to save changes like opacity'
		self.Apply.set_sensitive(True)

	def KillXwinwrap(self):
		if self.xwinwrap_running():
			print " * GWINWRAP ** Killing current xwinwrap process."
			self.Run("killall xwinwrap")

	def xwinwrap_running(self):
		'Use pidof and pgrep to determine if xwinwrap is running'
		if subprocess.call(['pidof','xwinwrap'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0 or subprocess.call(['pgrep','xwinwrap'], stdout=subprocess.PIPE) == 0:
			return True

	def xwinwrap_installed(self):
		'Use which to determine if xwinwrap is installed'
		if subprocess.call(['which','xwinwrap'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
			return True

	def SpeedChange(self, widget):
		'Checks the option to customize speed when the speed is changed from the slider'
		if not self.SpeedCheckBox.get_active():
			self.SpeedCheckBox.set_active(True)
		self.ShowPreview(widget)

	def UsingSpeedCheck(self):
		'Check the selected screensaver for a --speed option by reading its --help output'
		if string.find(subprocess.Popen(["%s%s" %(self.XSSDir,self.selectedSaver),"--help"], stdout=subprocess.PIPE, stderr=open(os.devnull, 'w')).communicate()[0],"--speed") >= 0:
			return True
		else: return False

	def SetUpSpeedList(self):
		'Custom values in order to make the speed-affected screensavers slower. Roughly merges the --maxfps option with the --speed option.'
		if self.SpeedCheckBox.get_active():
			speedvalue = self.Speed.get_value()
			speedStr = ""
			if speedvalue >= 5.0:
				speed = speedvalue - 5
			else: 
				speed = 1
				fps = speedvalue + 10
				fpsArg = " --maxfps "
				speedStr = "%s%i"%(fpsArg,fps)
			speedStr = speedStr + " --speed %i" %speed
			self.sscommand = self.sscommand + speedStr

	def SetUpTreeView(self):
		self.EffectList.insert_column_with_attributes(-1,"Effect",gtk.CellRendererText(),text=0)

		self.liststore = gtk.ListStore(str)

		self.GetScreenSavers()
		self.EffectList.set_model(self.liststore)

	def SetUpSocket(self):
		'Attach the socket and color it black to avoid flashes when changing previews'
		self.socket = gtk.Socket()
		self.Preview.add(self.socket)
 		self.black = gtk.gdk.Color(red=0, green=0, blue=0, pixel=0)
		self.socket.modify_bg(gtk.STATE_NORMAL,self.black)

	def ComposeCommand(self,mode="xwinwrap"):
		'Create the command to use when launching either xwinwrap or the previews'
		baseCommand = "xwinwrap -ni -argb -fs -s -st -sp -b -nf -o "
		if mode == "xwinwrap":
			opacity = float(self.Opacity.get_value())			
			opacity = opacity/100		
	
			xscreensaverArgs = " " + self.xscreensaverArgLabel.get_text()
					
			if gtk.CheckButton.get_active(self.CPUPriority):
				baseCommand = self.nice + baseCommand
			command = baseCommand + "%f"%opacity + " -- " + self.sscommand + xscreensaverArgs + " -window-id WID"

			return command

		elif mode == "xscreensaver":

			self.sscommand = "%s%s"%(self.XSSDir,self.selectedSaver)
	
			if self.UsingSpeed:
				self.SpeedHBox.set_sensitive(True)
				self.SetUpSpeedList()

			else: self.SpeedHBox.set_sensitive(False)

			command = self.sscommand + " -window-id %i"%self.socket.window.xid
			
			command = self.nice + command

			return command

		elif mode == "all":
			return baseCommand + " 1 -- %s%s -window-id WID" %(self.XSSDir,self.selectedSaver)
			

	def Run(self,command):
		'Change the command (in a string) into a list for subprocess, Launch quietly, and return the object for PID referencing'
		command = " " + command + " "
		command = command[1:-1].split()

		popen_object = subprocess.Popen(command, stdout=open(os.devnull, 'w'))

		return popen_object


	def Quit(self, widget):
		self.CleanUpPreview()
		print "\nThis is Gwinwrap saying, \"Sayonara!\"\n"
		gtk.main_quit()

class startOptions:
	"""This is a separate class which checks the startup command for options."""
	parser = OptionParser(usage="usage: %prog SCREENSAVER [options]",description="Thanks for trying %prog, a gui for xwinwrap. If you want, you can use %prog to run a screensaver with xwinwrap and default commands by adding it after ./%prog. For example: './%prog glmatrix' will start the glmatrix screensaver. This option disables the rest of the interface.")

	parser.add_option("-w", "--window", action="store_true", dest="window", default=False,
			help="Show the interface even if running a screensaver directly.")
	parser.add_option("-s", "--stop", action="store_true", dest="stop", default=False,
			help="An 'off' button. Quits any xwinwrap instances, then quits itself.")
	
	options, args = parser.parse_args()

		
if __name__ == "__main__":
	run = gwinwrap()
	gtk.main()
