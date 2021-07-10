from img_browser import ImgBrowser
from img_manager import ImgManager
from geo_browser import GeoBrowser
import wx


class Main(wx.App):
    IMG_PREVIEW_SIZE = (120,67)

    def __init__(self, redirect):
        super().__init__(redirect=redirect)

        self.frame = wx.Frame(parent=None, id=wx.ID_ANY,
                          title='IMGeotagger V3, xplat edition', size=(800, 600))

        self.browser = GeoBrowser(self.frame)
        self.img_manager = ImgManager(Main.IMG_PREVIEW_SIZE)
        self.img_browser = ImgBrowser(self, self.frame, Main.IMG_PREVIEW_SIZE)

        self.preview_active = False
        self.preview = wx.StaticBitmap(self.frame, id=wx.ID_ANY, bitmap=wx.NullBitmap)
        self.preview.SetScaleMode(wx.StaticBitmap.Scale_AspectFill)
        self.preview.Hide()

        self.box = wx.BoxSizer(wx.HORIZONTAL)
        self.box.Add(self.img_browser.panel, 0, wx.EXPAND)
        self.box.Add(self.browser.panel, 1, wx.EXPAND)
        self.box.Add(self.preview, 1, wx.EXPAND)
        self.frame.SetSizer(self.box)

        self.browser.load_browser()

        self.SetTopWindow(self.frame)
        self.frame.Show()

        self.coords = None
        self.timer_id = 1
        self.timer = wx.Timer(self, self.timer_id)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(300)


    def on_preview_requested(self, fname):
        if self.preview_active:
            pos = self.preview.GetPosition()
            size = self.preview.GetSize()
            self.preview.SetBitmap(wx.NullBitmap)
            self.preview.Hide()
            self.browser.panel.SetPosition(pos)
            self.browser.panel.SetSize(size)
            self.browser.panel.Show()
        else:
            path = self.img_manager.get_full_path_for(fname)
            pos = self.browser.panel.GetPosition()
            size = self.browser.panel.GetSize()
            img = wx.Image(path , wx.BITMAP_TYPE_ANY).ConvertToBitmap()
            self.preview.SetBitmap(img)
            self.browser.panel.Hide()
            self.preview.SetPosition(pos)
            self.preview.SetSize(size)
            self.preview.Show()

        self.preview_active = not self.preview_active
        self.frame.Update()

    
    def get_description_for(self, paths):
        return self.img_manager.get_description_for(paths)


    def load_images_from(self, path):
        self.img_manager.reload(path)
        return self.img_manager.imgs

    
    def get_image_preview(self, fname):
        return self.img_manager.get_image_preview(fname)

    
    def set_gps_coords_for(self, paths):
        pos = self.browser.get_coords()
        self.img_manager.set_positions_for(pos, paths)


    def on_timer(self, _):
        new_coords = self.browser.get_coords()
        if self.coords != new_coords:
            self.coords = new_coords
            self.img_browser.map_moved_to(self.browser.get_coords())


    def OnExit(self):
        self.timer.Stop()
        self.browser.on_app_exit()
        del self.browser
        GeoBrowser.static_on_app_exit()
        return 0


if __name__ == '__main__':
    app = Main(False)
    app.MainLoop()

