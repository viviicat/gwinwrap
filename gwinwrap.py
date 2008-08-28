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


# TODO:Add filter combobox for movies/savers/all?


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

import pygst
pygst.require("0.10")
import gst, re, signal, os

class gwinwrap:
	"""This is a GUI to xwinwrap...gwinrwap!"""

	def __init__(self):
		# TODO: Add a filechooserbutton to choose a custom directory?
		if os.path.isdir("/usr/libexec/xscreensaver/"):
			self.XSSDir = "/usr/libexec/xscreensaver/" 
		elif os.path.isdir("/usr/lib64/xscreensaver/"):
			self.XSSDir = "/usr/lib64/xscreensaver/" 
		else:
			self.XSSDir = "/usr/lib/xscreensaver/" 

		### ADJUSTABLE VARIABLES -- It won't hurt to edit these a bit	
		# The nice command
		self.nice = ["nice","-n","15"]
		# Pickle files
		self.pickle = ["presets.gwrp","prefs.gwrp"]
		### END AJUSTABLE VARIABLES ###

		self.settingLists = self.ReadFromDisk()
		self.PrefCommand = self.ReadFromDisk("preferences")

		# Set the Glade file
		self.gladefile = "gwinwrap.glade"
		self.gladeXML = gtk.glade.XML(self.gladefile)

		# Initialize some program variables
		self.PreviewShowing = False
		self.selectedSaver = ""
		self.selectedEffect = ""
		self.MakingNew = False
		self.CancelPressed = False
		self.PresetSelectionProcess = False
		self.ScreenSavers = []
		self.OldName = ""

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
			, "on_SpeedCheckBox_toggled" : self.SpeedCheckBox
			, "on_XscreensaverClose_clicked" : self.Quit
			, "on_XwinwrapClose_clicked" : self.Quit
			, "on_ArgLabel_changed" : self.OptionChange
			, "on_Remove_clicked" : self.Remove
			, "on_RemoveConfirm_response" : self.RemoveConfirmResponse
			, "on_New_clicked" : self.ShowNew
			, "on_Edit_clicked" : self.ShowEdit
			, "on_CancelEdit_clicked" : self.Cancel
			, "on_EffectName_changed" : self.EffectSaveableCheck
			, "on_EffectDescr_changed" : self.EffectSaveableCheck
			, "on_SaveEdit_clicked" : self.SaveEdit
			, "on_Add_clicked" : self.Add
			, "on_MovieRadio_toggled" : self.MovieRadioToggled
			, "on_SSRadio_toggled" : self.SaverRadioToggled
			, "on_Preferences_clicked" : self.PrefPane
			, "on_ClosePrefs_clicked" : self.PrefPane
		}		
		self.gladeXML.signal_autoconnect(dic)

		# Check for Xwinwrap
		if not self.is_installed("xwinwrap"):
			self.NoXwinwrap.show()
			print " ** You don't have Xwinwrap installed!"

		if not self.is_installed("mplayer"):
			self.MovieHBox.set_sensitive(False)
			print " ** Disabling video support -- you don't have mplayer installed"

		# Get the widgets we need
		# FIXME: isn't there a better way to do this?
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
		self.ArgLabel = self.gladeXML.get_widget("ArgLabel")
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
		self.DuplicateWarning = self.gladeXML.get_widget("DuplicateWarning")
		self.Prefs = self.gladeXML.get_widget("Prefs")
		self.Preferences = self.gladeXML.get_widget("Preferences")
		self.noinput = self.gladeXML.get_widget("noinput")
		self.nofocus = self.gladeXML.get_widget("nofocus")
		self.sticky = self.gladeXML.get_widget("sticky")
		self.fullscreen = self.gladeXML.get_widget("fullscreen")
		self.skiptaskbar = self.gladeXML.get_widget("skiptaskbar")
		self.skippager = self.gladeXML.get_widget("skippager")
		self.above = self.gladeXML.get_widget("above")
		self.below = self.gladeXML.get_widget("below")

		# Enable RGBA colormap
		self.gtk_screen = self.Main.get_screen()
		self.rgbcolormap = self.gtk_screen.get_rgb_colormap()
		self.colormap = self.gtk_screen.get_rgba_colormap()
		if self.colormap == None:
			self.colormap = self.rgbcolormap
		gtk.widget_set_default_colormap(self.colormap)


		self.PrefButtonID = {self.noinput:"-ni",self.nofocus:"-nf",self.sticky:"-s",self.fullscreen:"-fs",self.skiptaskbar:"-st",
					self.skippager:"-sp",self.above:"-a",self.below:"-b"}

		self.InitializeChoosers()

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

		# Express Mode
		if startOptions.args:
			if startOptions.args[0] in self.EffectNameList():
				print " * GWINWRAP ** Express mode enabled, launching preset \"%s\" now."%startOptions.args[0]
				nameindex = self.EffectNameList(startOptions.args[0])
				self.EffectsListSelection.select_path(nameindex)
				self.PresetSelectionProcess = True
				self.SetSettings(startOptions.args[0])
	
				if self.MovieRadio.get_active():
					self.ComposeCommand("movie",express=True)
				else:
					self.ComposeCommand("xscreensaver",express=True)
	
				self.ApplyEffect()
			else:
				print " * GWINWRAP ** ERROR: The chosen preset \"%s\" does not exist." %startOptions.args[0]
			if not startOptions.options.window:
				quit()

		self.SetPrefCheckBoxes()

		self.Main.show()

	def SetPrefCheckBoxes(self):
		for pref in self.PrefButtonID:
			if self.PrefButtonID[pref] in self.PrefCommand:
				pref.set_active(True)
	
	def PrefPane(self,widget):
		if widget == self.Preferences:
			self.Prefs.show()
		else:
			self.Prefs.hide()
			self.PrefCommand = []
			for pref in self.PrefButtonID:
				if pref.get_active():
					self.PrefCommand = self.PrefCommand + [self.PrefButtonID[pref]]
			# FIXME: We should refresh the apply button now if an effect is ready.

	def MovieRadioToggled(self,widget):
		if self.MovieChooser.get_filename() and widget.get_active():
			self.ChooseMovie(widget)

	def SaverRadioToggled(self,widget):
		if widget.get_active():
			self.SaverListSelect(None)

	def SpeedCheckBox(self,widget):
		if not self.PresetSelectionProcess:
			self.ShowPreview()

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
		if not self.SpeedCheckBox.get_active():
			speed = 0
		else:
			speed = self.Speed.get_value()

		if self.SSRadio.get_active():
			usingsaver = True
			selectedrow, locInRow = self.SaverListSelection.get_selected()
			if locInRow:
				coreEffect = selectedrow.get_value(locInRow,0)
		else:
			usingsaver = False
			coreEffect = self.MovieChooser.get_filename()
			
		self.TempSettings = [self.EffectName.get_text(),self.EffectDescr.get_text(),usingsaver,speed,coreEffect,
				self.Opacity.get_value(),self.CPUPriority.get_active(),self.ArgLabel.get_text()]
		if delold:
			self.EffectManager(self.OldName,mode="remove")
		self.EffectManager(mode="add")
		self.GetSavedEffects()
		sortednames = []
		for name in self.EffectNameList():
			sortednames = sortednames + [name.lower()]
		sortednames.sort()
		newname = self.TempSettings[0]
		nameindex = sortednames.index(newname.lower())
		self.EffectsListSelection.select_path(nameindex)
		self.EffectsList.scroll_to_cell(nameindex,use_align=True)
		print " * Updated settings."
		self.CloseEditing()
		self.OldName = ""

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
		DupeShowing = False
		if not self.PresetSelectionProcess:
			if self.EffectName.get_text() in self.EffectNameList() and self.EffectName.get_text() != self.OldName:
				self.DuplicateWarning.show()
				DupeShowing = True
			else:
				DupeShowing = False

		if self.EffectName.get_text() != "" and not DupeShowing:
				
			if self.is_selected(self.SaverListSelection) or self.movieSetAndChosen():
				self.Add.set_sensitive(True)	
				self.SaveEdit.set_sensitive(True)
		else:
			self.Add.set_sensitive(False)
			self.SaveEdit.set_sensitive(False)

		if not DupeShowing:
			self.DuplicateWarning.hide()

	def ChooseMovie(self,widget):
		if self.MovieChooser.get_filename():
			self.SpeedHBox.set_sensitive(False)
			self.MovieRadio.set_active(True)
			self.MovieFile = self.MovieChooser.get_filename()
			self.ShowPreview()

	def Remove(self,widget):
		self.RemoveConfirm.show()

	def RemoveConfirmResponse(self,widget,response):
		self.RemoveConfirm.hide()
		if response==0:
			selectedRow, locInRow = self.EffectsListSelection.get_selected()
			if locInRow:
				self.EffectManager(selectedRow.get_value(locInRow,0),"remove")
			self.Remove.set_sensitive(False)
			self.CleanUpPreview()
			self.ResetSettings()
			self.WelcomeBox.show()
			self.GetSavedEffects()
			

	def InitializeChoosers(self):
		self.MovieFilter = gtk.FileFilter()
		self.MovieFilter.add_mime_type("video/*")

		self.MovieChooser = gtk.FileChooserDialog(title="Choose a video file",buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		self.MovieChooser.set_current_folder(os.getenv("HOME"))
		self.MovieChooser.set_filter(self.MovieFilter)

		self.MovieChooserButton = gtk.FileChooserButton(self.MovieChooser)
 		self.MovieChooserButton.connect("file_set",self.ChooseMovie)
		self.MovieChooserButton.show()

		self.MovieHBox.add(self.MovieChooserButton)

	def ShowPreview(self):
		'Shows a preview of the selected xscreensaver within a gtk.Socket'
		self.Apply.set_sensitive(True)
		self.CleanUpPreview()
		self.Preview.show()

		self.Socket = self.SetUpSocket("socket")

		if self.MovieRadio.get_active():
			previewcommand = self.ComposeCommand("movie")
		else:
			previewcommand = self.ComposeCommand("xscreensaver")

		self.previewShow = self.Run(previewcommand)
		self.Socket.show()

		self.PreviewShowing = True

	def ApplyEffect(self, New=True):
		'If the effect is a new one, compose a new xwinwrap command. Then quit any currently running instances, then(finally), run the xwinwrap command.'
		if New:
			self.command = self.ComposeCommand()
			self.Refresh.set_sensitive(True)
		self.RunEffect()		

	def RunEffect(self):
		self.KillXwinwrap()
		if self.MovieRadio.get_active():
			self.CleanUpPreview()
		cmd = ""
		for item in self.command:
			cmd = cmd + item + " "
		print " * GWINWRAP ** Running: " + cmd
		self.Run(self.command)

	def Refresh(self, widget):
		self.ApplyEffect(False)

	def Apply(self, widget):
		self.Apply.set_sensitive(False)
		self.Stop.set_sensitive(True)
		self.ApplyEffect()

	def Stop(self, widget):
		self.Stop.set_sensitive(False)
		if self.is_selected(self.EffectsListSelection):
			self.Apply.set_sensitive(True)
		self.Refresh.set_sensitive(False)
		self.KillXwinwrap()

	def SaverListSelect(self, widget):
		'Get the new label, check if it s the same as the old, and if not change the preview and buttons accordingly. Also, check for speed now so we don t need to so frequently.'
		selectedRow, locInRow = self.SaverListSelection.get_selected()
		if locInRow and widget:
			if not self.SSRadio.get_active():
				self.SSRadio.set_active(True)
			self.EffectSaveableCheck(widget)
			self.selectedSaver = selectedRow.get_value(locInRow,0)
			self.UsingSpeed, self.UsingFPS = self.UsingCheck()
			self.ShowPreview()

	def GetScreenSavers(self):
		'Get a list of the screensavers in the xscreensaver directory'
		filelist = os.listdir(self.XSSDir)
		for item in filelist:
			if self.is_saver(item):
				self.ScreenSavers.append(item)
		if len(self.ScreenSavers) == 0:
			self.NoXscreensavers.show()
			print "You don't have any Xscreensavers in %s" %self.XSSDir
		self.ScreenSavers.sort()
		for item in self.ScreenSavers:
			
			self.SaverListstore.append([item])

	def CleanUpPreview(self):
		'Clean up the old preview/welcome note in preparation for the new preview'
		if self.PreviewShowing:
			self.Socket.destroy()
			self.Run(["kill","%s"%self.previewShow.pid])
			self.PreviewShowing = False
		else:
			self.WelcomeBox.hide()
			self.NewHelpBox.hide()

	def movieSetAndChosen(self):
		if self.MovieRadio.get_active() and self.MovieChooser.get_filename():
			return True
		else: return False

	def OptionChange(self,widget):
		'This is in order to save changes like opacity'
		if self.is_selected(self.SaverListSelection) or self.movieSetAndChosen():
			self.Apply.set_sensitive(True)
			self.SaveEdit.set_sensitive(True)

	def KillXwinwrap(self):
		if self.xwinwrap_running():
			print " * GWINWRAP ** Killing current xwinwrap process."
			self.Run(["killall","xwinwrap"])

	def xwinwrap_running(self):
		'Use pidof and pgrep to determine if xwinwrap is running'
		if subprocess.call(['pidof','xwinwrap'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0 or subprocess.call(['pgrep','xwinwrap'], stdout=subprocess.PIPE) == 0:
			return True

	def is_installed(self,app):
		'Use which to determine if xwinwrap is installed'
		if subprocess.call(['which',app], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
			return True

	def SpeedChange(self, widget):
		'Checks the option to customize speed when the speed is changed from the slider'
		self.SpeedCheckBox.set_active(True)
		self.OptionChange(widget)
		if not self.PresetSelectionProcess:
			self.ShowPreview()

	def UsingCheck(self):
		'Check the selected screensaver for an option by reading its --help output'
		helpfile = subprocess.Popen(["%s%s" %(self.XSSDir,self.selectedSaver),"--help"], stdout=subprocess.PIPE,stderr=subprocess.STDOUT).communicate()[0]

		if string.find(helpfile,"-speed") >= 0:
			speed = True				
		else: speed =  False

		if string.find(helpfile,"-maxfps") >= 0:
			maxfps = True
		else: maxfps = False

		return speed,maxfps

	def SetUpSpeedList(self):
		'Custom values in order to make the speed-affected screensavers slower. Roughly merges the --maxfps option with the --speed option.'
		if self.SpeedCheckBox.get_active():
			speedvalue = self.Speed.get_value()
			speedArg = []
			fpsArg = None
			if speedvalue >= 5.0:
				speed = speedvalue - 5
			elif self.UsingFPS: 
				speed = 1
				fps = speedvalue + 10
				fpsArg = ["--maxfps","%f"%fps]
			else:
				speed = speedvalue

			speedArg = speedArg + ["--speed","%i"%speed]
			self.Command = self.Command + speedArg

			if fpsArg:
				self.Command = self.Command + fpsArg

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

			self.EffectListstore = gtk.ListStore(str,str)

			self.GetSavedEffects()
			self.EffectsList.set_model(self.EffectListstore)
			self.EffectsListSelection = self.EffectsList.get_selection()

		for column in columns:
			treewidget.insert_column_with_attributes(-1,column,gtk.CellRendererText(),text=columns.index(column))
		
		if treeview == "effects":	
			self.EffectListstore.set_sort_column_id(0,gtk.SORT_ASCENDING)

	def EffectManager(self,name=None,mode="add"):
		'Returns a list of all the settings of a given custom effect name, adds settings, or removes settings.'				
		
		if mode == "remove":
			self.settingLists.pop(self.EffectNameList(name))
		
		if mode == "add":
			self.settingLists = self.settingLists + [self.TempSettings]

	def SaveToDisk(self, mode="presets"):
		if mode == "presets":
			picklefile = self.pickle[0]
			dump = self.settingLists
		elif mode == "preferences":
			picklefile = self.pickle[1]
			dump = self.PrefCommand

		pickleWrite = open(picklefile,"w")
		pickle.dump(dump,pickleWrite)
		pickleWrite.close()
		print " * The %s have been saved to %s." %(mode,picklefile)
		return

	def ReadFromDisk(self,mode="presets"):
		if mode == "presets":
			picklefile = self.pickle[0]
		elif mode == "preferences":
			picklefile = self.pickle[1]

		if os.path.exists(picklefile):
			pickleRead = open(picklefile,"r")
			readitems = pickle.load(pickleRead)
			pickleRead.close()

			if mode == "presets":
				returnableitems = []
				# Make sure all effects use installed savers or are movies
				# FIXME: This results in effects with uninstalled screensavers or incorrect filepaths getting deleted from the pickle. 
				# It might be better to just ignore them.
				for index in range(len(readitems)):
					if self.is_saver(readitems[index][4]):
						returnableitems = returnableitems + [readitems[index]]
					elif not readitems[index][2] and os.path.exists(readitems[index][4]):
						returnableitems = returnableitems + [readitems[index]]
				return returnableitems

			elif mode == "preferences":
				return readitems

		else:
			return []

	def EffectNameList(self,name=None):
		namelist = []
		for effectid in range(len(self.settingLists)):
			namelist.append(self.settingLists[effectid][0])

		if name:
			return namelist.index(name)
		else:
			return namelist

	def GetSavedEffects(self):
		self.EffectListstore.clear()
		for effectid in range(len(self.settingLists)):
			self.EffectListstore.append([self.settingLists[effectid][0],self.settingLists[effectid][1]])

	def EffectsListSelect(self,widget):
		selectedRow, locInRow = self.EffectsListSelection.get_selected()
		if locInRow:
			if selectedRow.get_value(locInRow,0) != self.selectedEffect or self.CancelPressed:
				self.PresetSelectionProcess = True
				listDescribe = ["Name:","Description:","Using a screensaver:","Screensaver Speed:",
						"Filepath/Screensaver Name:","Opacity:","Using low CPU priority:","Additional arguments:"]
				print "\n" + "="*40
				for item in range(0,len(listDescribe)):
					print listDescribe[item],self.settingLists[self.EffectNameList(selectedRow.get_value(locInRow,0))][item]
				print "="*40 + "\n"
			
				self.CancelPressed = False

				self.Remove.set_sensitive(True)
				self.Edit.set_sensitive(True)
				self.selectedEffect = selectedRow.get_value(locInRow,0)
				self.SetSettings(self.selectedEffect)
				self.ShowPreview()
				self.PresetSelectionProcess = False
					

	def ResetSettings(self):
		self.SelectedSaver = ""
		self.EffectName.set_text("")
		self.EffectDescr.set_text("")
		self.Opacity.set_value(100)
		self.Speed.set_value(1.0)
		self.CPUPriority.set_active(True)
		self.SpeedHBox.set_sensitive(False)
		self.SpeedCheckBox.set_active(False)
		self.ArgLabel.set_text("")
		self.SaveEdit.set_sensitive(False)
		self.Add.set_sensitive(False)
		self.SaverListSelection.unselect_all()
		self.SaverList.scroll_to_cell(0,use_align=True)
		self.Apply.set_sensitive(False)
		self.MovieChooser.unselect_all()
		self.MovieRadio.set_active(True)
		self.DuplicateWarning.hide()
		self.OldName = ""

	def SetSettings(self,name):
		self.ResetSettings()
		settingslist = self.settingLists[self.EffectNameList(name)]

		self.EffectName.set_text(settingslist[0])
		self.EffectDescr.set_text(settingslist[1])

		if settingslist[2]:
		# If using a screensaver
			self.selectedSaver = settingslist[4]
			self.UsingSpeed,self.UsingFPS = self.UsingCheck()
			self.SSRadio.set_active(True)
			saverid = self.ScreenSavers.index(settingslist[4])
			self.SaverListSelection.select_path(saverid)
			self.SaverList.scroll_to_cell(saverid,use_align=True)
		else:
			self.MovieFile = settingslist[4]
			self.MovieChooser.set_filename(self.MovieFile)
			self.MovieRadio.set_active(True)

		if settingslist[3] > 0:
		# If the speed is set at higher than or equal to 1, count it.
			self.Speed.set_value(settingslist[3])

		if not settingslist[6]:
		# If the priority setting is not on
			self.CPUPriority.set_active(True)
		
		# Set any saved arguments
		self.ArgLabel.set_text(settingslist[7])

		# Set opacity
		self.Opacity.set_value(settingslist[5])
			

	def is_selected(self,TreeViewSelection):
		selectedRow, locInRow = TreeViewSelection.get_selected()
		if locInRow:
			return True

	def is_saver(self,saver):
		'Just checking to make sure there arent any directories in the list.'
		#FIXME: Check more carefully (not just for dirs)
		if os.path.exists(self.XSSDir + saver) and not os.path.isdir(self.XSSDir + saver):
			return True
		else: 
			return  False

	def SetUpSocket(self,mode="socket"):
		'Attach the socket and color it black to avoid flashes when changing previews'
		# Disable alpha colormap
		gtk.widget_set_default_colormap(self.rgbcolormap)
		if mode == "socket":
			Socket = gtk.Socket()

		elif mode == "drawingarea":
			Socket = gtk.DrawingArea()

		self.Preview.add(Socket)
		black = gtk.gdk.Color(red=0, green=0, blue=0, pixel=0)
		Socket.modify_bg(gtk.STATE_NORMAL,black)

		# Re-enable alpha colormap
		gtk.widget_set_default_colormap(self.colormap)

		return Socket

	def ComposeCommand(self,mode="xwinwrap",express=False):
		'Create the command to use when launching either xwinwrap or the previews'
		baseCommand = ["xwinwrap"] + self.PrefCommand

		# Screensavers that use images -- they can't run with -argb option
		imagesavers = ["antspotlight","blitspin","bumps","carousel","decayscreen","distort","flipscreen3d","gleidescope","glslideshow","jigsaw",
				"mirrorblob","rotzoomer","slidescreen","spotlight","twang","zoom"]

		if mode == "xwinwrap":
			opacity = float(self.Opacity.get_value())			
			opacity = opacity/100		
	
			Args = self.ArgLabel.get_text()
					
			if self.CPUPriority.get_active():
				baseCommand = self.nice + baseCommand

			if not self.selectedSaver in imagesavers and self.SSRadio.get_active():
				baseCommand.append("-argb")

			command = baseCommand + ["-o","%f"%opacity,"--"] + self.Command

			if Args:
				command = command + [Args]


			if self.MovieRadio.get_active():
				command = command + ["-wid","WID"]
			else:
				command = command + ["-window-id","WID"]

		elif mode == "xscreensaver":

			self.Command = ["%s%s"%(self.XSSDir,self.selectedSaver)]
	
			if self.UsingSpeed:
				self.SpeedHBox.set_sensitive(True)
				self.SetUpSpeedList()

			else: self.SpeedHBox.set_sensitive(False)

			if not express:
				command = self.Command + ["-window-id","%i"%self.Socket.window.xid]		
				command = self.nice + command

		elif mode == "movie":
			baseMovieCommand = "mplayer"
			self.Command = [baseMovieCommand,"%s"%self.MovieFile,"-quiet"]
			command = self.Command + ["-wid","%i"%self.Socket.window.xid]

		elif mode == "all":
			command = baseCommand + ["1","--","%s%s"%(self.XSSDir,self.selectedSaver),"-window-id","WID"] 

		if not express:
			return command
			

	def Run(self,command):
		'Launch quietly, and return the object for PID referencing'
	#	signal.signal(signal.SIGCHLD, signal.SIG_IGN)
		popen_object = subprocess.Popen(command, stdout=open(os.devnull, 'w'),stderr=open(os.devnull,'w'))

		return popen_object


	def Quit(self, widget):
		self.CleanUpPreview()
		self.SaveToDisk()
		self.SaveToDisk("preferences")
		gtk.widget_pop_colormap()
		gtk.main_quit()

class startOptions:
	"""This is a separate class which checks the startup command for options."""
	parser = OptionParser(usage="usage: %prog SCREENSAVER [options]",description="QUICK START: If you want, you can use %prog to automatically run one of your preset effects by adding the name (including case, spaces require quotation marks) after ./%prog. For example: ./%prog \"Cool Plasma\" will start the Cool Plasma preset effect. This option disables the rest of the interface.")

	parser.add_option("-w", "--window", action="store_true", dest="window", default=False,
			help="Show the interface even if running an effect directly.")
	parser.add_option("-s", "--stop", action="store_true", dest="stop", default=False,
			help="An 'off' button. Quits any xwinwrap instances, then quits itself.")
	
	options, args = parser.parse_args()

		
if __name__ == "__main__":
	run = gwinwrap()
	gtk.main()
