"""Scan a tracked clip for jump candidates: runs of detection, then within each run the
ankle/hip signals. Prints per-run summary and the best flight windows."""
import sys, numpy as np
npz = np.load(sys.argv[1]); W = npz['world']; fps = float(npz['fps']); t0 = float(npz['t0'])
n = len(W); det = ~np.isnan(W[:, 0, 0])
# runs of detection
runs = []; s = None
for i in range(n + 1):
    d = det[i] if i < n else False
    if d and s is None: s = i
    if not d and s is not None: runs.append((s, i)); s = None
print(f'fps {fps:.2f} frames {n} detected {det.sum()}')
LA, RA, LH, RH, LS, RS, LK, RK = 27, 28, 23, 24, 11, 12, 25, 26
def sm(x, k=5):
    k = max(1, k); ker = np.ones(k) / k
    return np.convolve(np.nan_to_num(x), ker, 'same')
for a, b in runs:
    if b - a < int(fps * 0.5): continue
    seg = W[a:b]
    hip = (seg[:, LH, :3] + seg[:, RH, :3]) / 2
    # ankle height relative to hips (world y is down in mediapipe → flip)
    la = -(seg[:, LA, 1] - hip[:, 1]); ra = -(seg[:, RA, 1] - hip[:, 1])
    lk = -(seg[:, LK, 1] - hip[:, 1]); rk = -(seg[:, RK, 1] - hip[:, 1])
    # tuck score: both knees high (close to hip) and ankles close together
    ankgap = np.linalg.norm(seg[:, LA, :3] - seg[:, RA, :3], axis=1)
    kneeup = sm((lk + rk) / 2, 5)
    # shoulder axis yaw (image-plane proxy: x of shoulders difference) to see rotation
    shx = seg[:, LS, 0] - seg[:, RS, 0]
    shz = seg[:, LS, 2] - seg[:, RS, 2]
    yaw = np.unwrap(np.arctan2(shz, shx))
    rate = np.abs(np.gradient(sm(yaw, 3))) * fps / (2 * np.pi)  # rev/s
    print(f'\nrun {a/fps+t0:7.2f}-{b/fps+t0:7.2f}s ({b-a} fr)')
    # print 10 Hz summary
    step = max(1, int(fps / 10))
    for i in range(0, b - a, step):
        j = min(b - a, i + step)
        print(f'  {(a+i)/fps+t0:6.2f}  knee {kneeup[i:j].mean():+.2f}  gap {ankgap[i:j].mean():.2f}  rot {rate[i:j].mean():.1f}r/s  lA {la[i:j].mean():+.2f} rA {ra[i:j].mean():+.2f}')
