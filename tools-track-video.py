"""Pose tracking with a crop that follows the skater, full-resolution source, time window."""
import sys, numpy as np, cv2, mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
src, out, t0, t1 = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
opts = vision.PoseLandmarkerOptions(base_options=python.BaseOptions(model_asset_path='pose_landmarker_heavy.task'),
    running_mode=vision.RunningMode.VIDEO, num_poses=1, min_pose_detection_confidence=.3, min_tracking_confidence=.3, min_pose_presence_confidence=.3)
lm = vision.PoseLandmarker.create_from_options(opts)
cap = cv2.VideoCapture(src); fps = cap.get(cv2.CAP_PROP_FPS) or 30
cap.set(cv2.CAP_PROP_POS_FRAMES, int(t0*fps))
rows=[]; box=None; i=int(t0*fps); n=0
while i < int(t1*fps):
    ok, frame = cap.read()
    if not ok: break
    H, Wd = frame.shape[:2]
    if box is None: x0,y0,x1,y1 = 0,0,Wd,H
    else:
        cx,cy,s = box; s=max(s,220); x0=int(max(0,cx-s)); x1=int(min(Wd,cx+s)); y0=int(max(0,cy-s)); y1=int(min(H,cy+s))
    crop = frame[y0:y1, x0:x1]
    scale = 768/max(crop.shape[:2]); crop = cv2.resize(crop, (int(crop.shape[1]*scale), int(crop.shape[0]*scale)))
    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    r = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), int(n*1000/fps)); n+=1
    if r.pose_world_landmarks:
        wl = r.pose_world_landmarks[0]; il = r.pose_landmarks[0]
        rows.append([[p.x, p.y, p.z, p.visibility] for p in wl])
        xs=[p.x for p in il]; ys=[p.y for p in il]
        cw, ch = crop.shape[1]/scale, crop.shape[0]/scale
        cx = x0 + np.mean(xs)*cw; cy = y0 + np.mean(ys)*ch; s = max(np.ptp(ys)*ch, np.ptp(xs)*cw)*1.3
        box = (cx, cy, s)
    else:
        rows.append([[np.nan]*4]*33); box = None
    i += 1
R=np.array(rows); print('frames', len(R), 'detected', int(np.sum(~np.isnan(R[:,0,0]))))
np.savez(out, world=R, fps=fps, t0=t0)
