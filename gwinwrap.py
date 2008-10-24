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
		print "\n[ Gavin Langdon's GWINWRAP -- Keep it Simple Stupid! ]"

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
		# Startup items directory
		self.startupDir = "/.config/autostart/"
		### END AJUSTABLE VARIABLES ###

		print " * Loading Presets..."
		self.settingLists = self.ReadFromDisk()
		self.PrefCommand = self.ReadFromDisk("preferences")

		# Set the Glade file
		print " * Setting up GUI..."
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
		self.MovieFile = ""

		# Create our dictionary and connect it
		dic = {"on_Main_destroy" : self.Quit
			, "on_Close_clicked" : self.Quit 

			, "on_Apply_clicked" : self.Apply
			, "on_Refresh_clicked" : self.Refresh
			, "on_SaverList_cursor_changed" : self.SaverListSelect
			, "on_EffectsList_cursor_changed" : self.EffectsListSelect
			, "on_Stop_clicked" : self.Stop

			, "on_Speed_value_changed" : self.OptionChange
			, "on_Opacity_value_changed" : self.OptionChange
			, "on_CPUPriority_toggled" : self.OptionChange
			, "on_SpeedCheckBox_toggled" : self.OptionChange
			, "on_ArgLabel_changed" : self.OptionChange
			, "on_Loop_toggled" : self.OptionChange
			, "on_Sound_toggled" : self.OptionChange

			, "on_XscreensaverClose_clicked" : self.Quit
			, "on_XwinwrapClose_clicked" : self.Quit

			, "on_Remove_clicked" : self.Remove
			, "on_RemoveConfirm_response" : self.RemoveConfirmResponse

			, "on_New_clicked" : self.PaneChange
			, "on_Edit_clicked" : self.PaneChange
			, "on_CancelEdit_clicked" : self.PaneChange
			, "on_SaveEdit_clicked" : self.PaneChange
			, "on_Add_clicked" : self.PaneChange

			, "on_EffectName_changed" : self.EffectSaveableCheck
			, "on_EffectDescr_changed" : self.EffectSaveableCheck

			, "on_MovieRadio_toggled" : self.MovieRadioToggled
			, "on_SSRadio_toggled" : self.SaverRadioToggled

			, "on_Preferences_clicked" : self.PrefPane
			, "on_ClosePrefs_clicked" : self.PrefPane

			, "on_StartupCombo_changed" : self.CheckStartupBox
		}		
		self.gladeXML.signal_autoconnect(dic)

		# Check for Xwinwrap
		print " * Checking for Xwinwrap and MPlayer..."
		if not self.is_installed("xwinwrap"):
			self.NoXwinwrap.show()
			print " ** You don't have Xwinwrap installed!"

		if not self.is_installed("mplayer"):
			self.MovieHBox.set_sensitive(False)
			print " ** Disabling video support -- you don't have mplayer installed"

		# Get the widgets we need
		# > Explanation for those who don't understand glade:
		# This is assigning the xml stuff that the program Glade creates
		# to memory so that the program can interact with it. The string names
		# come from the widget's name defined in Glade.

		self.Main = self.gladeXML.get_widget("Main")
		self.SpeedCheckBox = self.gladeXML.get_widget("SpeedCheckBox")
		self.Speed = self.gladeXML.get_widget("Speed")
		self.Opacity = self.gladeXML.get_widget("Opacity")
		self.Stop = self.gladeXML.get_widget("Stop")
		self.Apply = self.gladeXML.get_widget("Apply")
		self.Refresh = self.gladeXML.get_widget("Refresh")
		self.SpeedHBox = self.gladeXML.get_widget("SpeedHBox")
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
		self.New = self.gladeXML.get_widget("New")
		self.CancelEdit = self.gladeXML.get_widget("CancelEdit")
		self.EffectsList = self.gladeXML.get_widget("EffectsList")
		self.EffectName = self.gladeXML.get_widget("EffectName")
		self.NewHelpBox = self.gladeXML.get_widget("NewHelpBox")
		self.Remove = self.gladeXML.get_widget("Remove")
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
		self.overrideredirect = self.gladeXML.get_widget("overrideredirect")
		self.InfoName = self.gladeXML.get_widget("InfoName")
		self.InfoDescr = self.gladeXML.get_widget("InfoDescr")
		self.InfoSet = self.gladeXML.get_widget("InfoSet")
		self.MovieOptionsHBox = self.gladeXML.get_widget("MovieOptionsHBox")
		self.Loop = self.gladeXML.get_widget("Loop")
		self.Sound = self.gladeXML.get_widget("Sound")
		self.StartupCombo = self.gladeXML.get_widget("StartupCombo")
		self.StartupCheckBox = self.gladeXML.get_widget("StartupCheckBox")


		# Enable RGBA colormap
		# > This is so that we have transparent windows. We need to check so we don't
		# crash if the theme doesn't support it.
		self.gtk_screen = self.Main.get_screen()
		self.rgbcolormap = self.gtk_screen.get_rgb_colormap()
		self.colormap = self.gtk_screen.get_rgba_colormap()
		if self.colormap == None:
			self.colormap = self.rgbcolormap
		gtk.widget_set_default_colormap(self.colormap)


		print " * Loading global preferences..."
		self.PrefButtonID = {self.noinput:"-ni",self.nofocus:"-nf",self.sticky:"-s",
					self.fullscreen:"-fs",self.skiptaskbar:"-st",
					self.skippager:"-sp",self.above:"-a",self.below:"-b",
					self.overrideredirect:"-ov"
					}

		self.InitializeChoosers()

		# Enable stopping the already running xwinwrap process
		if self.xwinwrap_running():
			self.Stop.set_sensitive(True)
			if startOptions.options.stop:
				self.KillAll()
				if not startOptions.args and not startOptions.options.window:
					quit()
		if startOptions.options.stop == True and not startOptions.args and not startOptions.options.window:
			print " * No need to stop anything, nothing's running.\n"
			quit()

		self.SetUpTreeView("effects")
		self.SetUpTreeView("screensavers")

		self.StartupCombo.set_model(self.EffectListstore)

		self.startupeffect = self.DesktopEntry()

		self.UpdateStartup()

		# Express Mode
		#  > This is used to start the effect without the window opening (used for startup command, etc).
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
		self.ShantzCheck()

		print " * Showing Main window..."
		self.Main.show()

	def UpdateStartup(self):
		if self.startupeffect:
			self.SettingStartup = True
			sortedlist = self.EffectNameList()
			newlist = []
			for name in sortedlist:
				newlist.append(name.lower())
			newlist.sort()
			self.StartupCombo.set_active(newlist.index(self.startupeffect.lower()))
		else:
			self.StartupCombo.set_active(0)
			self.StartupCheckBox.set_active(False)

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

			if self.StartupCheckBox.get_active():
				self.DesktopEntry("write",self.StartupCombo.get_active_text())
			else:
				self.DesktopEntry("remove")

	def CheckStartupBox(self,widget):
		if widget == self.StartupCombo:
			self.StartupCheckBox.set_active(True)
			self.SettingStartup = False
		else:
			self.StartupCheckBox.set_active(False)

	def MovieRadioToggled(self,widget):
		if widget.get_active() and self.MovieChooser.get_filename():
			self.EffectSaveableCheck(None)
			self.ChooseMovie(widget)

	def SaverRadioToggled(self,widget):
		if widget.get_active():
			self.EffectSaveableCheck(None)
			self.SaverListSelect(None)

	def ShowEditing(self):
                self.CustomFrame.hide()
                self.EditFrame.show()


	def PaneChange(self,widget):
		if widget == self.CancelEdit or widget == self.New:
			self.CleanUpPreview()

		if widget == self.New:
			self.Preview.hide()
			self.Add.show()
			self.SaveEdit.hide()
			self.ResetSettings()
			self.NewHelpBox.show()

		if widget == self.Edit:
			self.SaveEdit.show()
			self.Add.hide()
			self.SaveEdit.set_sensitive(False)
			# Save a copy of the label for identification later
			self.OldName = self.EffectName.get_text()

		if widget == self.CancelEdit:
			self.CancelPressed = True
			self.EffectsListSelect(widget)
			self.CloseEditing()

		if widget == self.SaveEdit:
			self.Save()

		if widget == self.Add:
			self.Save(overwrite=False)

		if widget == self.New or widget == self.Edit:
			self.ShowEditing()

	def Save(self,overwrite=True):
		if not self.SpeedCheckBox.get_active():
			speed = 0
		else:
			speed = self.Speed.get_value()

		if self.SSRadio.get_active():
			selectedrow, locInRow = self.SaverListSelection.get_selected()
			if locInRow:
				coreEffect = selectedrow.get_value(locInRow,0)
		else:
			coreEffect = self.MovieChooser.get_filename()
			
		self.TempSettings = [self.EffectName.get_text(),self.EffectDescr.get_text(),self.SSRadio.get_active(),speed,coreEffect,
				self.Opacity.get_value(),self.CPUPriority.get_active(),self.ArgLabel.get_text(),self.Loop.get_active(),
				self.Sound.get_active()]
		if overwrite:
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
		self.CloseEditing()
		self.UpdateStartup()
		self.OldName = ""

	def CloseEditing(self):
		self.EditFrame.hide()
		self.CustomFrame.show()

		if self.is_selected(self.EffectsListSelection):
			self.EffectsListSelect(None)
		else:
			self.WelcomeBox.show()
			self.ResetSettings()

	def StripPath(self,moviefile):
		'Strips the path from the filename so it just displays the name'
		strippedfilename = ""
		for letterindex in range(len(moviefile)-1,0,-1):
			if moviefile[letterindex] == "/":
				return strippedfilename
			else:
				strippedfilename = moviefile[letterindex] + strippedfilename
		return strippedfilename

	def SetInfoSet(self):
		string = ""
		select = True
		

		if self.SSRadio.get_active() and self.selectedSaver:
			string = "\"%s\" screensaver"%self.selectedSaver
		elif self.MovieRadio.get_active() and self.MovieFile:
			string = "\"%s\" video"%self.StripPath(self.MovieFile)

		else:
			select = False
			self.InfoSet.set_markup("<b> </b>")

		if select:
			
			if self.SpeedCheckBox.get_active():
				speedsetting = ", custom speed ~%u"%self.Speed.get_value()
			else: speedsetting = ""

			if self.ArgLabel.get_text() != "":
				args = ", custom options \"%s\""%self.ArgLabel.get_text()
			else: args = ""
		
			if self.CPUPriority.get_active():
				cpu = ", low CPU priority"
			else: cpu = ""

			if self.MovieRadio.get_active():
				if self.Loop.get_active():
					loop = ", looping"
				else: loop = ""
	
				if self.Sound.get_active():
					sound = ", with sound"
				else: sound = ""

			else:
				sound = ""
				loop = ""

			string = string + "%s%s, %i%% opacity%s%s%s"%(loop,sound,self.Opacity.get_value(),speedsetting,cpu,args)

			self.InfoSet.set_markup("<b>%s</b>"%string)

	def EffectSaveableCheck(self,widget):
		if widget == self.EffectName:
			# Avoid a resize when textbox is filled and emptied
			if widget.get_text() == "":
				self.InfoName.set_markup("<big><b> </b></big>")
			else:
				self.InfoName.set_markup("<big><b>%s</b></big>"%widget.get_text())

		elif widget == self.EffectDescr:
			self.InfoDescr.set_markup("<i>%s</i>"%widget.get_text())

		DupeShowing = False
		if not self.PresetSelectionProcess:
			self.SetInfoSet()

			lowerlist = []
			for name in self.EffectNameList():
				lowerlist.append(name.lower())

			if self.EffectName.get_text().lower() in lowerlist and self.EffectName.get_text() != self.OldName:
				self.DuplicateWarning.show()
				DupeShowing = True
			else:
				DupeShowing = False

		if self.EffectName.get_text() != "" and not DupeShowing:
				
			if self.is_selected(self.SaverListSelection) and self.SSRadio.get_active() or self.movieSetAndChosen():
				self.Add.set_sensitive(True)	
				self.SaveEdit.set_sensitive(True)
			else:
				self.Add.set_sensitive(False)
				self.SaveEdit.set_sensitive(False)
		else:
			self.Add.set_sensitive(False)
			self.SaveEdit.set_sensitive(False)

		if not DupeShowing:
			self.DuplicateWarning.hide()

	def ChooseMovie(self,widget):
		if self.MovieChooser.get_filename():
			self.MovieOptionsHBox.show()
			self.EffectSaveableCheck(None)
			self.SpeedHBox.hide()
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
			self.Edit.set_sensitive(False)
			self.GetSavedEffects()
			self.UpdateStartup()
			

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

		self.SetInfoSet()

		self.PreviewShowing = True

	def ApplyEffect(self, New=True):
		'If the effect is a new one, compose a new xwinwrap command. Then quit any currently running instances, then(finally), run the xwinwrap command.'
		if New:
			self.command = self.ComposeCommand()
			self.Refresh.set_sensitive(True)
		self.RunEffect()		

	def RunEffect(self):
		self.KillAll()
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
		if self.is_selected(self.EffectsListSelection) or self.MovieFile:
			self.Apply.set_sensitive(True)
		self.Refresh.set_sensitive(False)
		self.KillAll()

	def SaverListSelect(self, widget):
		'Get the new label, change the preview and buttons accordingly. Also, check for speed now so we don t need to so frequently.'
		selectedRow, locInRow = self.SaverListSelection.get_selected()
		if locInRow:
			if widget != self.SSRadio or self.SSRadio.get_active():
				if not self.SSRadio.get_active():
					self.SSRadio.set_active(True)
				self.MovieOptionsHBox.hide()
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
		if widget == self.SaverList:
			self.SSRadio.set_active(True)

		if self.is_selected(self.SaverListSelection) or self.movieSetAndChosen():
			self.SetInfoSet()
			self.Apply.set_sensitive(True)
			self.SaveEdit.set_sensitive(True)
			if widget in [self.Speed,self.SpeedCheckBox,self.Loop,self.Sound]:
				if widget == self.Speed:
					self.SpeedCheckBox.set_active(True)

				if not self.PresetSelectionProcess:
					self.ShowPreview()

	def KillAll(self,item="xwinwrap"):
		if self.xwinwrap_running():
			print " * GWINWRAP ** Killing current %s process."%item
			self.Run(["killall",item])

	def xwinwrap_running(self):
		'Use pidof and pgrep to determine if xwinwrap is running'
		if subprocess.call(['pidof','xwinwrap'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0 or subprocess.call(['pgrep','xwinwrap'], stdout=subprocess.PIPE) == 0:
			return True

	def is_installed(self,app):
		'Use which to determine if xwinwrap is installed'
		if subprocess.call(['which',app], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
			return True

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

	def ShantzCheck(self):
		#FIXME: Move to UsingCheck (I'm lazy)
		helpfile = subprocess.Popen(["xwinwrap","--help"], stdout=subprocess.PIPE,stderr=subprocess.STDOUT).communicate()[0]
		if string.find(helpfile,"-ov") >= 0:
			self.overrideredirect.set_sensitive(True)
		else:
			print " * Gwinwrap suggests installing Shantz Xwinwrap for a better experience."
			if self.overrideredirect.get_active():
				self.overrideredirect.set_active(False)
				self.PrefPane(None)
			


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
		'Adds settings, or removes settings.'				
		if mode == "remove":
			self.settingLists.pop(self.EffectNameList(name))
		
		if mode == "add":
			self.settingLists = self.settingLists + [self.TempSettings]

	def DesktopEntry(self,mode="read",effect=None):
		'Adds a desktop entry in [home]/.config/autostart/ linking to a bash script in the gwinwrap directory...'
		# FIXME: this is probably not the best way to do it. The bash script changes directories so that gwinwrap
		# knows where the gladefile is.

		gwrpdir = os.getcwd()
		home = os.getenv("HOME")
		twofiles = ["%s/startup"%gwrpdir,"%s%sgwinwrap.desktop"%(home,self.startupDir)]

		if mode == "write":
			for onefile in twofiles:
				if os.path.exists(onefile):
					os.remove(onefile)

			bashstring = "#!/bin/bash\ncd %s\n./gwinwrap.py \"%s\""%(gwrpdir,effect)
	
			write = open(twofiles[0], "w")
			write.write(bashstring)
			write.close()

			self.Run(["chmod","+x","%s/startup"%gwrpdir])

			desktopstring = "\n[Desktop Entry]\nType=Application\nEncoding=UTF-8\nVersion=1.0\nName=Gwinwrap Startup\nName[en_US]=Gwinwrap Startup\nComment[en_US]=Required for effect auto-start.\nComment=Required for effect auto-start.\nExec=%s/startup\nX-Gnome-Autostart-enabled=true"%gwrpdir

			write = open(twofiles[1],"w")
			write.write(desktopstring)
			write.close()

			self.startupeffect = effect

			print " * GWINWRAP ** Created a bash script in %s and added a desktop entry to %s which launches it. The effect \"%s\" will now start at login."%(gwrpdir,self.startupDir,effect)

		elif mode == "read":
			if os.path.exists(twofiles[0]) and os.path.exists(twofiles[1]):
				read = open(twofiles[0],"r")
				bashstring = read.read()
				counter = -1
				for letter in bashstring:
					counter = counter + 1
					if letter == "\"":
						return string.strip(bashstring[counter:],"\"\n")


			elif os.path.exists(twofiles[0]):
				os.remove(twofiles[0])
				return None

			elif os.path.exists(twofiles[1]):
				os.remove(twofiles[1])
				return None
			else:
				return None

		elif mode == "remove":
			removed = False
			for onefile in twofiles:
				if os.path.exists(onefile):
					removed = True
					os.remove(onefile)
			if removed:
				print " * GWINWRAP ** Removed desktop entry and bash script."


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
		
				self.CancelPressed = False
				self.Remove.set_sensitive(True)
				self.Edit.set_sensitive(True)
				self.selectedEffect = selectedRow.get_value(locInRow,0)
				self.SetSettings(self.selectedEffect)
				self.ShowPreview()
				self.PresetSelectionProcess = False
					

	def ResetSettings(self):
		self.selectedSaver = ""
		self.EffectName.set_text("")
		self.EffectDescr.set_text("")
		self.Opacity.set_value(100)
		self.Speed.set_value(1.0)
		self.CPUPriority.set_active(True)
		self.SpeedHBox.hide()
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
		self.InfoName.set_markup("<big><b> </b></big>")
		self.InfoDescr.set_text("")
		self.InfoSet.set_markup("<b> </b>")
		self.MovieOptionsHBox.hide()

	def SetSettings(self,name):
		self.ResetSettings()
		settingslist = self.settingLists[self.EffectNameList(name)]

		self.EffectName.set_text(settingslist[0])
		self.EffectDescr.set_text(settingslist[1])

		if settingslist[2]:
		# If using a screensaver
			self.SSRadio.set_active(True)
			self.selectedSaver = settingslist[4]
			self.UsingSpeed,self.UsingFPS = self.UsingCheck()
			saverid = self.ScreenSavers.index(settingslist[4])
			self.SaverListSelection.select_path(saverid)
			self.SaverList.scroll_to_cell(saverid,use_align=True)
			self.MovieOptionsHBox.hide()
		else:
			self.MovieFile = settingslist[4]
			self.MovieChooser.set_filename(self.MovieFile)
			self.MovieRadio.set_active(True)

		if settingslist[3] > 0:
		# If the speed is set at higher than or equal to 1, count it.
			self.Speed.set_value(settingslist[3])

		if not settingslist[6]:
		# If the priority setting is not on
			self.CPUPriority.set_active(False)

		# Set looping
		self.Loop.set_active(settingslist[8])
		# Set sound
		self.Sound.set_active(settingslist[9])
		
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
				"mirrorblob","rotzoomer","slidescreen","spotlight","twang","zoom","pacman","bubbles","xmatrix"]

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
				self.SpeedHBox.show()
				self.SetUpSpeedList()

			else: 
				self.SpeedHBox.hide()
				self.Speed.set_value(1.00)
				self.SpeedCheckBox.set_active(False)

			if not express:
				command = self.Command + ["-window-id","%i"%self.Socket.window.xid]		
				command = self.nice + command

		elif mode == "movie":
			self.Command = ["mplayer","%s"%self.MovieFile,"-quiet","-noconsolecontrols"]
			if self.Loop.get_active():
				self.Command = self.Command + ["-loop","0"]
			if not self.Sound.get_active():
				self.Command.append("-nosound")

			if not express:
				command = self.Command + ["-wid","%i"%self.Socket.window.xid]

		elif mode == "all":
			command = baseCommand + ["1","--","%s%s"%(self.XSSDir,self.selectedSaver),"-window-id","WID"] 

		if not express:
			return command
			

	def Run(self,command):
		'Launch quietly, and return the object for PID referencing so that we can kill it later'
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
