"""Spin position from tracked video -> looping clip in the jump-clip frame format.
usage: python3 -I spin2clip.py <npz> <name> <out.json> <t0> <t1> [slow] [mirror]
The skater stays in place; yaw is synthesized (2 rev/s real) so single-view ambiguity never matters:
limb directions are expressed in the hip frame, which is view-independent."""
import sys, json, math, numpy as np
sys.path.insert(0, '../mocap')
from convert import unit, smooth
npz, name, out, t0s, t1s = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5])
slow = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
mirror = len(sys.argv) > 7 and sys.argv[7] == 'mirror'
d = np.load(npz); W = d['world']; fps = float(d['fps']); tb = float(d['t0'])
a, b = int((t0s-tb)*fps), int((t1s-tb)*fps); W = W[a:b]
T = len(W); idx = np.arange(T)
for j in range(33):
    for k in range(3):
        col = W[:,j,k]; m = ~np.isnan(col)
        if m.sum() >= 2: W[:,j,k] = np.interp(idx, idx[m], col[m])
P = W[:,:,:3].copy(); P[:,:,1] *= -1; P[:,:,2] *= -1
P = smooth(P, 9)
L = lambda i: P[:, i, :]; mid = lambda i, j: (P[:, i, :] + P[:, j, :]) / 2
up = np.array([0,1,0.])
left = L(23)-L(24); left[:,1]=0; left = unit(left); fwd = unit(np.cross(left, np.tile(up,(T,1))))
def local(v): return np.stack([np.sum(v*left,1), v[:,1], np.sum(v*fwd,1)],1)
chest = local(unit(mid(11,12)-mid(23,24))); torsoP = np.arctan2(chest[:,2],chest[:,1]); torsoR = -np.arctan2(chest[:,0],chest[:,1])
shl = L(11)-L(12); shl[:,1]=0; shl=unit(shl); shl_l = local(shl); torsoY = np.arctan2(-shl_l[:,2], shl_l[:,0])
head = local(unit(mid(7,8)+up*0.12 - mid(11,12))); headP = np.arctan2(head[:,2],head[:,1]) - torsoP; headR = -np.arctan2(head[:,0],head[:,1]) - torsoR
dirs = {'lArm':local(unit(L(13)-L(11))),'lFore':local(unit(L(15)-L(13))),'rArm':local(unit(L(14)-L(12))),'rFore':local(unit(L(16)-L(14))),
        'lThigh':local(unit(L(25)-L(23))),'lShin':local(unit(L(27)-L(25))),'lFoot':local(unit(L(31)-L(27))),
        'rThigh':local(unit(L(26)-L(24))),'rShin':local(unit(L(28)-L(26))),'rFoot':local(unit(L(32)-L(28)))}
KEYS = ['lArm','lFore','rArm','rFore','lThigh','lShin','lFoot','rThigh','rShin','rFoot']
if mirror:
    sw = {'lArm':'rArm','rArm':'lArm','lFore':'rFore','rFore':'lFore','lThigh':'rThigh','rThigh':'lThigh','lShin':'rShin','rShin':'lShin','lFoot':'rFoot','rFoot':'lFoot'}
    dirs = {k: dirs[sw[k]]*np.array([-1,1,1]) for k in KEYS}; torsoY = -torsoY; torsoR = -torsoR; headR = -headR
fps_eff = fps*slow
rate = 2.0  # rev/s synthesized
frames=[]
for t in range(T):
    tr = t/fps_eff
    row=[0.0, 0.0, round(2*math.pi*rate*tr,4), 0.0, float(torsoP[t]), float(torsoY[t]), float(torsoR[t]), float(headP[t]), float(headR[t])]
    for k in KEYS:
        v=dirs[k][t]; row += [float(v[0]), float(v[1]), float(v[2])]
    frames.append([round(x,4) for x in row])
# downsample to ~30 fps
step = max(1, int(round(fps_eff/30)))
frames = frames[::step]; fps_out = fps_eff/step
clip={'kind':'spin','fps':fps_out,'n':len(frames),'rate':rate,'src':'video','frames':frames}
json.dump({name: clip}, open(out,'w'))
print('spin clip', name, 'frames', len(frames), 'fps', round(fps_out,1), 'dur', round(len(frames)/fps_out,2))
