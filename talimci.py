import re,gi,os
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')

from gi.repository import Gtk, GtkSource, GObject, Gio, Gdk


class SoruDialog(Gtk.Dialog):
	def __init__(self, baslik, ebeveyn):
		Gtk.Dialog.__init__(self, baslik, ebeveyn, 0,
			(Gtk.STOCK_YES, Gtk.ResponseType.OK,
			Gtk.STOCK_NO, Gtk.ResponseType.CANCEL))

		self.set_default_size(150, 100)

		self.label = Gtk.Label()

		kutu = self.get_content_area()
		kutu.add(self.label)
		self.show_all()

	def set_text(self,yazi):
		self.label.set_text(yazi)


class CustomCompletionProvider(GObject.GObject, GtkSource.CompletionProvider):
	"""
	This is a custom Completion Provider
	In this instance, it will do 2 things;
	1) always provide Hello World! (Not ideal but an option so its in the example)
	2) Utilizes the Gtk.TextIter from the TextBuffer to determine if there is a jinja
	example of '{{ custom.' if so it will provide you with the options of foo and bar.
	if select it will insert foo }} or bar }}, completing your syntax
	PLEASE NOTE the GtkTextIter Logic and regex are really rough and should be adjusted and tuned
	to fit your requirements
	# Implement the Completion Provider
	# http://stackoverflow.com/questions/32611820/implementing-gobject-interfaces-in-python
	# https://gist.github.com/andialbrecht/4463278 (Python example implementing TreeModel)
	# https://developer.gnome.org/gtk3/stable/GtkTreeModel.html (Gtk TreeModel interface specification)
	# A special thank you to @zeroSteiner
	"""

	def do_populate(self, context):
		proposals = []
			#GtkSource.CompletionItem(label='Hello World!', text='Hello World!', icon=None, info=None),  # always proposed
			#GtkSource.CompletionItem(label='[Paketci]', text='[Paketci]', icon=None, info=None)  # always proposed

		# found difference in Gtk Versions
		end_iter = context.get_iter()
		if not isinstance(end_iter, Gtk.TextIter):
			_, end_iter = context.get_iter()

#		print(end_iter.get_text())

		if end_iter:
			mps_list ={
				"[paket]":["tanim    =","paketci =","grup       =","url           ="],
				"[kaynak]":["gz            =","xz            =","dosya    =","bz2         =","github  =","1              =","2              =","3              ="],
				"[sha256]":["1              =","2              =","3              =","4              =","5              =","6              ="],
				"[derle]":["betik     =","dosya    =","yama    =","tip          ="],
				"[pakur]":["tip          =","dosya    =","betik     =","strip     ="]

			}


			buf = end_iter.get_buffer()
			mov_iter = end_iter.copy()
			if mov_iter.backward_search('[', Gtk.TextSearchFlags.VISIBLE_ONLY):
				mov_iter, _ = mov_iter.backward_search('[', Gtk.TextSearchFlags.VISIBLE_ONLY)
				left_text = buf.get_text(mov_iter, end_iter, True)
				text = left_text.split("\n")
				if len(text) == 1:
					for key in mps_list.keys():
						proposals.append(GtkSource.CompletionItem(label=key, text=key[1:], icon=None, info=None))
				elif text[0] == "[paket]" and "=" not in text[-1]:
					for key in mps_list["[paket]"]:
						proposals.append(GtkSource.CompletionItem(label=key, text=key, icon=None, info=None))
				elif text[0] == "[kaynak]" and "=" not in text[-1]:
					for key in mps_list["[kaynak]"]:
						proposals.append(GtkSource.CompletionItem(label=key, text=key, icon=None, info=None))
				elif text[0] == "[sha256]" and "=" not in text[-1]:
					for key in mps_list["[sha256]"]:
						proposals.append(GtkSource.CompletionItem(label=key, text=key, icon=None, info=None))
				elif text[0] == "[derle]" and "=" not in text[-1]:
					for key in mps_list["[derle]"]:
						proposals.append(GtkSource.CompletionItem(label=key, text=key, icon=None, info=None))
				elif text[0] == "[pakur]" and "=" not in text[-1]:
					for key in mps_list["[pakur]"]:
						proposals.append(GtkSource.CompletionItem(label=key, text=key, icon=None, info=None))
			else:
				left_text = ''

			if re.match(r'.*\{\{\s*custom\.$', left_text):
				proposals.append(
					GtkSource.CompletionItem(label='foo', text='foo }}')  # optionally proposed based on left search via regex
				)
				proposals.append(
					GtkSource.CompletionItem(label='bar', text='bar }}')  # optionally proposed based on left search via regex
				)

		context.add_proposals(self, proposals, True)
		return

class Talimci(Gtk.Window):
	def __init__(self, title = "Talimat Editör"):
		Gtk.Window.__init__(self)
		ana_kutu = Gtk.VBox()
		self.add(ana_kutu)
		self.connect("key-press-event",self.tus_basildi_fonksiyon)
		self.set_default_size(800,600)

		toolbar = Gtk.Toolbar()
		ana_kutu.pack_start(toolbar, expand = False, fill = False, padding = 5)
		#toolbar.set_style(Gtk.TOOLBAR_ICONS)

		#TOOL BAR GÖRÜNÜM OLUŞTURULUYOR
		self.d_ac = Gtk.ToolButton(Gtk.STOCK_OPEN)
		self.d_ac.set_label("Talimat aç")
		toolbar.insert(self.d_ac, 0)
		self.d_ac.connect("clicked",self.d_ac_basildi)
		self.d_ac.set_property("has-tooltip", True)
		self.d_ac.connect("query-tooltip", self.d_bilgi,"Talimat Aç")

		self.d_kaydet = Gtk.ToolButton(Gtk.STOCK_SAVE)
		self.d_kaydet.set_label("Talimatı kaydet")
		self.d_kaydet.set_sensitive(False)
		toolbar.insert(self.d_kaydet, 1)
		self.d_kaydet.connect("clicked",self.d_kaydet_basildi)
		self.d_kaydet.set_property("has-tooltip", True)
		self.d_kaydet.connect("query-tooltip", self.d_bilgi,"Talimat Kaydet")


		self.d_farkli_kaydet = Gtk.ToolButton(Gtk.STOCK_SAVE_AS)
		self.d_farkli_kaydet.set_label("Talimatı farklı kaydet")
		toolbar.insert(self.d_farkli_kaydet, 2)
		self.d_farkli_kaydet.connect("clicked",self.d_farkli_kaydet_basildi)
		self.d_farkli_kaydet.set_property("has-tooltip", True)
		self.d_farkli_kaydet.connect("query-tooltip", self.d_bilgi,"Talimat Farklı Kaydet")

		self.talimat_yolu_degis = Gtk.ToolButton(Gtk.STOCK_FILE)
		self.talimat_yolu_degis.set_label("Talimat liste yolunu değiştir")
		toolbar.insert(self.talimat_yolu_degis, 3)
		self.talimat_yolu_degis.connect("clicked",self.talimat_yolu_degis_basildi)
		self.talimat_yolu_degis.set_property("has-tooltip", True)
		self.talimat_yolu_degis.connect("query-tooltip", self.d_bilgi,"Talimat Dizini Aç")

		iki_boluk_kutu = Gtk.HPaned()
		sol_kutu = Gtk.VBox()
		sag_kutu = Gtk.VBox()
		iki_boluk_kutu.add1(sol_kutu)
		iki_boluk_kutu.add2(sag_kutu)
		ana_kutu.pack_start(iki_boluk_kutu, expand = True, fill = True, padding = 5)

		#Widgetlerin alanı
		self.talimat_yolu = Gtk.Entry()
		self.talimat_yolu.connect("activate", self.talimatname_yolu_basildi)
		#self.talimat_yolu.set_editable(False)
		sol_kutu.pack_start(self.talimat_yolu, expand = False, fill = False, padding = 5)

		self.kategori_combo = Gtk.ComboBoxText()
		self.kategori_combo.connect("changed", self.combo_degisti)
		sol_kutu.pack_start(self.kategori_combo, expand = False, fill = False, padding = 5)

		scrol = Gtk.ScrolledWindow()
		scrol.set_hexpand(True)
		scrol.set_vexpand(True)

		self.talimat_ara = Gtk.SearchEntry()
		self.talimat_ara.connect("search_changed", self.talimat_arandi)
		sol_kutu.pack_start(self.talimat_ara, expand = False, fill = False, padding = 5)


		self.talimat_liste = Gtk.TreeView()
		self.talimat_liste.connect("row-activated", self.talimat_liste_tiklandi)
		scrol.add(self.talimat_liste)
		sol_kutu.pack_start(scrol, expand = False, fill = True, padding = 5)
		rendererText = Gtk.CellRendererText()
		column = Gtk.TreeViewColumn("Talimatlar", rendererText, text=0)
		self.talimat_liste.append_column(column)


		self.dosya_yolu = Gtk.Entry()
		self.dosya_yolu.connect("activate", self.dosya_yolu_basildi)
		#self.dosya_yolu.set_editable(False)
		sag_kutu.pack_start(self.dosya_yolu, expand = False, fill = False, padding = 5)

		scroll = Gtk.ScrolledWindow()
		scroll.set_hexpand(True)
		scroll.set_vexpand(True)
		self.gsv = GtkSource.View()
		self.gsv.set_show_line_numbers(1)
		self.gsv.set_indent_on_tab(1)
		self.gsv.set_tab_width(8)
		self.gsv.set_show_line_marks(1)
		scroll.add(self.gsv)
		sag_kutu.pack_start(scroll, expand = True, fill = True, padding = 5)
		self.textbuff = GtkSource.Buffer()
		self.textbuff.connect("changed",self.yazi_degisti)
		self.gsv.set_buffer(self.textbuff)
		self.lm = GtkSource.LanguageManager()
		self.textbuff.set_language(self.lm.get_language('ini'))

		self.keywords = """
				GtkSourceView
				Completion
			"""
		self.set_auto_completation()
		if os.path.isdir("/usr/milis/talimatname"):
			self.dizin_doldur("/usr/milis/talimatname")

	def d_bilgi(self, widget, x, y, keyboard_mode, tooltip, text):
		tooltip.set_text(text)
		return True

	def talimatname_yolu_basildi(self,basilan=""):
		yazilan = self.dosya_yolu.get_text()
		self.talimat_yolu_kontrol(yazilan)


	def dosya_yolu_basildi(self,basilan=""):
		yazilan = self.dosya_yolu.get_text()
		if os.path.exists(yazilan):
			if yazilan.split("/")[-1] != "talimat":
				self.bilgi_diyalogu("Hata","Lütfen bir 'talimat' dosyası yolu giriniz.",Gtk.MessageType.WARNING)
			else:
				self.dosya_ac(yazilan)
		else:
			self.bilgi_diyalogu("Hata","Böyle bir dosya yada dizin yok.",Gtk.MessageType.WARNING)

	def tus_basildi_fonksiyon(self, widget, event):
		ctrl = (event.state & Gdk.ModifierType.CONTROL_MASK)
		if ctrl and event.keyval == Gdk.KEY_s:
			if self.d_kaydet.get_sensitive():
				self.d_kaydet_basildi()

	def talimat_arandi(self, basilan):
		combo = self.kategori_combo.get_active_text()
		yazilan = self.talimat_ara.get_text()
		if combo != None:
			yeni_ = []
			self.talimat_ls = Gtk.ListStore(str)
			for liste in self.talimatlar.keys():
				for madde in self.talimatlar[liste]:
					if yazilan in madde:
						self.talimat_ls.append([madde])
			self.talimat_liste.set_model(self.talimat_ls)

	def talimat_yolu_degis_basildi(self,basilan=""):
		dialog = Gtk.FileChooserDialog("Lütfen Bir Talimatname Dizini Seçiniz", self,
						Gtk.FileChooserAction.SELECT_FOLDER,
						(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
						Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			yazilan = dialog.get_filename()
			if self.talimat_yolu_kontrol(yazilan):
				dialog.destroy()
				self.talimat_yolu_degis_basildi()
			else:
				dialog.destroy()
		elif response == Gtk.ResponseType.CANCEL:
			dialog.destroy()

	def talimat_yolu_kontrol(self,yol):
			if yol.split("/")[-1] != "talimatname":
				self.bilgi_diyalogu("Hata","Sizden'talimatname' dizini seçmeniz beklenmektedir",Gtk.MessageType.WARNING)
				return True
			else:
				self.dizin_doldur(yol)
				return False


	def talimat_liste_tiklandi(self, widget, row, col):
		model = widget.get_model()
		yazi = model[row][0]
		self.dosya_ac(self.talimat_yolu.get_text()+"/"+yazi+"/talimat")

	def dizin_doldur(self,dizin):
		self.kategori_combo.remove_all()
		self.talimat_yolu.set_text(dizin)
		self.talimatlar = {}
		kategoriler = os.listdir(dizin)
		for kategori in kategoriler:
			if os.path.isdir(dizin+"/"+kategori):
				self.talimatlar[kategori] = []
				self.kategori_combo.append_text(kategori)
		self.dizin_listele(dizin)

	def dizin_listele(self,dizin):
		for dosya in os.listdir(dizin):
			x = dizin+"/"+dosya
			if os.path.isdir(x):
				self.dizin_listele(x)
			elif dosya == "talimat":
				kategori = dizin.split("talimatname/")[1].split("/")[0]
				self.talimatlar[kategori].append(dizin.split("talimatname/")[1])

	def yazi_degisti(self,buffer):
		if self.dosya_yolu.get_text() != "":
			self.d_kaydet.set_sensitive(True)

	def combo_degisti(self,degisen):
		self.talimat_ara.set_text("")
		self.talimat_ls = Gtk.ListStore(str)
		for madde in self.talimatlar[self.kategori_combo.get_active_text()]:
			self.talimat_ls.append([madde])
		self.talimat_liste.set_model(self.talimat_ls)

	def set_auto_completation(self):
		"""
		1)
		Set up a provider that get words from what has already been entered
		in the gtkSource.Buffer that is tied to the GtkSourceView
		2)
		Set up a second buffer that stores the keywords we want to be available
		3)
		Setup an instance of our custome completion class to handle special characters with
		auto complete.
		"""
		# This gets the GtkSourceView completion that's already tied to the GtkSourceView
		# We need it to attached our providers to it
		self.gsv_completion = self.gsv.get_completion()

		# 1) Make a new provider, attach it to the main buffer add to view_autocomplete
		self.gsv_autocomplete = GtkSource.CompletionWords.new('main')
		self.gsv_autocomplete.register(self.textbuff)
		self.gsv_completion.add_provider(self.gsv_autocomplete)

		# 2) Make a new buffer, add a str to it, make a provider, add it to the view_autocomplete
		self.keybuff = GtkSource.Buffer()
		self.keybuff.begin_not_undoable_action()
		self.keybuff.set_text(self.keywords)
		self.keybuff.end_not_undoable_action()
		self.gsv_keyword_complete = GtkSource.CompletionWords.new('keyword')
		self.gsv_keyword_complete.register(self.keybuff)
		self.gsv_completion.add_provider(self.gsv_keyword_complete)

		# 3) Set up our custom provider for syntax completion.
		custom_completion_provider = CustomCompletionProvider()
		self.gsv_completion.add_provider(custom_completion_provider)
		self.custom_completion_provider = custom_completion_provider
		return

	def d_ac_basildi(self,basilan=""):
		dialog = Gtk.FileChooserDialog("Lütfen Bir Talimat Dosyası Seçiniz", self,
						Gtk.FileChooserAction.OPEN,
						(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
						Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
		filter_text = Gtk.FileFilter()
		filter_text.set_name("Talimat Dosyası")
		filter_text.add_mime_type("text/plain")
		dialog.add_filter(filter_text)
		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			yazilan = dialog.get_filename()
			if yazilan.split("/")[-1] != "talimat":
				self.bilgi_diyalogu("Hata","Lütfen bir 'talimat' dosyası seçiniz",Gtk.MessageType.WARNING)
				dialog.destroy()
				self.d_ac_basildi()
			else:
				self.dosya_ac(yazilan)
				dialog.destroy()
		elif response == Gtk.ResponseType.CANCEL:
			dialog.destroy()

	def dosya_ac(self,dosya_yolu):
		if self.d_kaydet.get_sensitive():
			soru = SoruDialog("Dikkat",self)
			soru.set_text("Dosya değiştirildi ve kaydedilmedi.\nDevam etmeniz halinde çalışmalarınız silinecek.\nDevam Etmek İstiyor Musunuz?")
			response = soru.run()
			if response == Gtk.ResponseType.CANCEL:
				soru.destroy()
				return
			else:
				soru.destroy()
		try:
			with open(dosya_yolu) as dosya:
				okunan = dosya.read()
				self.textbuff.set_text(okunan)
				self.dosya_yolu.set_text(dosya_yolu)
				self.d_kaydet.set_sensitive(False)
		except IOError as hata:
			self.bilgi_diyalogu("Hata","Dosya okunamadı!",Gtk.MessageType.WARNING)


	def d_kaydet_basildi(self,basilan=""):
		self.dosya_kaydet(self.dosya_yolu.get_text())

	def d_farkli_kaydet_basildi(self,basilan=""):
		dialog = Gtk.FileChooserDialog("Lütfen Dosya Kaydı İçin Bir Dizin Seçiniz", self,
						Gtk.FileChooserAction.SAVE,
						(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
						Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
		filter_text = Gtk.FileFilter()
		filter_text.set_name("Talimat Dosyası")
		filter_text.add_mime_type("text/plain")
		dialog.add_filter(filter_text)
		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			yazilan = dialog.get_filename()
			if yazilan.split("/")[-1] != "talimat":
				self.bilgi_diyalogu("Hata","Lütfen dosya adını 'talimat' olarak yazınız",Gtk.MessageType.WARNING)
				dialog.destroy()
				self.d_farkli_kaydet_basildi()
			else:
				dialog.destroy()
				if os.path.exists(yazilan):
					soru = SoruDialog("Dikkat",self)
					soru.set_text("Seçmiş olduğunuz konumda dosya mevcut.\nDevam etmeniz halinde dosyanın üzerine yazılacak.\nDevam Etmek İstiyor Musunuz?")
					response = soru.run()
					if response == Gtk.ResponseType.OK:
						self.dosya_kaydet(yazilan)
					soru.destroy()
				else:
					self.dosya_kaydet(yazilan)
		elif response == Gtk.ResponseType.CANCEL:
			dialog.destroy()

	def dosya_kaydet(self,dosya_yolu):
		self.dosya_yolu.set_text(dosya_yolu)
		yazi = self.textbuff.get_text(self.textbuff.get_start_iter(), self.textbuff.get_end_iter(),True)
		try:
			f = open(dosya_yolu,"w")
			f.write(yazi)
			f.close()
			self.d_kaydet.set_sensitive(False)
		except IOError as hata:
			self.bilgi_diyalogu("Hata","Dosya yazılamadı!",Gtk.MessageType.WARNING)

	def bilgi_diyalogu(self,yazi_1,yazi_2,tip=Gtk.MessageType.INFO):
		dialog = Gtk.MessageDialog(self, 0, tip, Gtk.ButtonsType.OK, yazi_1)
		dialog.format_secondary_text(yazi_2)
		dialog.run()
		dialog.destroy()


def main():
	pen = Talimci()
	pen.connect("destroy", Gtk.main_quit)
	pen.show_all()
	Gtk.main()

if __name__ == '__main__':
	main()
