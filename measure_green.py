import cv2
import numpy as np

img = cv2.imread('/Users/kosta/.gemini/antigravity/brain/c8ee4d6f-219a-45e7-ba86-3151e9bd0b1a/.user_uploaded/media_1790696675849.png')
# Find PURE GREEN (0, 255, 0)
lower_green = np.array([0, 200, 0])
upper_green = np.array([50, 255, 50])
mask = cv2.inRange(img, lower_green, upper_green)

y_coords, x_coords = np.where(mask > 0)
if len(x_coords) > 0:
    w = np.max(x_coords) - np.min(x_coords)
    h = np.max(y_coords) - np.min(y_coords)
    print(f"Green Square: W={w}, H={h}")
    print(f"Position: X({np.min(x_coords)}-{np.max(x_coords)}), Y({np.min(y_coords)}-{np.max(y_coords)})")

    # Find cyan bounding box for comparison
    lower_cyan = np.array([200, 200, 0])
    upper_cyan = np.array([255, 255, 50])
    mask2 = cv2.inRange(img, lower_cyan, upper_cyan)
    cy, cx = np.where(mask2 > 0)
    print(f"Cyan Width: {np.max(cx) - np.min(cx)}")
