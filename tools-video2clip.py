"""Slow-motion replay -> clip. Flight found from leg configuration; time compressed so the flight matches a real jump."""
import sys, json, math, numpy as np
sys.path.insert(0, '../mocap')
from convert import unit, smooth
npz, code, revs_declared, out, t0s, t1s = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], float(sys.argv[5]), float(sys.argv[6])
d = np.load(npz); W = d['world']; fps = float(d['fps']); tb = float(d['t0'])
a, b = int((t0s-tb)*fps), int((t1s-tb)*fps); W = W[a:b]
T = len(W); idx = np.arange(T)
for j in range(33):
    for k in range(3):
        col = W[:,j,k]; m = ~np.isnan(col)
        if m.sum() >= 2: W[:,j,k] = np.interp(idx, idx[m], col[m])
P = W[:,:,:3].copy(); P[:,:,1] *= -1; P[:,:,2] *= -1
P = smooth(P, 7)
L = lambda i: P[:, i, :]; mid = lambda i, j: (P[:, i, :] + P[:, j, :]) / 2
up = np.array([0,1,0.])
def ang(a,b,c):  # angle at b
    v1=a-b; v2=c-b; return np.degrees(np.arccos(np.clip(np.sum(v1*v2,1)/(np.linalg.norm(v1,axis=1)*np.linalg.norm(v2,axis=1)+1e-9),-1,1)))
kneeL = ang(L(23),L(25),L(27)); kneeR = ang(L(24),L(26),L(28)); ankd = np.linalg.norm(L(27)-L(28),axis=1)
tuck = (kneeL>150)&(kneeR>150)&(ankd<0.25)
# longest tuck run
best=(0,0); i=0
while i<T:
    if tuck[i]:
        j=i
        while j<T and tuck[j]: j+=1
        if j-i>best[1]-best[0]: best=(i,j)
        i=j
    else: i+=1
t_off, t_land = best
if len(sys.argv) > 8: t_off, t_land = int((float(sys.argv[7])-t0s)*fps), int((float(sys.argv[8])-t0s)*fps)   # manual takeoff/landing (absolute s)
air_real = {1:.42,2:.52,3:.62,4:.72}[min(4,revs_declared)] + (0.06 if code=='A' else 0)
slow = (t_land - t_off)/fps/air_real            # slow-motion factor
print('tuck window', round(t_off/fps,2), round(t_land/fps,2), 'slow-mo x', round(slow,2))
if slow < 1.2: slow = 1.0
fps_eff = fps*slow   # slow-motion frames each cover less real time
# character frame from hips
left = L(23)-L(24); left[:,1]=0; left = unit(left); fwd = unit(np.cross(left, np.tile(up,(T,1))))
def local(v): return np.stack([np.sum(v*left,1), v[:,1], np.sum(v*fwd,1)],1)
chest = local(unit(mid(11,12)-mid(23,24))); torsoP = np.arctan2(chest[:,2],chest[:,1]); torsoR = -np.arctan2(chest[:,0],chest[:,1])
shl = L(11)-L(12); shl[:,1]=0; shl=unit(shl); shl_l = local(shl); torsoY = np.arctan2(-shl_l[:,2], shl_l[:,0])
head = local(unit(mid(7,8)+up*0.12 - mid(11,12))); headP = np.arctan2(head[:,2],head[:,1]) - torsoP; headR = -np.arctan2(head[:,0],head[:,1]) - torsoR
dirs = {'lArm':local(unit(L(13)-L(11))),'lFore':local(unit(L(15)-L(13))),'rArm':local(unit(L(14)-L(12))),'rFore':local(unit(L(16)-L(14))),
        'lThigh':local(unit(L(25)-L(23))),'lShin':local(unit(L(27)-L(25))),'lFoot':local(unit(L(31)-L(27))),
        'rThigh':local(unit(L(26)-L(24))),'rShin':local(unit(L(28)-L(26))),'rFoot':local(unit(L(32)-L(28)))}
# heading: takeoff facing. Axel takes off forward (yawRel 0 at takeoff); toe/edge jumps take off backwards (pi)
yaw0 = 0.0 if code=='A' else math.pi
air_revs = revs_declared + (0.5 if code=='A' else -0.4)
hmax = 9.81*air_real*air_real/8
pre_real, post_real = 0.9, 1.0
s = max(0, t_off - int(pre_real*fps_eff)); e = min(T, t_land + int(post_real*fps_eff))
frames=[]
for t in range(s, e):
    tr = (t - t_off)/fps_eff          # real seconds relative to takeoff
    along = 4.6*tr
    if t < t_off: yr = yaw0; air = 0.0
    elif t < t_land: u=(t-t_off)/(t_land-t_off); yr = yaw0 + 2*math.pi*air_revs*u; air = 4*hmax*u*(1-u)
    else: yr = yaw0 + 2*math.pi*air_revs; air = 0.0
    row=[round(along,4), 0.0, round(yr,4), round(float(air),4), float(torsoP[t]), float(torsoY[t]), float(torsoR[t]), float(headP[t]), float(headR[t])]
    for k in ['lArm','lFore','rArm','rFore','lThigh','lShin','lFoot','rThigh','rShin','rFoot']:
        v=dirs[k][t]; row += [round(float(v[0]),4), round(float(v[1]),4), round(float(v[2]),4)]
    frames.append([round(x,4) for x in row])
clip={'fps':fps_eff,'n':len(frames),'takeoff':(t_off-s)/fps_eff,'landing':(t_land-s)/fps_eff,'air':(t_land-t_off)/fps_eff,'revs':air_revs,'mirrored':False,'src':'video-slowmo','frames':frames}
# downsample to ~30 fps
step=max(1,int(round(fps_eff/30)))
if step>1: clip['frames']=clip['frames'][::step]; clip['fps']=fps_eff/step; clip['n']=len(clip['frames'])
json.dump({code:{str(revs_declared):clip}}, open(out,'w'), separators=(',',':'))
print('clip: air', round(clip['air'],2), 'frames', clip['n'], 'fps', round(clip['fps'],1))
