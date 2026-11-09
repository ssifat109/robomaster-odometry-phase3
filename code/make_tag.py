"""Generate an A4, 140 mm black-square AprilTag 36h11 ID 3 at exact scale."""
from io import BytesIO
from pathlib import Path

import cv2
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

MM = 72 / 25.4
PAGE_W, PAGE_H = 210 * MM, 297 * MM
BLACK_MM = 140
WHITE_BORDER_MM = 8

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
bitmap = cv2.aruco.drawMarker(dictionary, 3, 1800, borderBits=1)
ok, png = cv2.imencode(".png", bitmap)
if not ok:
    raise RuntimeError("Marker PNG encoding failed")

out = Path(__file__).resolve().parents[1] / "tags" / "apriltag3_140mm_A4.pdf"
canvas = Canvas(str(out), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
canvas.setTitle("RoboMaster AprilTag 36h11 ID 3 - 140 mm")
canvas.setFont("Helvetica-Bold", 13)
canvas.drawCentredString(PAGE_W / 2, PAGE_H - 17 * MM,
                         "RoboMaster target: AprilTag 36h11, ID 3")
canvas.setFont("Helvetica", 9)
canvas.drawCentredString(PAGE_W / 2, PAGE_H - 24 * MM,
                         "Print A4 at Actual size / 100%. Disable Fit to page.")

side = (BLACK_MM + 2 * WHITE_BORDER_MM) * MM
left = (PAGE_W - side) / 2
bottom = 68 * MM
canvas.setFillColorRGB(1, 1, 1)
canvas.rect(left, bottom, side, side, stroke=0, fill=1)
canvas.drawImage(ImageReader(BytesIO(png.tobytes())),
                 left + WHITE_BORDER_MM * MM,
                 bottom + WHITE_BORDER_MM * MM,
                 BLACK_MM * MM, BLACK_MM * MM, mask="auto")
canvas.setStrokeColorRGB(0.35, 0.35, 0.35)
canvas.setDash(2, 2)
canvas.rect(left, bottom, side, side, stroke=1, fill=0)
canvas.setDash()
canvas.setFont("Helvetica", 9)
canvas.drawCentredString(PAGE_W / 2, bottom - 7 * MM,
                         "Black square: 140 x 140 mm; outer cut square: 156 x 156 mm")
canvas.drawCentredString(PAGE_W / 2, bottom - 13 * MM,
                         "Keep the white border and mount the sheet flat.")
line_y = 13 * MM
canvas.line((PAGE_W - 100 * MM) / 2, line_y,
            (PAGE_W + 100 * MM) / 2, line_y)
canvas.drawCentredString(PAGE_W / 2, 7 * MM,
                         "Scale check: line above must measure 100 mm")
canvas.showPage()
canvas.save()
print(out)
