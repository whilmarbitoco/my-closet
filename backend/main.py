# My Closet — Backend (FastAPI)
# Virtual Try-On Engine — OpenCV MVP

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np
import os
import uuid
from typing import Optional
from pydantic import BaseModel

from body_detection import detect_body

app = FastAPI(title="My Closet API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/opt/data/my-closet/uploads"
RESULT_DIR = "/opt/data/my-closet/results"
WARDROBE_DIR = "/opt/data/my-closet/wardrobe"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(WARDROBE_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=RESULT_DIR), name="static")

sessions: dict = {}


class TryOnRequest(BaseModel):
    session_id: str
    clothing_id: str
    category: str


# ─── Clothing Warping ─────────────────────────────────────

def warp_clothing_to_body(
    user_img: np.ndarray,
    clothing_img: np.ndarray,
    keypoints: dict,
    category: str
) -> np.ndarray:
    h, w = user_img.shape[:2]

    if category == "top":
        dst_pts = np.float32([
            [keypoints["left_shoulder"][0] - 10, keypoints["left_shoulder"][1] - 5],
            [keypoints["right_shoulder"][0] + 10, keypoints["right_shoulder"][1] - 5],
            [
                keypoints["right_hip"][0] + int(keypoints["hip_width"] * 0.3),
                int((keypoints["left_hip"][1] + keypoints["right_hip"][1]) / 2)
            ],
            [
                keypoints["left_hip"][0] - int(keypoints["hip_width"] * 0.3),
                int((keypoints["left_hip"][1] + keypoints["right_hip"][1]) / 2)
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
        [0, clothing_img.shape[0]]
    ])

    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(clothing_img, matrix, (w, h), borderMode=cv2.BORDER_TRANSPARENT)
    return warped


# ─── Composite Rendering ──────────────────────────────────

def composite_images(user_img: np.ndarray, warped_clothing: np.ndarray) -> np.ndarray:
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


# ─── Simple Background Removal (no rembg) ─────────────────

def simple_bg_remove(image_path: str, output_path: str) -> bool:
    """Simple background removal using color thresholding. MVP quality."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return False

        # Convert to HSV and create mask for non-white/non-uniform backgrounds
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Detect white/light background
        lower_white = np.array([0, 0, 180])
        upper_white = np.array([180, 30, 255])
        bg_mask = cv2.inRange(hsv, lower_white, upper_white)

        # Invert: we want the person/clothing, not the background
        fg_mask = cv2.bitwise_not(bg_mask)

        # Clean up with morphological operations
        kernel = np.ones((5, 5), np.uint8)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)

        # Apply mask as alpha channel
        bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        bgra[:, :, 3] = fg_mask

        cv2.imwrite(output_path, bgra)
        return True
    except Exception as e:
        print(f"BG removal failed: {e}")
        return False


# ─── API Endpoints ────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "app": "My Closet API", "version": "0.1.0"}


@app.post("/api/session/create")
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {"user_photo": None, "keypoints": None, "wardrobe": [], "results": []}
    return {"session_id": session_id}


@app.post("/api/user/upload")
async def upload_user_photo(session_id: str, file: UploadFile = File(...)):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"user_{session_id}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    with open(filepath, "wb") as f:
        f.write(contents)

    keypoints = detect_body(filepath)
    if keypoints is None:
        raise HTTPException(status_code=400, detail="Could not detect body. Use a clear full-body photo.")

    sessions[session_id]["user_photo"] = filename
    sessions[session_id]["keypoints"] = keypoints

    return {"status": "ok", "filename": filename, "keypoints_detected": True}


@app.post("/api/wardrobe/upload")
async def upload_clothing(session_id: str, category: str = "top", file: UploadFile = File(...)):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    if category not in ("top", "bottom", "dress", "jacket"):
        raise HTTPException(status_code=400, detail="Invalid category")
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    clothing_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"{clothing_id}.{ext}"
    filepath = os.path.join(WARDROBE_DIR, filename)

    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    # Try simple background removal
    no_bg_path = os.path.join(WARDROBE_DIR, f"{clothing_id}_nobg.png")
    bg_removed = simple_bg_remove(filepath, no_bg_path)

    item = {
        "id": clothing_id,
        "category": category,
        "original": filename,
        "no_background": f"{clothing_id}_nobg.png" if bg_removed else None,
    }
    sessions[session_id]["wardrobe"].append(item)

    return {"status": "ok", "clothing_id": clothing_id, "category": category, "background_removed": bg_removed}


@app.get("/api/wardrobe/{session_id}")
def get_wardrobe(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"wardrobe": sessions[session_id]["wardrobe"]}


@app.post("/api/try-on")
async def try_on(request: TryOnRequest):
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[request.session_id]
    if not session.get("user_photo"):
        raise HTTPException(status_code=400, detail="Upload a user photo first")

    clothing_item = next((i for i in session["wardrobe"] if i["id"] == request.clothing_id), None)
    if not clothing_item:
        raise HTTPException(status_code=404, detail="Clothing item not found")

    user_path = os.path.join(UPLOAD_DIR, session["user_photo"])
    if clothing_item.get("no_background"):
        clothing_path = os.path.join(WARDROBE_DIR, clothing_item["no_background"])
    else:
        clothing_path = os.path.join(WARDROBE_DIR, clothing_item["original"])

    user_img = cv2.imread(user_path)
    clothing_img = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)

    if user_img is None:
        raise HTTPException(status_code=500, detail="Failed to load user image")
    if clothing_img is None:
        raise HTTPException(status_code=500, detail="Failed to load clothing image")

    keypoints = session.get("keypoints")
    if not keypoints:
        raise HTTPException(status_code=500, detail="No body data. Re-upload user photo.")

    warped = warp_clothing_to_body(user_img, clothing_img, keypoints, request.category)
    result = composite_images(user_img, warped)

    result_id = str(uuid.uuid4())
    result_filename = f"{result_id}.jpg"
    result_path = os.path.join(RESULT_DIR, result_filename)
    cv2.imwrite(result_path, result)

    result_data = {
        "id": result_id,
        "clothing_id": request.clothing_id,
        "category": request.category,
        "filename": result_filename,
        "url": f"/static/{result_filename}"
    }
    session["results"].append(result_data)

    return {"status": "ok", "result_id": result_id, "image_url": f"/static/{result_filename}"}


@app.get("/api/results/{session_id}")
def get_results(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"results": sessions[session_id]["results"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
