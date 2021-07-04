# This file was stolen and adapted from here
# https://github.com/cztomczak/cefpython/blob/master/examples/wxpython.py

from cefpython3 import cefpython as cef
import platform
import sys
import wx

# Platforms
WINDOWS = (platform.system() == "Windows")
LINUX = (platform.system() == "Linux")
MAC = (platform.system() == "Darwin")

def cef_xplat_init():
    assert cef.__version__ >= "66.0", "CEF Python v66.0+ required to run this"
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    settings = {}
    if MAC:
        # Issue #442 requires enabling message pump on Mac
        # and calling message loop work in a timer both at
        # the same time. This is an incorrect approach
        # and only a temporary fix.
        settings["external_message_pump"] = True
    cef.Initialize(settings=settings)

    # Must ignore X11 errors like 'BadWindow' and others by
    # installing X11 error handlers. This must be done after
    # wx was intialized.
    if LINUX:
        cef.WindowUtils.InstallX11ErrorHandlers()

    if MAC:
        try:
            # noinspection PyUnresolvedReferences
            from AppKit import NSApp
        except ImportError:
            print("[wxpython.py] Error: PyObjC package is missing, "
                  "cannot fix Issue #371")
            print("[wxpython.py] To install PyObjC type: "
                  "pip install -U pyobjc")
            sys.exit(1)

        # Make the content view for the window have a layer.
        # This will make all sub-views have layers. This is
        # necessary to ensure correct layer ordering of all
        # child views and their layers. This fixes Window
        # glitchiness during initial loading on Mac (Issue #371).
        NSApp.windows()[0].contentView().setWantsLayer_(True)


class FocusHandler(object):
    def OnGotFocus(self, browser, **_):
        # Temporary fix for focus issues on Linux (Issue #284).
        if LINUX:
            print("[wxpython.py] FocusHandler.OnGotFocus:"
                  " keyboard focus fix (Issue #284)")
            browser.SetFocus(True)


class GeoBrowser:
    BROWSER_CREATED = False

    def __init__(self, parent_wnd):
        if GeoBrowser.BROWSER_CREATED:
            print("Only one browser instance is supported")
            sys.exit(1)

        GeoBrowser.BROWSER_CREATED = True
        cef_xplat_init()

        self.parent_wnd = parent_wnd
        self.browser = None

        # Set wx.WANTS_CHARS style for the keyboard to work.
        # This style also needs to be set for all parent controls.
        self.panel = wx.Panel(self.parent_wnd, style=wx.WANTS_CHARS)
        self.panel.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.panel.Bind(wx.EVT_SIZE, self.OnSize)
        self.panel.Bind(wx.EVT_CLOSE, self.OnClose)

        self.timer_id = 1
        self.timer = wx.Timer(self.panel, self.timer_id)


    def load_browser(self):
        if LINUX:
            # On Linux must show before embedding browser, so that handle
            # is available (Issue #347).
            self.parent_wnd.Show()
            # In wxPython 3.0 and wxPython 4.0 on Linux handle is
            # still not yet available, so must delay embedding browser
            # (Issue #349).
            if wx.version().startswith("3.") or wx.version().startswith("4."):
                wx.CallLater(100, self.embed_browser)
            else:
                # This works fine in wxPython 2.8 on Linux
                self.embed_browser()
        else:
            self.embed_browser()
            self.parent_wnd.Show()

        self.timer_cnt = 0
        self.panel.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(10)  # 10ms timer


    def embed_browser(self):
        window_info = cef.WindowInfo()
        (width, height) = self.panel.GetClientSize().Get()
        assert self.panel.GetHandle(), "Window handle not available"
        window_info.SetAsChild(self.panel.GetHandle(),
                               [0, 0, width, height])
        self.browser = cef.CreateBrowserSync(window_info, url="https://maps.google.com/")
        self.browser.SetClientHandler(FocusHandler())

    
    def on_timer(self, _):
        cef.MessageLoopWork()
        self.timer_cnt -= 1
        if self.timer_cnt <= 0:
            self.timer_cnt = 1000 / self.timer.Interval # 1 second
            self.apply_hacks()


    def apply_hacks(self):
        """ Show a crosshair in the middle of the page """
        hack = "" + \
               "if (!document.getElementById('hack_crosshair')) {" + \
               "var img = document.createElement('img');" + \
               "img.id = 'hack_crosshair';" + \
               "img.src = 'https://raw.githubusercontent.com/nicolasbrailo/IMGeotaggerV3/master/crosshair.png';" + \
               "img.style.position='absolute';" + \
               "img.style.left='50%';" + \
               "img.style.marginLeft='-24px';" + \
               "img.style.top='50%';" + \
               "img.style.marginTop='-24px';" + \
               "document.body.appendChild(img);" + \
               "}"
        self.browser.GetMainFrame().ExecuteJavascript(hack)

    
    def get_coords(self):
        if self.browser is None:
            return None
        return GeoBrowser.hack_coords_from_gmaps(self.browser.GetUrl())


    @staticmethod
    def hack_coords_from_gmaps(map_path):
        """ Tries to get the map coords from the url of a Google maps page """
        #Expected URL format: https://www.google.nl/maps/@37.2870888,22.3544721,4z
        try:
            start_tok = 'maps/@'
            lat_pos = map_path.find(start_tok) + len(start_tok)
            lat_end = map_path.find(',', lat_pos)
            lon_pos = lat_end + 1
            lon_end = map_path.find(',', lon_pos)
            
            if (lat_pos < 0) or (lat_end < 0) or (lon_pos < 0) or (lon_end < 0):
                return None

            return (float(map_path[lat_pos:lat_end]), float(map_path[lon_pos:lon_end]))
        except:
            print("Can't extract coords from this url:", map_path)
            return None


    def OnSetFocus(self, _):
        if not self.browser:
            return
        if WINDOWS:
            cef.WindowUtils.OnSetFocus(self.panel.GetHandle(), 0, 0, 0)
        self.browser.SetFocus(True)


    def OnSize(self, _):
        if not self.browser:
            return
        if WINDOWS:
            cef.WindowUtils.OnSize(self.panel.GetHandle(), 0, 0, 0)
        elif LINUX:
            (x, y) = (0, 0)
            (width, height) = self.panel.GetSize().Get()
            self.browser.SetBounds(x, y, width, height)
        self.browser.NotifyMoveOrResizeStarted()


    def OnClose(self, event):
        print("[wxpython.py] OnClose called")
        if not self.browser:
            # May already be closing, may be called multiple times on Mac
            return

        if MAC:
            # On Mac things work differently, other steps are required
            self.browser.CloseBrowser()
            self.clear_browser_references()
            self.Destroy()
            cef.Shutdown()
            wx.GetApp().ExitMainLoop()
            # Call _exit otherwise app exits with code 255 (Issue #162).
            # noinspection PyProtectedMember
            sys.exit(0)
        else:
            # Calling browser.CloseBrowser() and/or self.Destroy()
            # in OnClose may cause app crash on some paltforms in
            # some use cases, details in Issue #107.
            self.browser.ParentWindowWillClose()
            event.Skip()
            self.clear_browser_references()


    def clear_browser_references(self):
        # Clear browser references that you keep anywhere in your
        # code. All references must be cleared for CEF to shutdown cleanly.
        self.browser = None

    def on_app_exit(self):
        self.timer.Stop()

    @staticmethod
    def static_on_app_exit():
        if not MAC:
            # On Mac shutdown is called in OnClose
            cef.Shutdown()

