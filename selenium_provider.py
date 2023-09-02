# configure Firefox / Selenium
from selenium.webdriver import FirefoxOptions
from selenium import webdriver

MIME_TYPES = [
    "text/plain",
    "text/css",
    "text/javascript",
    "binary/octet-stream",
    "application/octet-stream",
    "text/xml",
    "application/xml",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
    "image/gif",
    # .dxf
    "image/vnd.dxf",
    # .dwg
    "image/vnd.dwg",
    # .ps
    "image/vnd.adobe.photoshop",
    # .bmp
    "image/bmp",
    "image/x-bmp",
    "image/x-bitmap",
    "image/x-xbitmap",
    "image/x-win-bitmap",
    "image/x-windows-bmp",
    "image/ms-bmp",
    "image/x-ms-bmp",
    "application/bmp",
    "application/x-bmp",
    "application/x-win-bitmap",
    # .tga
    "image/tga",
    "image/x-tga",
    "image/x-targa",
    "application/tga",
    "application/x-tga",
    "application/x-targa",
    "application/x-rar-compressed",
    "application/x-7z-compressed",
    # .zip
    "application/zip",
    "application/x-zip-compressed",
    "multipart/x-zip",
    # .obj
    "application/x-tgif",
    # .blend
    "application/x-blender",
    # .c4d (technically wrong MIME-type for Cinema 4D)
    "application/vnd.clonk.c4group",
    # .3ds, .max
    "image/x-3ds",
    "image/x-3s",
    "application/x-3ds",
    "model/stl",
    # .x3d, .x3dz, .x3db, .x3dbz, .x3dv, .x3dvz
    "model/x3d",
    "model/x3d+xml",
    "model/x3d+vrml",
    "model/x3d+binary",
    # .dae
    "model/vnd.collada",
    "model/vnd.collada+xml",
    "audio/vnd.dts",
    # .mp4
    "application/mp4",
    "video/mp4",
]


def get_driver(download_folder):
    firefox_options = FirefoxOptions()

    firefox_options.page_load_strategy = "eager"

    # don't ask to send notifications
    firefox_options.set_preference("dom.webnotifications.enabled", False)

    # download without asking to preconfigured folder
    firefox_options.set_preference("browser.download.folderList", 2)
    firefox_options.set_preference("browser.download.dir", download_folder)
    firefox_options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk", ";".join(MIME_TYPES) + ";"
    )

    # don't show the download progress popup
    firefox_options.set_preference("browser.download.panel.shown", False)

    firefox_options.set_capability(
        "moz:firefoxOptions",
        {
            "args": [
                "-profile",
            ]
        },
    )

    driver = webdriver.Firefox(options=firefox_options)
    return driver
