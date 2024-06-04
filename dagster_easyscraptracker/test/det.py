import cv2
import torch
import numpy as np

from segment_anything import (
  sam_model_registry, 
  SamAutomaticMaskGenerator, 
  SamPredictor
)

def resize_img(img, scale_factor):
  return cv2.resize(
    img,
    None,
    fx=scale_factor, 
    fy=scale_factor, 
    interpolation=cv2.INTER_AREA
  )

# Read image
img = cv2.imread("./data/13.32.08[R][0@0][0][0].jpeg")

# Load model
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
MODEL_TYPE = "vit_h"
CHECKPOINT_PATH  = "./dagster_easyscraptracker/models/sam/sam_vit_h_4b8939.pth"

sam = sam_model_registry[MODEL_TYPE](checkpoint=CHECKPOINT_PATH)
sam.to(device=DEVICE)

predictor = SamPredictor(sam)

# Select ROI
scale_factor = 0.3
img_resize = resize_img(img, scale_factor)

roi = cv2.selectROI(img_resize, False)
cv2.destroyAllWindows()

roi_orig = (
  int(roi[0] / scale_factor), 
  int(roi[1] / scale_factor),
  int(roi[2] / scale_factor),
  int(roi[3] / scale_factor)
)

box = np.array([
  roi_orig[0], 
  roi_orig[1], 
  roi_orig[0] + roi_orig[2], 
  roi_orig[1] + roi_orig[3]
])

# Get masks from a given prompt (scrap)
predictor.set_image(img)
masks, _, _ = predictor.predict(
    box=box,
    multimask_output=False
)

scrap_mask = np.transpose(masks.astype(np.uint8) * 255, (1, 2, 0))
scrap_mask = cv2.merge([scrap_mask, scrap_mask, scrap_mask])
cv2.imshow("Scrap mask", resize_img(scrap_mask, scale_factor))
cv2.waitKey(0)

# Crop scrap from source image
result = cv2.bitwise_and(img, scrap_mask)
scrap = result[roi_orig[1]:roi_orig[1]+roi_orig[3], roi_orig[0]:roi_orig[0]+roi_orig[2]]
cv2.imshow("Scrap", resize_img(scrap, scale_factor))
cv2.waitKey(0)

cv2.destroyAllWindows()

# Generate masks for an entire image (from scrap)
mask_generator = SamAutomaticMaskGenerator(
    model=sam,
    points_per_side=32,
    pred_iou_thresh=0.86,
    stability_score_thresh=0.92,
    crop_n_layers=1,
    crop_n_points_downscale_factor=2,
    min_mask_region_area=100,
    output_mode="binary_mask"
)

masks = mask_generator.generate(scrap)

for i, mask in enumerate(masks):
  x, y, w, h = mask["bbox"]

  detection = scrap[y:y+h, x:x+w]
  cv2.imwrite(f"./results/0/{i}.jpg", detection)

  # cv2.rectangle(scrap, (x, y), (x+w, y+h), (255,0,0), thickness=2)
  # cv2.imshow("Results", resize_img(scrap, scale_factor))
  # cv2.waitKey(0)
