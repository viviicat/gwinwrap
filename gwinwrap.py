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










# DON'T FORGET TO ADD THE SECOND SCROLL TO CELL AND FINISH UP











import sys, subprocess, os, string
try:
 	import pygtk
  	pygtk.require("2.6")
except:
  	pass
try:
	import gtk
  	import gtk.glade
except:
	sys.exit(1)

from optparse import OptionParser
import pickle

class gwinwrap:
	"""This is a GUI to xwinwrap...gwinrwap!"""

	print "\n== GWINWRAP VERSION 0.1-SVN -- Have fun with your animated desktop! =="
	def __init__(self):
		
		### ADJUSTABLE VARIABLES -- It won't hurt to edit these a bit
		# Directory for screensavers
		self.XSSDir = "/usr/lib/xscreensaver/" 
		# The nice command
		self.nice = "nice -n 15 "
		# Pickle file
		self.pickle = "effects.gwrp"
		### END AJUSTABLE VARIABLES ###

		self.effectList = []
		self.descList = []
		self.isSaverList = []
		self.saverSpeedList = []
		self.filepathList = []
		self.opacityList = []
		self.priorityList = []
		self.argList = []

		self.settingLists = self.ReadFromDisk()

		# Set the Glade file
		self.gladefile = "gwinwrap.glade"
		self.gladeXML = gtk.glade.XML(self.gladefile)

		# Initialize some program variables
		self.PreviewShowing = False
		self.selectedSaver = ""
		self.selectedEffect = ""
		self.MakingNew = False
		self.CancelPressed = False

		# Create our dictionary and connect it
		dic = {"on_Main_destroy" : self.Quit
			, "on_Close_clicked" : self.Quit 
			, "on_Apply_clicked" : self.Apply
			, "on_Refresh_clicked" : self.Refresh
			, "on_SaverList_cursor_changed" : self.SaverListSelect
			, "on_EffectsList_cursor_changed" : self.EffectsListSelect
			, "on_Stop_clicked" : self.Stop
			, "on_Speed_value_changed" : self.SpeedChange
			, "on_Opacity_value_changed" : self.OptionChange
			, "on_CPUPriority_toggled" : self.OptionChange
			, "on_SpeedCheckBox_toggled" : self.ShowPreview
			, "on_XscreensaverClose_clicked" : self.Quit
			, "on_XwinwrapClose_clicked" : self.Quit
			, "on_xscreensaverArgLabel_changed" : self.OptionChange
			, "on_Remove_clicked" : self.Remove
			, "on_RemoveConfirm_response" : self.RemoveConfirmResponse
			, "on_New_clicked" : self.ShowNew
			, "on_Edit_clicked" : self.ShowEdit
			, "on_CancelEdit_clicked" : self.Cancel
			, "on_MovieChooser_file_set" : self.ChooseMovie
			, "on_EffectName_changed" : self.EffectSaveableCheck
			, "on_EffectDescr_changed" : self.EffectSaveableCheck
			, "on_SaveEdit_clicked" : self.SaveEdit
			, "on_Add_clicked" : self.Add
		}		
		self.gladeXML.signal_autoconnect(dic)

		# Check for Xwinwrap
		if not self.xwinwrap_installed():
			self.NoXwinwrap.show()
			print " ** You don't have Xwinwrap installed!"			

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
		self.SaverList = self.gladeXML.get_widget("SaverList")
		self.Preview = self.gladeXML.get_widget("Preview")
		self.xscreensaverArgLabel = self.gladeXML.get_widget("xscreensaverArgLabel")
		self.CPUPriority = self.gladeXML.get_widget("CPUPriority")
		self.RemoveConfirm = self.gladeXML.get_widget("RemoveConfirm")
		self.CustomFrame = self.gladeXML.get_widget("CustomFrame")
		self.EditFrame = self.gladeXML.get_widget("EditFrame")
		self.SSRadio = self.gladeXML.get_widget("SSRadio")
		self.MovieHBox = self.gladeXML.get_widget("MovieHBox")
		self.MovieRadio = self.gladeXML.get_widget("MovieRadio")
		self.SaveEdit = self.gladeXML.get_widget("SaveEdit")
		self.Add = self.gladeXML.get_widget("Add")
		self.EffectsList = self.gladeXML.get_widget("EffectsList")
		self.EffectName = self.gladeXML.get_widget("EffectName")
		self.NewHelpBox = self.gladeXML.get_widget("NewHelpBox")
		self.Remove= self.gladeXML.get_widget("Remove")
		self.EffectDescr = self.gladeXML.get_widget("EffectDescr")
		self.Edit = self.gladeXML.get_widget("Edit")

		self.InitializeMovieChooser()

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

		self.SetUpTreeView("effects")
		self.SetUpTreeView("screensavers")

		if startOptions.args:
			self.selectedSaver = startOptions.args[0]
			self.command = self.ComposeCommand("all")
			self.RunEffect()
			if not startOptions.options.window:
				quit()

		self.Main.show()

	def ShowEdit(self,widget):
		self.SaveEdit.show()
		self.Add.hide()
		self.SaveEdit.set_sensitive(False)
		self.ShowEditing()
		# Save a copy of the label for identification later
		self.OldName = self.EffectName.get_text()

	def Add(self,widget):
		self.Save(delold=False)

	def SaveEdit(self,widget):
		self.Save()

	def Save(self,delold=True):
		if not self.SpeedCheckBox.get_active:
			speed = 0
		else:
			speed = self.Speed.get_value()

		if self.SSRadio.get_active:
			usingsaver = True
			selectedrow, locInRow = self.SaverListSelection.get_selected()
			if locInRow:
				saver = selectedrow.get_value(locInRow,0)
		else:
			usingsaver = False
			saver = ""
			
		self.TempSettings = [self.EffectName.get_text(),self.EffectDescr.get_text(),usingsaver,speed,saver,
				self.Opacity.get_value(),self.CPUPriority.get_active(),self.xscreensaverArgLabel.get_text()]
		if delold:
			self.EffectManager(self.OldName,mode="remove")
		self.EffectManager(mode="add")
		self.GetSavedEffects()
		names = self.settingLists[0]
		sortednames = []
		for name in names:
			sortednames = sortednames + [name.lower()]
		sortednames.sort()
		tempsettings = self.TempSettings[0]
		nameindex = sortednames.index(tempsettings.lower())
		self.EffectsListSelection.select_path(nameindex)
		self.EffectsList.scroll_to_cell(nameindex,use_align=True)
		print " * Updated settings."
		self.CloseEditing()

	def ShowNew(self,widget):
		self.Add.show()
		self.SaveEdit.hide()
		self.ShowEditing()
		self.ResetSettings()
		self.CleanUpPreview()
		self.NewHelpBox.show()

	def ShowEditing(self):
		self.SettingsHBox.set_sensitive(True)
		self.CustomFrame.hide()
		self.EditFrame.show()

	def Cancel(self,widget):
		self.CancelPressed = True
		self.CleanUpPreview()
		self.EffectsListSelect(widget)
		self.CloseEditing()

	def CloseEditing(self):
		self.EditFrame.hide()
		self.CustomFrame.show()

		if self.is_selected(self.EffectsListSelection):
			self.EffectsListSelect(None)
		else:
			self.WelcomeBox.show()

		self.SettingsHBox.set_sensitive(False)

	def EffectSaveableCheck(self,widget):
		if self.is_selected(self.SaverListSelection) and self.EffectName.get_text() != "":
			self.Add.set_sensitive(True)
			self.SaveEdit.set_sensitive(True)

	def ChooseMovie(self,widget):
		self.MovieRadio.set_active(True)

	def Remove(self,widget):
		self.RemoveConfirm.show()

	def RemoveConfirmResponse(self,widget,response):
		self.RemoveConfirm.hide()
		if response==0:
			selectedRow, locInRow = self.EffectsListSelection.get_selected()
			if locInRow:
				self.EffectManager(selectedRow.get_value(locInRow,0),"remove")
			self.Remove.set_sensitive(False)
			self.GetSavedEffects()
			

	def InitializeMovieChooser(self):
		self.MovieFilter = gtk.FileFilter()
		self.MovieFilter.add_mime_type("video/*")

		self.MovieChooser = gtk.FileChooserDialog(title="Choose a video file",buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		self.MovieChooser.set_current_folder(os.getenv("HOME"))
		self.MovieChooser.set_filter(self.MovieFilter)

		self.MovieChooserButton = gtk.FileChooserButton(self.MovieChooser)
		self.MovieChooserButton.show()

		self.MovieHBox.add(self.MovieChooserButton)

	def ShowPreview(self, widget):
		'Shows a preview of the selected xscreensaver within a gtk.Socket'
		self.Apply.set_sensitive(True)
		self.CleanUpPreview()
		self.Preview.show()
		self.SetUpSocket()

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

	def SaverListSelect(self, widget):
		'Get the new label, check if it s the same as the old, and if not change the preview and buttons accordingly. Also, check for speed now so we don t need to so frequently.'
		self.SSRadio.set_active(True)
		selectedRow, locInRow = self.SaverListSelection.get_selected()
		if locInRow:
			if selectedRow.get_value(locInRow,0) != self.selectedSaver:
				self.EffectSaveableCheck(widget)
				self.selectedSaver = selectedRow.get_value(locInRow,0)
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
			self.SaverListstore.append([item])

	def CleanUpPreview(self):
		'Clean up the old preview/welcome note in preparation for the new preview'
		if self.PreviewShowing:
			self.socket.destroy()
			self.Run("kill %s" %self.previewShow.pid)
			self.PreviewShowing = False
		else:
			self.WelcomeBox.hide()
			self.NewHelpBox.hide()

	def OptionChange(self,widget):
		'This is in order to save changes like opacity'
		if self.is_selected(self.SaverListSelection):
			self.Apply.set_sensitive(True)
			self.SaveEdit.set_sensitive(True)

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
		self.OptionChange(widget)
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

	def SetUpTreeView(self,treeview="screensavers"):
		if treeview == "screensavers":
			treewidget = self.SaverList
			columns = ["screensavers"]
			self.SaverListstore = gtk.ListStore(str)
			self.GetScreenSavers()
			self.SaverList.set_model(self.SaverListstore)
			self.SaverListSelection = self.SaverList.get_selection()

		if treeview == "effects":
			treewidget = self.EffectsList
			columns = ["Name","Description"]

			# The liststore needs: Name, Description, whether it's a screensaver, speed (if screensaver), screensaver or 
			# movie filepath, opacity, priority setting, additional arguments (hence all the values below).
			self.EffectListstore = gtk.ListStore(str,str,bool,float,str,int,bool,str)

			self.GetSavedEffects()
			self.EffectsList.set_model(self.EffectListstore)
			self.EffectsListSelection = self.EffectsList.get_selection()

		for column in columns:
			treewidget.insert_column_with_attributes(-1,column,gtk.CellRendererText(),text=columns.index(column))
		
		if treeview == "effects":	
			self.EffectListstore.set_sort_column_id(0,gtk.SORT_ASCENDING)

	def EffectManager(self,name=None,mode="list"):
		'Returns a list of all the settings of a given custom effect name, adds settings, or removes settings.'	

		if mode == "list" or mode == "remove":
			index = self.settingLists[0].index(name)

		if mode == "list":
			settingslist = []
			for setting in self.settingLists:
				settingslist = settingslist + [setting[index]]	
			return settingslist
		
		if mode == "remove":
			for setting in self.settingLists:
				setting.pop(index)
		
		if mode == "add":
			for index in range(0,len(self.settingLists)):
				self.settingLists[index] = self.settingLists[index] + [self.TempSettings[index]]

	def SaveToDisk(self):
		pickleWrite = open(self.pickle,"w")
		pickle.dump(self.settingLists,pickleWrite)
		pickleWrite.close()
		print " * The settings have been saved to %s." %self.pickle
		return

	def ReadFromDisk(self):
		if os.path.exists(self.pickle):
			pickleRead = open(self.pickle,"r")
			readitems = pickle.load(pickleRead)
			pickleRead.close()
			return readitems

		else:
			return [self.effectList,self.descList,self.isSaverList,self.saverSpeedList,self.filepathList,self.opacityList,
				self.priorityList,self.argList]

	def GetSavedEffects(self):
		self.EffectListstore.clear()
		for effectname in self.settingLists[0]:
			# get the index of effect
			index = self.settingLists[0].index(effectname)
			ListstoreList = []
			for settingid in range(0,8):
			# iterate through all settings of that one effect
				listlist = self.settingLists[settingid]
				# add the settings for effect one by one
				ListstoreList = ListstoreList + [listlist[index]]
			self.EffectListstore.append(ListstoreList)

	def EffectsListSelect(self,widget):
		selectedRow, locInRow = self.EffectsListSelection.get_selected()
		if locInRow:
			if selectedRow.get_value(locInRow,0) != self.selectedEffect or self.CancelPressed:
				listDescribe = ["Name:","Description:","Using a screensaver:","Screensaver Speed:",
						"Filepath/Screensaver Name:","Opacity:","Using low CPU priority:","Additional arguments:"]
				print "\n" + "="*40
				for row in range(0,len(listDescribe)):
					print listDescribe[row],selectedRow.get_value(locInRow,row)
				print "="*40 + "\n"
			
				self.CancelPressed = False

				self.Remove.set_sensitive(True)
				self.Edit.set_sensitive(True)
				self.selectedEffect = selectedRow.get_value(locInRow,0)
				self.SetSettings(self.selectedEffect)
				self.ShowPreview(widget)
					

	def ResetSettings(self):
		self.EffectName.set_text("")
		self.EffectDescr.set_text("")
		self.MovieRadio.set_active(True)
		self.Opacity.set_value(100)
		self.Speed.set_value(1.0)
		self.CPUPriority.set_active(True)
		self.SpeedCheckBox.set_active(False)
		self.xscreensaverArgLabel.set_text("")
		self.SaveEdit.set_sensitive(False)
		self.Add.set_sensitive(False)
		self.SaverListSelection.unselect_all()
		self.SaverList.scroll_to_cell(0,use_align=True)
		self.Apply.set_sensitive(False)

	def SetSettings(self,name):
		self.ResetSettings()
		settingslist = self.EffectManager(name)

		self.selectedSaver = settingslist[4]
		self.UsingSpeed = self.UsingSpeedCheck()

		self.EffectName.set_text(settingslist[0])
		self.EffectDescr.set_text(settingslist[1])

		if settingslist[2]:
		# If using a screensaver
			self.SSRadio.set_active(True)
			saverid = self.ScreenSavers.index(settingslist[4])
			self.SaverListSelection.select_path(saverid)
			self.SaverList.scroll_to_cell(saverid,use_align=True)

		if settingslist[3] > 0:
		# If the speed is set at higher than or equal to 1, count it.
			self.Speed.set_value(settingslist[3])

		if not settingslist[6]:
		# If the priority setting is not on
			self.CPUPriority.set_active(True)
		
		# Set any saved arguments
		self.xscreensaverArgLabel.set_text(settingslist[7])

		# Set opacity
		self.Opacity.set_value(settingslist[5])
			

	def is_selected(self,TreeViewSelection):
		selectedRow, locInRow = TreeViewSelection.get_selected()
		if locInRow:
			return True

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
		self.SaveToDisk()
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
