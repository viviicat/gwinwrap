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

class gwinwrap:
	"""This is a GUI to xwinwrap...gwinrwap!"""

	print "\n == GWINWRAP VERSION 0.1-SVN -- Have fun with your animated desktop! ==\n"
	def __init__(self):
		
		### ADJUSTABLE VARIABLES -- It won't hurt to edit these a bit
		# Directory for screensavers
		self.XSSDir = "/usr/lib/xscreensaver/" 
		# The nice command
		self.nice = "nice -n 15 "
		### END AJUSTABLE VARIABLES ################################

		# Set the Glade file
		self.gladefile = "gwinwrap.glade"
		self.main = gtk.glade.XML(self.gladefile)

		# Initialize some program variables
		self.PreviewShowing = False
		self.selectedRowValue = ""
			
		# Create our dictionary and connect it
		dic = {"on_mainWindow_destroy" : self.Quit
			, "on_Close_clicked" : self.Quit 
			, "on_Apply_clicked" : self.Apply
			, "on_Refresh_clicked" : self.Refresh
			, "on_EffectList_cursor_changed" : self.ListItemChange
			, "on_Stop_clicked" : self.Stop
			, "on_speed_value_changed" : self.SpeedChange
			, "on_Opacity_value_changed" : self.OptionChange
			, "on_CPUPriority_toggled" : self.OptionChange
			, "on_SpeedCheckBox_toggled" : self.ShowPreview
			, "on_XscreensaverClose_clicked" : self.Quit
			, "on_XwinwrapClose_clicked" : self.Quit
		}		
		self.main.signal_autoconnect(dic)

		# Check for Xwinwrap
		if not self.xwinwrap_installed():
			self.NoXwinwrap = self.main.get_widget("NoXwinwrap")
			self.NoXwinwrap.show()
			print " ** You don't have Xwinwrap installed!"

		# Get the widgets we need
		self.SpeedCheckBox = self.main.get_widget("SpeedCheckBox")
		self.speed = self.main.get_widget("speed")
		self.Opacity = self.main.get_widget("Opacity")
		self.Stop = self.main.get_widget("Stop")
		self.Apply = self.main.get_widget("Apply")
		self.Refresh = self.main.get_widget("Refresh")
		self.speedHBox = self.main.get_widget("speedHBox")
		self.SettingsHBox = self.main.get_widget("SettingsHBox")

		# Enable stopping the already running xwinwrap process
		if self.xwinwrap_running():
			self.Stop.set_sensitive(True)	

		self.SetUpTreeView()

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
		oldrow = self.selectedRowValue
		selectedRow, locInRow = self.EffectList.get_selection().get_selected()
		self.selectedRowValue = selectedRow.get_value(locInRow,0)
		if oldrow != self.selectedRowValue:
			self.Apply.set_sensitive(True)
			self.UsingSpeed = self.UsingSpeedCheck()
			self.ShowPreview(widget)

	def GetScreenSavers(self):
		'Get a list of the screensavers in the xscreensaver directory'
		self.ScreenSavers = os.listdir(self.XSSDir)
		if len(self.ScreenSavers) == 0:
			self.NoXscreensavers = self.main.get_widget("NoXscreensavers")
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
			self.WelcomeBox = self.main.get_widget("WelcomeBox")
			self.Preview = self.main.get_widget("Preview")

			self.WelcomeBox.destroy()
			self.Preview.show()

	def OptionChange(self,widget):
		'This is in order to save changes like opacity'
		self.Apply.set_sensitive(True)

	def KillXwinwrap(self):
		if self.xwinwrap_running():
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
		if string.find(subprocess.Popen(["%s%s" %(self.XSSDir,self.selectedRowValue),"--help"], stdout=subprocess.PIPE, stderr=open(os.devnull, 'w')).communicate()[0],"--speed") >= 0:
			return True
		else: return False

	def SetUpSpeedList(self):
		'Custom values in order to make the speed-affected screensavers slower. Roughly merges the --maxfps option with the --speed option.'
		if self.SpeedCheckBox.get_active():
			speedvalue = self.speed.get_value()
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
		self.EffectList = self.main.get_widget("EffectList")
		self.EffectList.insert_column_with_attributes(-1,"Effect",gtk.CellRendererText(),text=0)

		self.liststore = gtk.ListStore(str)

		self.GetScreenSavers()
		self.EffectList.set_model(self.liststore)

	def SetUpSocket(self):
		'Attach the socket and color it black to avoid flashes when changing previews'
		self.Preview = self.main.get_widget("Preview")
		self.socket = gtk.Socket()
		self.Preview.add(self.socket)
 		self.black = gtk.gdk.Color(red=0, green=0, blue=0, pixel=0)
		self.socket.modify_bg(gtk.STATE_NORMAL,self.black)

	def ComposeCommand(self,mode="xwinwrap"):
		'Create the command to use when launching either xwinwrap or the previews'
		if mode == "xwinwrap":
			opacity = float(self.Opacity.get_value())			
			opacity = opacity/100		
	
			self.xscreensaverArgLabel = self.main.get_widget("xscreensaverArgLabel")
			xscreensaverArgs = self.xscreensaverArgLabel.get_text()
	
			baseCommand = "xwinwrap -ni -argb -fs -s -st -sp -b -nf -o %f -- " %opacity
					
			self.CPUPriority = self.main.get_widget("CPUPriority")
			if gtk.CheckButton.get_active(self.CPUPriority):
				baseCommand = self.nice + baseCommand
			command = baseCommand + self.sscommand + xscreensaverArgs + " -window-id WID"

			return command

		elif mode == "xscreensaver":

			self.sscommand = "%s%s"%(self.XSSDir,self.selectedRowValue)
	
			if self.UsingSpeed:
				self.speedHBox.set_sensitive(True)
				self.SetUpSpeedList()

			else: self.speedHBox.set_sensitive(False)

			command = self.sscommand + " -window-id %i"%self.socket.window.xid
			
			command = self.nice + command

			return command

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

		
if __name__ == "__main__":
	run = gwinwrap()
	gtk.main()
