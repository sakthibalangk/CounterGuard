"""
utils/barcode_reader.py
--------------------------
Decodes a barcode from raw image bytes — whether that image came from
a webcam-captured frame (base64 JPEG from the browser) or an uploaded
photo file. OpenCV handles image decoding; zxing-cpp does the actual
barcode decode.

Note: an earlier version of this module used `pyzbar`, but pyzbar
loads its underlying `zbar` C library via ctypes at runtime, which
turned out to be unreliable on some Windows setups (DLL dependency
loading failures that persisted even after installing the Visual C++
Redistributable). `zxing-cpp` ships as a properly compiled Python
extension with no separate runtime DLL-loading step, which avoids
that whole class of problem.
"""

import cv2
import numpy as np
import zxingcpp


def decode_barcode_from_image_bytes(image_bytes):
    """
    Attempt to decode the first barcode found in `image_bytes`.
    Returns the decoded string value, or None if no barcode could be
    detected in the image at all.
    """
    if not image_bytes:
        return None

    np_arr = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image is None:
        # Not a decodable image at all (corrupt data, wrong format).
        return None

    results = zxingcpp.read_barcodes(image)
    if not results:
        return None

    return results[0].text
