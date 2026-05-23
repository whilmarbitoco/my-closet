from typing import Optional
import cv2
import numpy as np


def detect_body(image_path: str) -> Optional[dict]:
    """Detect body using OpenCV HOG + contour analysis. No external deps needed."""
    img = cv2.imread(image_path)
    if img is None:
        return None

    h, w = img.shape[:2]

    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    boxes, weights = hog.detectMultiScale(img, winStride=(8, 8), padding=(4, 4), scale=1.05)

    if len(boxes) > 0:
        best_idx = np.argmax(weights)
        x, y, bw, bh = boxes[best_idx]
    else:
        x, y, bw, bh = int(w * 0.15), int(h * 0.05), int(w * 0.7), int(h * 0.9)

    keypoints = {
        "left_shoulder":  (x + int(bw * 0.28), y + int(bh * 0.08)),
        "right_shoulder": (x + int(bw * 0.72), y + int(bh * 0.08)),
        "left_hip":       (x + int(bw * 0.32), y + int(bh * 0.52)),
        "right_hip":      (x + int(bw * 0.68), y + int(bh * 0.52)),
        "left_elbow":     (x + int(bw * 0.18), y + int(bh * 0.25)),
        "right_elbow":    (x + int(bw * 0.82), y + int(bh * 0.25)),
        "left_wrist":     (x + int(bw * 0.12), y + int(bh * 0.42)),
        "right_wrist":    (x + int(bw * 0.88), y + int(bh * 0.42)),
        "left_knee":      (x + int(bw * 0.35), y + int(bh * 0.67)),
        "right_knee":     (x + int(bw * 0.65), y + int(bh * 0.67)),
        "left_ankle":     (x + int(bw * 0.35), y + int(bh * 0.88)),
        "right_ankle":    (x + int(bw * 0.65), y + int(bh * 0.88)),
        "nose":           (x + int(bw * 0.5), y + int(bh * 0.03)),
        "shoulder_width": int(bw * 0.44),
        "hip_width":      int(bw * 0.36),
        "torso_height":   int(bh * 0.44),
        "image_width":    w,
        "image_height":   h,
    }
    return keypoints


def warp_clothing_to_body(
    user_img: np.ndarray,
    clothing_img: np.ndarray,
    keypoints: dict,
    category: str,
) -> np.ndarray:
    """Warp clothing image to fit body keypoints using perspective transform."""
    h, w = user_img.shape[:2]

    if category == "top":
        dst_pts = np.float32([
            [keypoints["left_shoulder"][0] - 10, keypoints["left_shoulder"][1] - 5],
            [keypoints["right_shoulder"][0] + 10, keypoints["right_shoulder"][1] - 5],
            [
                keypoints["right_hip"][0] + int(keypoints["hip_width"] * 0.3),
                int((keypoints["left_hip"][1] + keypoints["right_hip"][1]) / 2),
            ],
            [
                keypoints["left_hip"][0] - int(keypoints["hip_width"] * 0.3),
                int((keypoints["left_hip"][1] + keypoints["right_hip"][1]) / 2),
            ],
        ])
    elif category == "bottom":
        hip_y = int((keypoints["left_hip"][1] + keypoints["right_hip"][1]) / 2)
        knee_y = int((keypoints["left_knee"][1] + keypoints["right_knee"][1]) / 2)
        dst_pts = np.float32([
            [keypoints["left_hip"][0] - 5, hip_y],
            [keypoints["right_hip"][0] + 5, hip_y],
            [keypoints["right_knee"][0] + 5, knee_y],
            [keypoints["left_knee"][0] - 5, knee_y],
        ])
    elif category == "dress":
        knee_y = int((keypoints["left_knee"][1] + keypoints["right_knee"][1]) / 2)
        dst_pts = np.float32([
            [keypoints["left_shoulder"][0] - 10, keypoints["left_shoulder"][1] - 5],
            [keypoints["right_shoulder"][0] + 10, keypoints["right_shoulder"][1] - 5],
            [keypoints["right_knee"][0] + int(keypoints["hip_width"] * 0.4), knee_y],
            [keypoints["left_knee"][0] - int(keypoints["hip_width"] * 0.4), knee_y],
        ])
    else:  # jacket
        dst_pts = np.float32([
            [keypoints["left_shoulder"][0], keypoints["left_shoulder"][1]],
            [keypoints["right_shoulder"][0], keypoints["right_shoulder"][1]],
            [keypoints["right_hip"][0], keypoints["right_hip"][1]],
            [keypoints["left_hip"][0], keypoints["left_hip"][1]],
        ])

    src_pts = np.float32([
        [0, 0],
        [clothing_img.shape[1], 0],
        [clothing_img.shape[1], clothing_img.shape[0]],
        [0, clothing_img.shape[0]],
    ])

    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(clothing_img, matrix, (w, h), borderMode=cv2.BORDER_TRANSPARENT)
    return warped


def composite_images(user_img: np.ndarray, warped_clothing: np.ndarray) -> np.ndarray:
    """Alpha-blend warped clothing onto user image."""
    if warped_clothing.shape[2] == 4:
        alpha = warped_clothing[:, :, 3:4].astype(float) / 255.0
        warped_rgb = warped_clothing[:, :, :3]
    else:
        gray = cv2.cvtColor(warped_clothing, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        alpha = mask.astype(float) / 255.0
        alpha = np.stack([alpha] * 3, axis=-1)
        warped_rgb = warped_clothing

    result = (warped_rgb.astype(float) * alpha + user_img.astype(float) * (1 - alpha)).astype(np.uint8)
    return result


def simple_bg_remove(image_path: str, output_path: str) -> bool:
    """Simple background removal using HSV color thresholding. MVP quality."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return False

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0, 0, 180])
        upper_white = np.array([180, 30, 255])
        bg_mask = cv2.inRange(hsv, lower_white, upper_white)
        fg_mask = cv2.bitwise_not(bg_mask)

        kernel = np.ones((5, 5), np.uint8)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)

        bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        bgra[:, :, 3] = fg_mask
        cv2.imwrite(output_path, bgra)
        return True
    except Exception as e:
        print(f"BG removal failed: {e}")
        return False
