import cv2
import numpy as np

# Load user screenshot
img = cv2.imread('/Users/kosta/.gemini/antigravity/brain/c8ee4d6f-219a-45e7-ba86-3151e9bd0b1a/.user_uploaded/media_1790693012012.png')

# Convert to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Find the bright cyan border of the viewport-outer-frame
# Cyan is roughly BGR (255, 240, 0) in OpenCV (B,G,R). We can just use Canny edge detection.
edges = cv2.Canny(gray, 50, 150)
y_coords, x_coords = np.where(edges > 0)

print(f"Image shape: {img.shape}")
print(f"Edges bounding box: X({np.min(x_coords)}-{np.max(x_coords)}), Y({np.min(y_coords)}-{np.max(y_coords)})")

