from collections import namedtuple
from img_exif import get_exif_position, set_exif_position
import math
import os
import sys
import tempfile
import wx

Img = namedtuple('Img', 'preview path fname coords_set')

class ImgManager:
    def __init__(self, preview_size, start_path=None):
        self._allowed_extensions = ['JPG', 'JPEG']
        self.preview_size = preview_size
        self.imgs = []
        if start_path is not None:
            self.reload(start_path)


    def reload(self, path):
        # TODO this is slow and blocks the UI thread
        # To speed it up, it should load the images in a bg thread and notify
        # the UI thread as images become available
        self.imgs = []
        self.positions_cache = {}
        if not os.path.isdir(path): return

        lst = os.listdir(path)
        lst.sort()
        files = []
        for filename in lst:
            for ext in self._allowed_extensions:
                if filename.upper().endswith(ext.upper()):
                    files.append(os.path.join(path, filename))

        previews = []
        for file_path in files:
            try:
                print(f"Loading {file_path}")
                preview = wx.Image(file_path , wx.BITMAP_TYPE_ANY)
                preview = preview.Scale(*self.preview_size, wx.IMAGE_QUALITY_NORMAL)
                preview = wx.Bitmap(preview)
                previews.append((file_path, preview))
            except:
                print(f"Error loading {file_path}", sys.exc_info()[0])

        for (path, preview) in previews:
            try:
                coords_set = 'Y' if self.get_position(path) is not None else 'N'
            except:
                print(f"Error loading coords for {file_path}", sys.exc_info()[0])
                coords_set = 'N'

            self.imgs.append(Img(preview=preview,
                            path=path,
                            fname=os.path.split(path)[1],
                            coords_set=coords_set))


    def get_full_path_for(self, fname):
        for img in self.imgs:
            if img.fname == fname:
                return img.path
        return None


    def get_description_for(self, files):
        if files == None or len(files) == 0:
            file_selection = 'No file selected'
            file_coord = "-"
        elif len(files) == 1:
            file_selection = files[0]
            file_coord = self.get_position(self.get_full_path_for(files[0]))
        else:
            file_selection = 'Multiple files selected'
            coord_0 = self.get_position(self.get_full_path_for(files[0]))
            file_coord = str(coord_0)
            for fn in files:
                coord = self.get_position(self.get_full_path_for(fn))
                if coord != coord_0:
                    file_coord = 'Multiple positions'
                    break

        return f"{file_selection}\nFile position: {file_coord}"""


    def set_positions_for(self, pos, paths):
        if pos is None:
            print("Cowardly refusing to set null coords, bailing out")
            return

        for fn in paths:
            fullpath = self.get_full_path_for(fn)
            if set_exif_position(fullpath, pos):
                self.positions_cache[fullpath] = pos
                print("Set", fn, "to position", pos)
            else:
                print("Failed setting", fn, "to position", pos)


    def get_position(self, path):
        if path not in self.positions_cache:
            self.positions_cache[path] = get_exif_position(path)
        return self.positions_cache[path]

