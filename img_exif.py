from fractions import Fraction
import math
import pyexiv2

LAT_KEY = 'Exif.GPSInfo.GPSLatitude'
LON_KEY = 'Exif.GPSInfo.GPSLongitude'
LAT_REF_KEY = 'Exif.GPSInfo.GPSLatitudeRef'
LON_REF_KEY = 'Exif.GPSInfo.GPSLongitudeRef'


def dec_to_sex(x):
    degs = int(math.floor(x))
    mins = int(math.floor(60 * (x - degs)))
    secs = round((((x - degs) * 60) - mins) * 60, 4)
    return (degs, mins, secs)


def dec_to_frac(dec):
    def frac(n):
        f = Fraction(n).limit_denominator()
        return str(f.numerator) + '/' + str(f.denominator)
    return ' '.join([frac(x) for x in list(dec_to_sex(abs(float(dec))))])


def sex_to_dec(s):
    (degs, mins, secs) = s
    return degs + ((mins + (secs / 60.)) / 60.)


def frac_to_sex(f):
    def num(n):
        n = n.split('/')
        den = int(n[1])
        if den == 0:
            den = 1
        return float(int(n[0])) /den 
    if f == None or len(f.split()) != 3:
        return None
    ns = [num(x) for x in f.split()]
    return ns[0], ns[1], ns[2]


def frac_to_dec(f):
    f = frac_to_sex(f)
    return sex_to_dec(f) if f else None


def get_exif_position(path):
    try:
        meta = pyexiv2.Image(path).read_exif()
    except RuntimeError:
        print(f"Error loading metadata for {path}")
        return None

    try:
        lat = frac_to_dec(meta[LAT_KEY])
        lon = frac_to_dec(meta[LON_KEY])
        if lat is None or lon is None:
            print(f"Error loading position for {path}, lat/lon wasn't a number")
            return None

        lat_ref = meta[LAT_REF_KEY]
        if lat_ref.upper() not in ['N', 'S']:
            print(f"Error loading position for {path}, lat ref wasn't valid")
            return None

        lon_ref = meta[LON_REF_KEY]
        if lon_ref.upper() not in ['W', 'E']:
            print(f"Error loading position for {path}, lon ref wasn't valid")
            return None

        return f"{lat:.5f}{lat_ref} {lon:.5f}{lon_ref}"
    except KeyError:
        return None


def set_exif_position(path, coords):
    try:
        img = pyexiv2.Image(path)
    except RuntimeError:
        print(f"Error loading image metadata for {path}")
        return False

    lat, lon = coords
    frac_lat = dec_to_frac(lat)
    frac_lon = dec_to_frac(lon)
    lat_ref = 'S' if lat < 0 else 'N'
    lon_ref = 'W' if lon < 0 else 'E'

    img.modify_exif({
        LAT_KEY: frac_lat,
        LON_KEY: frac_lon,
        LAT_REF_KEY: lat_ref,
        LON_REF_KEY: lon_ref,
    })

    return True

