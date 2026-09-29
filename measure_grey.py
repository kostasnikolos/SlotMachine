import cv2
import numpy as np

img = cv2.imread('/Users/kosta/.gemini/antigravity/brain/c8ee4d6f-219a-45e7-ba86-3151e9bd0b1a/.user_uploaded/media_1790697780538.png')

# Let's crop a small patch from the top left square (Row 0, Col 0)
# Looking at the grid, the top left square starts around X=400, Y=350.
# Let's just print the RGB of the pixel at (400, 350) and a 10x10 area around it.
patch = img[350:360, 400:410]
print("Row 0 Col 0 (Dark Grey):", np.mean(patch, axis=(0,1)))

# Let's crop Row 4 Col 4
patch2 = img[750:760, 650:660]
print("Row 4 Col 4 (Dark Grey):", np.mean(patch2, axis=(0,1)))

# Let's find exactly 0x111111 (which is 17, 17, 17 in RGB)
mask = cv2.inRange(img, np.array([16,16,16]), np.array([18,18,18]))
y, x = np.where(mask > 0)
print(f"Pixels with RGB ~17,17,17: {len(x)}")
