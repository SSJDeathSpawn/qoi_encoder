from ast import arg
import numpy as np
import pickle
import sys

from PIL import Image
from file import QOIFile

def has_transparency(img):
    if image.info.get("transparency", None) is not None:
        return True
    if img.mode == "P":
        transparent = img.info.get("transparency", -1)
        for _, index in img.getcolors():
            if index == transparent:
                return True
    elif img.mode == "RGBA":
        extrema = img.getextrema()
        if extrema[3][0] < 255:
            return True
    return False

if __name__=="__main__":
    path = sys.argv[1] if sys.argv and len(sys.argv) > 1 else input("Enter path to image (png):")
    image = Image.open(path + (".png" if path[-4:] != ".png" else ""))
    image = image.convert('RGBA' if (has_transparency(image)) else 'RGB')

    write_path = sys.argv[2] if sys.argv and len(sys.argv) > 2 else input("Enter path of final image (qoi):")
    write_path += (".qoi" if write_path[-4:] != ".qoi" else "")

    np_img = np.asarray(image)
    qoifile = QOIFile(np_img)

    with open(write_path, 'wb') as f:
        f.write(bytes(qoifile))

    print(f"Written to {write_path}. Exiting...")