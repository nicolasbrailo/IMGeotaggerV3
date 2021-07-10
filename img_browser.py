import threading
import wx

class ImgBrowser:
    CTRL_MARGIN = 5
    BUTTON_WIDTH = 100
    NAME_COL_WIDTH = 180
    COORDS_COL_WIDTH = 30

    def __init__(self, app, parent_wnd, img_preview_size):
        self.panel = wx.Panel(parent_wnd, -1)
        self.app = app
        self.img_preview_size = img_preview_size
        self.bg = None

        start_lbl = self.app.get_description_for(None)
        self.selection_detail = wx.StaticText(self.panel, -1, style=wx.TE_MULTILINE, label=start_lbl)

        start_lbl = '[Right click an image for larger preview]'
        self.map_detail = wx.StaticText(self.panel, -1, label=start_lbl)

        self.pos_set = wx.Button(self.panel, label="Set positions", size=(ImgBrowser.BUTTON_WIDTH, -1))
        self.pos_set.Bind(wx.EVT_BUTTON, self._on_pos_set_click)

        self.preview = wx.Button(self.panel, label="Preview", size=(ImgBrowser.BUTTON_WIDTH, -1))
        self.preview.Bind(wx.EVT_BUTTON, self._on_preview_requested)

        panel_size = (ImgBrowser.NAME_COL_WIDTH + ImgBrowser.COORDS_COL_WIDTH + img_preview_size[0] + ImgBrowser.CTRL_MARGIN, -1)
        self.imgs = wx.ListCtrl(self.panel, style=wx.LC_REPORT|wx.BORDER_SUNKEN, size=panel_size)
        self.imgs.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_selection)
        self.imgs.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self._on_preview_requested)
        self.imgs.InsertColumn(0, 'Preview', width=img_preview_size[0] + ImgBrowser.CTRL_MARGIN, format=wx.LIST_FORMAT_CENTRE)
        self.imgs.InsertColumn(1, 'Pos', width=ImgBrowser.COORDS_COL_WIDTH)
        self.imgs.InsertColumn(2, 'Name', width=ImgBrowser.NAME_COL_WIDTH)

        self.previews_lst = wx.ImageList(*img_preview_size)
        self.imgs.SetImageList(self.previews_lst, wx.IMAGE_LIST_SMALL)

        self.dir_select = wx.DirPickerCtrl(parent_wnd)
        self.dir_select.Bind(wx.EVT_DIRPICKER_CHANGED, self._on_path_selected)

        box = wx.BoxSizer(wx.VERTICAL)
        topbox = wx.BoxSizer(wx.HORIZONTAL)
        topbox.Add(self.pos_set, 1, wx.ALL, ImgBrowser.CTRL_MARGIN)
        topbox.Add(self.preview, 1, wx.ALL, ImgBrowser.CTRL_MARGIN)
        box.Add(self.dir_select, 1, wx.ALL, ImgBrowser.CTRL_MARGIN)
        box.Add(topbox)
        box.Add(self.selection_detail)
        box.Add(self.map_detail)
        box.Add(self.imgs, wx.EXPAND)
        self.panel.SetSizer(box)


    def _on_path_selected(self, _):
        # First clear list, otherwise the list may hold refs to a cleand up img
        self.imgs.DeleteAllItems()
        self.previews_lst.RemoveAll()
        path = self.dir_select.GetPath()
        row=0
        for img in self.app.load_images_from(path):
            browserimg=self.previews_lst.Add(img.preview)
            self.imgs.InsertItem(row, browserimg)
            self.imgs.SetItem(row, 1, img.coords_set)
            self.imgs.SetItem(row, 2, img.fname)
            row += 1

        if self.bg:
            self.bg.join()
        self.bg = threading.Thread(target=self._previews_bg_load)
        self.bg.start()


    def _previews_bg_load(self):
        for i in range(self.imgs.GetItemCount()):
            fname = self.imgs.GetItem(i, 2).GetText()
            preview = self.app.get_image_preview(fname)
            self.previews_lst.Replace(i, preview)
            if self.imgs.IsVisible(i):
                # The only way to refresh the items in the list seem to be to
                # change the scroll position or to re-set its image list.
                # Calling .RefreshItem(i), .Refresh() or .Update() doesn't work
                self.imgs.SetImageList(self.previews_lst, wx.IMAGE_LIST_SMALL)


    @staticmethod
    def _get_selected_paths(lst):
        item = lst.GetFirstSelected()
        paths = []
        while item != -1:
            paths.append(lst.GetItem(item, 2).GetText())
            item = lst.GetNextSelected(item)
        return paths


    def _on_preview_requested(self, _):
        paths = ImgBrowser._get_selected_paths(self.imgs)
        if paths is None or len(paths) == 0:
            return
        self.app.on_preview_requested(paths[0])


    def _on_selection(self, _):
        paths = ImgBrowser._get_selected_paths(self.imgs)
        self.selection_detail.SetLabel(self.app.get_description_for(paths))

    
    def _on_pos_set_click(self, _):
        paths = ImgBrowser._get_selected_paths(self.imgs)
        self.app.set_gps_coords_for(paths)
        self.selection_detail.SetLabel(self.app.get_description_for(paths))

        # Update selected rows to pos set=true
        item = self.imgs.GetFirstSelected()
        while item != -1:
            self.imgs.SetItem(item, 1, 'Y')
            item = self.imgs.GetNextSelected(item)


    def map_moved_to(self, pos):
        # TODO: This belongs one level up, but first I need to add a vertical layout
        self.map_detail.SetLabel(f"Map position: {pos}")

