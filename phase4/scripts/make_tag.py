from pathlib import Path
import cv2

root = Path(__file__).resolve().parents[1]
out = root / 'assets'
out.mkdir(exist_ok=True)
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
tag = cv2.aruco.generateImageMarker(dictionary, 0, 1000)
tag = cv2.copyMakeBorder(tag, 125, 125, 125, 125, cv2.BORDER_CONSTANT, value=255)
target = out / 'tag_0.png'
cv2.imwrite(str(target), tag)
print(f'Created {target}. Print at 100% and measure the black square side.')
