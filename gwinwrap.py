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

	def __init__(self):
			
		#Set the Glade file
		self.gladefile = "gwinwrap.glade"
		self.main = gtk.glade.XML(self.gladefile) 

		self.FirstTime = True
		self.useOld = False

		self.nice = ["nice","-n","15"]
			
		#Create our dictionary and connect it
		dic = {"on_mainWindow_destroy" : self.Quit
			, "on_Close_clicked" : self.Quit 
			, "on_Apply_clicked" : self.ApplyEffect 
			, "on_Refresh_clicked" : self.Refresh
			, "on_EffectList_cursor_changed" : self.ListItemChange
			, "on_Stop_clicked" : self.Stop
			, "on_speed_value_changed" : self.SpeedChange
			, "on_SpeedCheckBox_toggled" : self.ShowPreview
		}		
		self.main.signal_autoconnect(dic)

		self.SpeedCheckBox = self.main.get_widget("SpeedCheckBox")
		self.speed = self.main.get_widget("speed")
		self.Opacity = self.main.get_widget("Opacity")
		self.Stop = self.main.get_widget("Stop")
		self.Apply = self.main.get_widget("Apply")
		self.Refresh = self.main.get_widget("Refresh")

		self.speedHBox = self.main.get_widget("speedHBox")
		self.SSSettingsHBox = self.main.get_widget("SSSettingsHBox")

		if self.xwinwrap_running():
			self.Stop.show()

		else: self.Apply.show()	

		#Get the treeView from the widget Tree
		self.EffectList = self.main.get_widget("EffectList")
		self.EffectList.insert_column_with_attributes(-1,"Effect",gtk.CellRendererText(),text=0)
	
		#Create the listStore Model
		self.liststore = gtk.ListStore(str)

		self.GetScreenSavers()

		#Attach the model to the treeView
		self.EffectList.set_model(self.liststore)


#		self.RunPreview()

	def GetScreenSavers(self):
		self.ScreenSavers = os.listdir("/usr/lib/xscreensaver")
		self.ScreenSavers.sort()
		for item in self.ScreenSavers:
			self.liststore.append([item])
	
	def CleanUpPreview(self):
		if not self.FirstTime:
			self.socket.destroy()
			subprocess.Popen(["kill","%s" %self.previewShow.pid])

	def ListItemChange(self, widget):
		self.UsingSpeed = self.UsingSpeedCheck()
		self.ShowPreview(widget)


	def ShowPreview(self, widget):
		self.CleanUpPreview()
		self.SSSettingsHBox.set_sensitive(True)

		self.Preview = self.main.get_widget("Preview")
		self.socket = gtk.Socket()
		self.Preview.add(self.socket)
 		self.black = gtk.gdk.Color(red=0, green=0, blue=0, pixel=0)
		self.socket.modify_bg(gtk.STATE_NORMAL,self.black)

		self.sscommand = ["/usr/lib/xscreensaver/%s"%self.selectedRowValue]

		if self.UsingSpeed:
			self.speedHBox.set_sensitive(True)
			if self.SpeedCheckBox.get_active():
				speedvalue = self.speed.get_value()
				if speedvalue >= 5.0:
					speed = speedvalue - 5
					fpsArg = ""
					fps = 120
				else: 
					speed = 1
					fps = speedvalue + 10
					fpsArg = "--maxfps"
				speedList = [fpsArg,"%i"%fps,"--speed","%i"%speed]
				self.sscommand = self.sscommand + speedList
		else: self.speedHBox.set_sensitive(False)

		previewcommand = self.sscommand + ["-window-id","%i"%self.socket.window.xid]
		
		previewcommand = self.nice + previewcommand

		self.previewShow = subprocess.Popen(previewcommand)
		self.socket.show()
		self.FirstTime = False

		self.Stop.hide()
		self.Apply.show()
		self.Apply.set_sensitive(True)

	def Refresh(self, widget):
		self.useOld = True
		self.ApplyEffect(widget)

	def ApplyEffect(self, widget):
		if not self.FirstTime:
			self.KillXwinwrap()
			if not self.useOld:
				opacity = float(self.Opacity.get_value())			
				opacity = opacity/100		
				nice = []
				self.xscreensaverArgLabel = self.main.get_widget("xscreensaverArgLabel")
				xscreensaverArgs = self.xscreensaverArgLabel.get_text()
				#convert the xscreensaver arguments to items in a list
				xscreensaverArgs = " " + xscreensaverArgs + " "
				xscreensaverArgs = xscreensaverArgs[1:-1].split()
				command = ["xwinwrap","-ni","-argb","-fs","-s","-st","-sp","-b","-nf","-o","%f" %opacity,"--"]
				
				self.CPUPriority = self.main.get_widget("CPUPriority")
				if gtk.CheckButton.get_active(self.CPUPriority):
					self.command = self.nice + command
				self.command = self.command + self.sscommand + xscreensaverArgs + ["-window-id","WID"]
				self.Apply.hide()
				self.Stop.show()
				self.Refresh.set_sensitive(True)
			subprocess.Popen(self.command)
			self.useOld = False
					
		else: subprocess.Popen(["killall","xwinwrap"])

	def Ok(self, widget):
		self.ApplyEffect(self)
		self.Quit(widget)

	def Quit(self, widget):
		self.CleanUpPreview()
		print "Bye bye"
		gtk.main_quit()

	def Stop(self, widget):
		self.KillXwinwrap()
		self.Stop.hide()
		self.Apply.show()

	def KillXwinwrap(self):
		if self.xwinwrap_running():
			subprocess.Popen(['killall','xwinwrap'])

	def xwinwrap_running(self):
		'Use pidof and pgrep to determine if xwinwrap is running'
		if subprocess.call(['pidof','xwinwrap'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0 or subprocess.call(['pgrep','xwinwrap'], stdout=subprocess.PIPE) == 0:
			return True

	def ChangeTreeSort(self, widget):
		EffectCombo = self.main.get_widget("EffectCombo")
		listname = gtk.ComboBox.get_active_text(EffectCombo)
		print "Now showing the list of %s" %listname

	def SpeedChange(self, widget):
		if not self.SpeedCheckBox.get_active():
			self.SpeedCheckBox.set_active(True)
		self.ShowPreview(widget)

	def UsingSpeedCheck(self):
		selectedRow, locInRow = self.EffectList.get_selection().get_selected()
		self.selectedRowValue = selectedRow.get_value(locInRow,0)
		if string.find(subprocess.Popen(["/usr/lib/xscreensaver/%s" %self.selectedRowValue,"--help"], stdout=subprocess.PIPE, stderr=open(os.devnull, 'w')).communicate()[0],"--speed") >= 0:
			return True
		else: return False

		
if __name__ == "__main__":
	run = gwinwrap()
	gtk.main()
