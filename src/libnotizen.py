#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

"""
 Copyright (C) 2007 Christoph Würstle

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as
published by the Free Software Foundation.
"""

import time
import logging
import uuid

import gobject
import gtk

import simple_list


try:
	_
except NameError:
	_ = lambda x: x


class Notizen(gtk.HBox):

	def __init__(self, db, topBox):
		self._db = db
		self._topBox = topBox
		self.noteId = -1
		self._pos = -1
		self._noteBody = None #Last notetext
		self._categoryName = ""

		gtk.HBox.__init__(self, homogeneous = False, spacing = 0)
		logging.info("libnotizen, init")

		self._noteslist = simple_list.SimpleList()
		self._noteslist.set_eventfunction_cursor_changed(self._update_noteslist)

		self._noteslist.set_size_request(250, -1)

		vbox = gtk.VBox(homogeneous = False, spacing = 0)

		frame = gtk.Frame(_("Titles"))
		frame.add(self._noteslist)
		vbox.pack_start(frame, expand = True, fill = True, padding = 3)

		buttonHBox = gtk.HBox()
		vbox.pack_start(buttonHBox, expand = False, fill = True, padding = 3)

		button = gtk.Button(stock = gtk.STOCK_ADD)
		button.connect("clicked", self._on_add_note, None)
		buttonHBox.pack_start(button, expand = True, fill = True, padding = 3)

		button = gtk.Button(stock = gtk.STOCK_DELETE)
		button.connect("clicked", self._on_delete_note, None)
		buttonHBox.pack_start(button, expand = True, fill = True, padding = 3)

		self.pack_start(vbox, expand = False, fill = True, padding = 3)

		self._noteBodyView = gtk.TextView()
		self._noteBodyView.connect("focus-out-event", self.save_note, "focus-out-event")
		buf = self._noteBodyView.get_buffer()
		buf.set_text("")
		buf.connect("changed", self._on_note_changed, None)

		#self.textviewNotiz.set_size_request(-1, 50)
		self._noteScrollWindow = gtk.ScrolledWindow()
		self._noteScrollWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self._noteScrollWindow.add(self._noteBodyView)

		frame = gtk.Frame(_("Note"))
		frame.add(self._noteScrollWindow)

		vbox = gtk.VBox(homogeneous = False, spacing = 0)
		vbox.pack_start(frame, expand = True, fill = True, padding = 3)

		self._historyBox = gtk.HBox(homogeneous = False, spacing = 0)

		self._historyStatusLabel = gtk.Label(_("No History"))
		self._historyStatusLabel.set_alignment(0.0, 0.5)
		self._historyBox.pack_start(self._historyStatusLabel, expand = True, fill = True, padding = 3)

		button = gtk.Button(_("History"))
		button.connect("clicked", self._on_show_history, None)
		self._historyBox.pack_start(button, expand = True, fill = True, padding = 3)

		vbox.pack_start(self._historyBox, expand = False, fill = True, padding = 3)

		self.pack_start(vbox, expand = True, fill = True, padding = 3)

		self.load_notes()
		self._topBox.connect("reload_notes", self.load_notes)

	def set_wordwrap(self, enableWordWrap):
		if enableWordWrap:
			self._noteScrollWindow.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
			self._noteBodyView.set_wrap_mode(gtk.WRAP_WORD)
		else:
			self._noteScrollWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
			self._noteBodyView.set_wrap_mode(gtk.WRAP_NONE)

	def show_history_area(self, visible):
		if visible:
			self._historyBox.show()
		else:
			self._historyBox.hide()

	def load_notes(self, data = None):
		logging.info("load_notes params: pos:"+str(self._pos)+" noteid:"+str(self.noteId))
		self._noteslist.clear_items()
		self._noteslist.append_item(_("new Note"), "new")

		self._categoryName = self._topBox.get_category()
		search = self._topBox.get_search_pattern()
		notes = self._db.searchNotes(search, self._categoryName)

		if notes is not None:
			for note in notes:
				noteid, category, noteText = note
				title = self._get_title(noteText)
				self._noteslist.append_item(title, noteid)

		self.noteId = -1
		self._pos = -1
		self._noteBodyView.get_buffer().set_text("")

	def save_note(self, widget = None, data = None, data2 = None):
		logging.info("save_note params: pos:"+str(self._pos)+" noteid:"+str(self.noteId))
		#print "params:", data, data2
		buf = self._noteBodyView.get_buffer().get_text(self._noteBodyView.get_buffer().get_start_iter(), self._noteBodyView.get_buffer().get_end_iter())
		if buf is None or len(buf) == 0:
			return

		if buf == self._noteBody:
			return

		logging.info("Saving note: "+buf)
		if self._pos == -1 or self.noteId == -1:
			self._pos = -1
			self.noteId = str(uuid.uuid4())
			self._db.saveNote(self.noteId, buf, self._categoryName)
			self._noteslist.append_item(self._get_title(buf), self.noteId)
			self._pos = self._noteslist.select_last_item()
		else:
			self._db.saveNote(self.noteId, buf, self._categoryName)

		self._topBox.define_this_category()

	def _get_title(self, buf):
		"""
		@returns the title of the current note
		"""
		eol = buf.find("\n")
		if -1 == eol:
			eol = len(buf)
		title = buf[:eol]
		return title

	def _set_focus(self):
		self._noteBodyView.grab_focus()
		return False

	def _update_noteslist(self, data = None, data2 = None):
		if self._pos != -1:
			self.save_note()

		try:
			(pos, key, value) = self._noteslist.get_selection_data()
			if (pos == -1):
				return
		except StandardError:
			if data != "new":
				return
			key = None

		if key == "new" or data == "new":
			#both methods supported click add note or new note (first one disabled)
			self.noteId = str(uuid.uuid4())
			self._db.saveNote(self.noteId, "", self._categoryName)
			self._pos = -1
			self._noteslist.append_item("", self.noteId)
			self._noteBodyView.get_buffer().set_text("")
			self._pos = self._noteslist.select_last_item()
		else:
			self._pos = pos
			self.noteId, pcdatum, self._categoryName, self._noteBody = self._db.loadNote(key)
			self._historyStatusLabel.set_text(time.strftime(_("Last change: %d.%m.%y %H:%M"), time.localtime(pcdatum)))
			buf = self._noteBodyView.get_buffer()
			buf.set_text(self._noteBody)

		gobject.timeout_add(200, self._set_focus)

	def _on_note_changed(self, widget = None, data = None):
		if self._pos == -1 or self.noteId == -1:
			return

		buf = self._noteBodyView.get_buffer().get_text(self._noteBodyView.get_buffer().get_start_iter(), self._noteBodyView.get_buffer().get_end_iter())

		title = self._get_title(buf)
		value, key = self._noteslist.get_item(self._pos)

		if value != title:
			self._noteslist.change_item(self._pos, title, self.noteId)

	def _on_add_note(self, widget = None, data = None):
		self._update_noteslist("new")

	def _on_delete_note(self, widget = None, data = None):
		if (self.noteId == -1):
			return
		mbox = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO, _("Really delete?"))
		response = mbox.run()
		mbox.hide()
		mbox.destroy()
		if response == gtk.RESPONSE_YES:
			self._db.delNote(self.noteId)
			self.noteId = -1
			self._noteslist.remove_item(self._pos)
			self._pos = -1
			self._noteBodyView.get_buffer().set_text("")

	def _on_show_history(self, widget = None, data = None, label = None):
		if self.noteId == -1:
			mbox =  gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, _("No note selected."))
			response = mbox.run()
			mbox.hide()
			mbox.destroy()
			return

		rows = self._db.getNoteHistory(self.noteId)

		import libhistory
		dialog = libhistory.Dialog()

		lastNoteStr = ""
		for row in rows:
			daten = row[4][1]
			if daten != "" and lastNoteStr != daten:
				lastNoteStr = daten
				dialog.noteHistory.append([row[0], row[1], row[2], row[3], daten+"\n"])

		dialog.vbox.show_all()
		dialog.set_size_request(600, 380)

		if dialog.run() == gtk.RESPONSE_ACCEPT:
			print "saving"
			self.save_note()
			data = dialog.get_selected_row()
			if data is not None:
				self._db.speichereSQL(data[2], data[3].split(" <<Tren-ner>> "), rowid = self.noteId)
				logging.info("loading History")
				self._update_noteslist()

		dialog.destroy()
