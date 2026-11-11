"""Find stroking / crossover stretches and jump candidates in a tracked full program.
usage: python3 -I findskating.py <npz> [min_len_s]
Prints: stride stretches (upright, alternating feet, no flight) with stride period, and flight candidates."""
import sys, numpy as np
npz = np.load(sys.argv[1]); W = npz['world']; fps = float(npz['fps']); minlen = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
n = len(W); det = ~np.isnan(W[:, 0, 0])
P = W[:, :, :3].copy(); P[:, :, 1] *= -1  # y up
def col(j, k): return P[:, j, k]
hipc = (P[:, 23] + P[:, 24]) / 2; shc = (P[:, 11] + P[:, 12]) / 2
torso = shc - hipc; upright = torso[:, 1] / (np.linalg.norm(torso, axis=1) + 1e-6)   # ~1 when standing tall
la = P[:, 27] - hipc; ra = P[:, 28] - hipc                                             # ankles relative to hips
ankdiff = la[:, 1] - ra[:, 1]                                                          # which foot is higher
ankgap = np.linalg.norm(la - ra, axis=1)
kneeL = P[:, 25, 1] - hipc[:, 1]; kneeR = P[:, 26, 1] - hipc[:, 1]
def runs(mask, gap=int(fps*0.3)):
    out = []; s = None; last = -10**9
    for i in range(n+1):
        m = mask[i] if i < n else False
        if m:
            if s is None: s = i
            last = i
        elif s is not None and i - last > gap:
            out.append((s, last+1)); s = None
    return out
ok = det & (upright > 0.9) & (np.maximum(kneeL, kneeR) < -0.15)   # upright, not tucked / not in a sit
# stride: ankle height difference oscillates; measure zero crossings per second in a sliding window
sm = np.convolve(np.nan_to_num(ankdiff), np.ones(5)/5, 'same')
zc = np.zeros(n);
for i in range(1, n):
    if sm[i-1]*sm[i] < 0 and abs(sm[i]-sm[i-1]) > 0.01: zc[i] = 1
win = int(fps*2); zcs = np.convolve(zc, np.ones(win), 'same')
stride = ok & (zcs >= 1.5) & (zcs <= 6)
print('stride stretches (t0 t1 len  strides/s  mean ankle gap):')
for a, b in runs(stride):
    if (b-a)/fps < minlen: continue
    rate = zcs[a:b].mean()/2/2  # zero crossings per 2 s window -> strides per second (2 crossings per stride)
    print(f'  {a/fps:7.1f} {b/fps:7.1f} {(b-a)/fps:5.1f}s  {rate:4.2f}/s  gap {np.nanmean(ankgap[a:b]):.2f}')
# flight candidates: both knees high (tuck) and ankles together
tuck = det & (np.minimum(kneeL, kneeR) > -0.32) & (ankgap < 0.25)
print('tuck/flight candidates (t0 t1 len):')
for a, b in runs(tuck, gap=int(fps*0.1)):
    if 0.25 < (b-a)/fps < 1.2: print(f'  {a/fps:7.2f} {b/fps:7.2f} {(b-a)/fps:4.2f}s')
