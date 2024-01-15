import gc
import jpegdec
from urllib import urequest
from ujson import load

gc.collect()

graphics = None
WIDTH = None
HEIGHT = None

FILENAME = "webgallery-cache"

# Length of time between updates in minutes.
# Frequent updates will reduce battery life!
UPDATE_INTERVAL = 5

def show_error(text):
    graphics.set_pen(4)
    graphics.rectangle(0, 10, WIDTH, 35)
    graphics.set_pen(1)
    graphics.text(text, 5, 16, 400, 2)

def update():
    IMG_URL = "https://CLOUD_FUNCTION_HOST_URL/serve_image"

    try:
        # Grab the image
        
        socket = urequest.urlopen(IMG_URL)

        gc.collect()

        data = bytearray(1024)
        with open(FILENAME, "wb") as f:
            while True:
                if socket.readinto(data) == 0:
                    break
                f.write(data)
        socket.close()
        del data
        gc.collect()
    except OSError as e:
        print(e)
        show_error("Unable to download image")


def draw():
    jpeg = jpegdec.JPEG(graphics)
    gc.collect()  # For good measure...

    graphics.set_pen(1)
    graphics.clear()

    try:
        jpeg.open_file(FILENAME)
        jpeg.decode(0, 0, jpegdec.JPEG_SCALE_FULL)
    except OSError:
        graphics.set_pen(4)
        graphics.rectangle(0, (HEIGHT // 2) - 20, WIDTH, 40)
        graphics.set_pen(1)
        graphics.text("Unable to display image!", 5, (HEIGHT // 2) - 15, WIDTH, 2)
        graphics.text("Check your network settings in secrets.py", 5, (HEIGHT // 2) + 2, WIDTH, 2)

    gc.collect()

    graphics.update()
