from collections import namedtuple
import exif
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
                coords_set = 'Y' if ImgManager.get_position(path) is not None else 'N'
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
        if files == None:
            file_selection = 'No file selected'
            file_coord = "-"
        elif len(files) == 1:
            file_selection = files[0]
            file_coord = ImgManager.get_position(self.get_full_path_for(files[0]))
        else:
            file_selection = 'Multiple files selected'
            coord_0 = ImgManager.get_position(self.get_full_path_for(files[0]))
            file_coord = str(coord_0)
            for fn in files:
                coord = ImgManager.get_position(self.get_full_path_for(fn))
                if coord != coord_0:
                    file_coord = 'Multiple positions'
                    break

        return f"{file_selection}\nFiles position: {file_coord}"""


    def set_positions_for(self, pos, paths):
        if pos is None:
            print("Cowardly refusing to set null coords, bailing out")
            return

        for fn in paths:
            fullpath = self.get_full_path_for(fn)
            if ImgManager.set_position(fullpath, pos):
                print("Set", fn, "to position", pos)
            else:
                print("Failed setting", fn, "to position", pos)


    @staticmethod
    def set_position(path, coords):
        try:
            img = exif.Image(path)
        except:
            print(f"Couldn't open image metadata for {path}")
            return False

        lat, lon = coords
        img.gps_latitude = ImgManager._dec_to_sex(lat)
        img.gps_longitude = ImgManager._dec_to_sex(lon)
        img.gps_latitude_ref = 'S' if lat < 0 else 'N'
        img.gps_longitude_ref = 'W' if lon < 0 else 'E'

        try:
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.write(img.get_file())
            tmp.close()
            os.replace(tmp.name, path)
            return True
        except:
            print(f"Error saving coords for {file_path}", sys.exc_info()[0])
            return False


    @staticmethod
    def get_position(path):
        try:
            img = exif.Image(path)
        except:
            print(f"Couldn't open image metadata for {path}")
            return None

        try:
            lat = ImgManager._sex_to_dec(img.gps_latitude)
            lon = ImgManager._sex_to_dec(img.gps_longitude)
            return f"{lat:.5f}{img.gps_latitude_ref} {lon:.5f}{img.gps_longitude_ref}"
        except ValueError:
            return None
        except KeyError:
            return None


    @staticmethod
    def _dec_to_sex(x):
        x = abs(x)
        degs = int(math.floor(x))
        mins = int(math.floor(60 * (x - degs)))
        secs = round(60 * (60 * (x - degs) - mins), 4)
        return (degs, mins, secs)


    @staticmethod
    def _sex_to_dec(s):
        (degs, mins, secs) = s
        return degs + ((mins + (secs / 60.)) / 60.)


