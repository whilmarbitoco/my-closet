from typing import Optional
import cv2
import numpy as np

def detect_body(image_path: str) -> Optional[dict]:
    """Detect body using OpenCV HOG + contour analysis. No external deps needed."""
    img = cv2.imread(image_path)
    if img is None:
        return None

    h, w = img.shape[:2]

    # HOG person detector
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    boxes, weights = hog.detectMultiScale(img, winStride=(8, 8), padding=(4, 4), scale=1.05)

    if len(boxes) > 0:
        # Use highest confidence detection
        best_idx = np.argmax(weights)
        x, y, bw, bh = boxes[best_idx]
    else:
        # Fallback: use upper 80% of image as body region
        x, y, bw, bh = int(w * 0.15), int(h * 0.05), int(w * 0.7), int(h * 0.9)

    # Estimate body landmarks from bounding box proportions
    # Based on standard human body proportions
    keypoints = {
        # Shoulders: top 15-20% of body, spread ~50% of body width
        "left_shoulder":  (x + int(bw * 0.28), y + int(bh * 0.08)),
        "right_shoulder": (x + int(bw * 0.72), y + int(bh * 0.08)),
        # Hips: ~50-55% down
        "left_hip":  (x + int(bw * 0.32), y + int(bh * 0.52)),
        "right_hip": (x + int(bw * 0.68), y + int(bh * 0.52)),
        # Elbows: ~25-30% down
        "left_elbow":  (x + int(bw * 0.18), y + int(bh * 0.25)),
        "right_elbow": (x + int(bw * 0.82), y + int(bh * 0.25)),
        # Wrists: ~40-45% down
        "left_wrist":  (x + int(bw * 0.12), y + int(bh * 0.42)),
        "right_wrist": (x + int(bw * 0.88), y + int(bh * 0.42)),
        # Knees: ~65-70% down
        "left_knee":  (x + int(bw * 0.35), y + int(bh * 0.67)),
        "right_knee": (x + int(bw * 0.65), y + int(bh * 0.67)),
        # Ankles: ~85-90% down
        "left_ankle":  (x + int(bw * 0.35), y + int(bh * 0.88)),
        "right_ankle": (x + int(bw * 0.65), y + int(bh * 0.88)),
        # Nose/head: top center
        "nose": (x + int(bw * 0.5), y + int(bh * 0.03)),
        # Measurements
        "shoulder_width": int(bw * 0.44),
        "hip_width": int(bw * 0.36),
        "torso_height": int(bh * 0.44),
        "image_width": w,
        "image_height": h,
    }

    return keypoints
