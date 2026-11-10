"""Convert FS-Jump3D C3D recordings into pose clips for the Gold Studio skater rig.
Output: clips.json  { "<Type>": { "<revs>": clip } }, clip = {fps, pre, post, takeoff, landing, revs, frames:[...]}
Each frame: [along, lateral, yawRel, air, torsoP, torsoY, torsoR, headP, headR, then 10 direction vectors x3]
Character space: +X left, +Y up, +Z forward.   Source: Z-up millimetres at 60 Hz.
"""
import sys, os, json, math, warnings
import numpy as np
warnings.filterwarnings('ignore')
import c3d
# some files carry a malformed TRIAL:ACTUAL_START_FIELD; use the header frame range instead
c3d.Reader.first_frame = property(lambda self: int(self.header.first_frame))
c3d.Reader.last_frame = property(lambda self: int(self.header.last_frame))

ROOT = sys.argv[1] if len(sys.argv) > 1 else 'c3d/c3d'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'clips.json'
NEED = ['PELVIS','L_Hip Joint','R_Hip Joint','LKNE','RKNE','LANK','RANK','LHEL','RHEL','L_Toe','R_Toe',
        'L_Shoulder Joint','R_Shoulder Joint','LELB','RELB','LWRT','RWRT','CLAV','C7','Vertex','Nasion','Xiphoid','LMT5','RMT5']
DIRKEYS = ['lArm','lFore','rArm','rFore','lThigh','lShin','lFoot','rThigh','rShin','rFoot']

def load(path):
    r = c3d.Reader(open(path,'rb'))
    labels = [l.strip() for l in r.point_labels]
    idx = {l:i for i,l in enumerate(labels)}
    missing = [n for n in NEED if n not in idx]
    if missing: raise ValueError('missing '+','.join(missing))
    frames = [f[1][:, :3] for f in r.read_frames()]
    P = np.array(frames, dtype=np.float64) / 1000.0           # (T, M, 3) metres, Z-up
    # --- level the capture: fit the ice plane through the lowest foot contact of each frame ---
    footnames = ['LHEL','RHEL','L_Toe','R_Toe','LMT5','RMT5']
    F = np.stack([P[:, idx[n], :] for n in footnames], axis=1)      # (T,6,3)
    lo = F[np.arange(len(F)), F[:,:,2].argmin(axis=1)]              # lowest foot point per frame (T,3)
    pts = lo.copy()
    for _ in range(6):   # iterative plane fit keeping the lowest points
        A = np.c_[pts[:,0], pts[:,1], np.ones(len(pts))]
        coef, *_ = np.linalg.lstsq(A, pts[:,2], rcond=None)
        res = lo[:,2] - (coef[0]*lo[:,0] + coef[1]*lo[:,1] + coef[2])
        keep = res < np.percentile(res, 45)
        pts = lo[keep]
    a_, b_, c_ = coef
    n = np.array([-a_, -b_, 1.0]); n /= np.linalg.norm(n)
    # rotation taking plane normal n to +Z
    z = np.array([0,0,1.0]); v = np.cross(n, z); sng = np.linalg.norm(v); cs = float(np.dot(n, z))
    if sng > 1e-9:
        vx = np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
        Rm = np.eye(3) + vx + vx@vx*((1-cs)/(sng**2))
    else: Rm = np.eye(3)
    P = P - np.array([0,0,c_])
    P = P @ Rm.T
    # Z-up -> Y-up (right-handed): (x, y, z) -> (x, z, -y)
    P = np.stack([P[:,:,0], P[:,:,2], -P[:,:,1]], axis=2)
    J = {n: P[:, idx[n], :] for n in NEED}
    return J, float(r.point_rate)

def unit(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True); n[n<1e-9] = 1; return v / n

def smooth(x, k=3):
    if k <= 1: return x
    ker = np.ones(k)/k; pad = k//2
    xp = np.pad(x, ((pad,pad),)+((0,0),)*(x.ndim-1), mode='edge')
    return np.apply_along_axis(lambda a: np.convolve(a, ker, mode='valid'), 0, xp)

def convert(path, jtype):
    J, fps = load(path)
    T = len(J['PELVIS'])
    for k in J: J[k] = smooth(J[k], 3)
    up = np.array([0,1,0.])
    # character frame per frame from the hip axis
    left = J['L_Hip Joint'] - J['R_Hip Joint']; left[:,1] = 0; left = unit(left)
    fwd = unit(np.cross(left, np.tile(up,(T,1))))
    yaw = np.arctan2(fwd[:,0], fwd[:,2])
    def local(v):  # world vector -> character-local components [x(left), y(up), z(forward)]
        return np.stack([np.sum(v*left,1), v[:,1], np.sum(v*fwd,1)], axis=1)
    # feet height & flight detection
    feet = np.stack([J['LHEL'][:,1], J['RHEL'][:,1], J['L_Toe'][:,1], J['R_Toe'][:,1], J['LMT5'][:,1], J['RMT5'][:,1]], axis=1)
    lowest = feet.min(axis=1)
    # flight detection from physics: the pelvis (~centre of mass) is in free fall only while airborne.
    pz = smooth(J['PELVIS'][:,1:2], 5)[:,0]
    dt = 1.0/fps
    vz = np.gradient(pz, dt); az = np.gradient(vz, dt)
    az = smooth(az[:,None], 7)[:,0]
    ff = (az < -5.5) & (az > -14.0)
    best=(0,0); i=0
    while i < T:
        if ff[i]:
            j=i
            while j < T and ff[j]: j+=1
            if j-i > best[1]-best[0]: best=(i,j)
            i=j
        else: i+=1
    t_off, t_land = best
    if t_land - t_off < int(0.25*fps): raise ValueError('no flight found')
    # refine with the feet: ice level = lowest foot just before takeoff and after landing
    ice = min(np.percentile(lowest[max(0,t_off-int(0.3*fps)):t_off+1], 20), np.percentile(lowest[t_land-1:min(T,t_land+int(0.3*fps))], 20))
    h = lowest - ice
    # widen the free-fall window by at most 3 frames on each side while the feet are clearly off the ice
    k=0
    while t_off > 0 and h[t_off-1] > 0.03 and k < 3: t_off -= 1; k+=1
    k=0
    while t_land < T and h[t_land] > 0.03 and k < 3: t_land += 1; k+=1
    pre = int(round(0.9*fps)); post = int(round(1.0*fps))
    s = max(0, t_off - pre); e = min(T, t_land + post)
    # revolutions in flight from unwrapped shoulder-axis yaw
    shl = J['L_Shoulder Joint'] - J['R_Shoulder Joint']; shl[:,1]=0; shl = unit(shl)
    shyaw = np.unwrap(np.arctan2(shl[:,0], shl[:,2]))
    turn = (shyaw[t_land-1] - shyaw[t_off]) / (2*math.pi)
    revs = abs(turn)
    sign = 1 if turn > 0 else -1
    # approach direction = pelvis velocity over the 0.4 s before takeoff
    pel = J['PELVIS']
    a0 = max(0, t_off - int(0.4*fps))
    appr = pel[t_off] - pel[a0]; appr[1]=0
    if np.linalg.norm(appr) < 1e-3: appr = fwd[t_off]
    appr = appr/np.linalg.norm(appr)
    aperp = np.cross(up, appr)   # left of travel
    ayaw = math.atan2(appr[0], appr[2])
    # body yaw unwrapped, relative to approach; mirror clockwise jumpers so every clip rotates counter-clockwise
    body_yaw = np.unwrap(yaw)
    yaw_rel = body_yaw - ayaw
    # torso orientation
    chest = local(unit(J['CLAV'] - J['PELVIS']))
    torsoP = np.arctan2(chest[:,2], chest[:,1])
    torsoR = -np.arctan2(chest[:,0], chest[:,1])
    shl_l = local(shl)
    torsoY = np.arctan2(-shl_l[:,2], shl_l[:,0])
    head = local(unit(J['Vertex'] - J['C7']))
    headP = np.arctan2(head[:,2], head[:,1]) - torsoP
    headR = -np.arctan2(head[:,0], head[:,1]) - torsoR
    dirs = {
        'lArm': local(unit(J['LELB']-J['L_Shoulder Joint'])), 'lFore': local(unit(J['LWRT']-J['LELB'])),
        'rArm': local(unit(J['RELB']-J['R_Shoulder Joint'])), 'rFore': local(unit(J['RWRT']-J['RELB'])),
        'lThigh': local(unit(J['LKNE']-J['L_Hip Joint'])), 'lShin': local(unit(J['LANK']-J['LKNE'])), 'lFoot': local(unit(J['L_Toe']-J['LANK'])),
        'rThigh': local(unit(J['RKNE']-J['R_Hip Joint'])), 'rShin': local(unit(J['RANK']-J['RKNE'])), 'rFoot': local(unit(J['R_Toe']-J['RANK'])),
    }
    mirror = sign < 0
    frames = []
    for t in range(s, e):
        d = pel[t] - pel[t_off]; d[1]=0
        along = float(np.dot(d, appr)); lateral = float(np.dot(d, aperp))
        yr = float(yaw_rel[t] - yaw_rel[t_off] + (yaw_rel[t_off]))  # keep absolute relation to approach
        tp, ty, tr, hp, hr = float(torsoP[t]), float(torsoY[t]), float(torsoR[t]), float(headP[t]), float(headR[t])
        row = [along, lateral, yr, float(max(0.0, h[t]))]
        if mirror:
            lateral = -lateral; yr = -yr; ty=-ty; tr=-tr; hr=-hr
            row = [along, lateral, yr, float(max(0.0, h[t]))]
        row += [tp, ty, tr, hp, hr]
        for k in DIRKEYS:
            kk = k
            if mirror: kk = {'lArm':'rArm','rArm':'lArm','lFore':'rFore','rFore':'lFore','lThigh':'rThigh','rThigh':'lThigh','lShin':'rShin','rShin':'lShin','lFoot':'rFoot','rFoot':'lFoot'}[k]
            v = dirs[kk][t]
            if mirror: v = np.array([-v[0], v[1], v[2]])
            row += [round(float(v[0]),4), round(float(v[1]),4), round(float(v[2]),4)]
        frames.append([round(x,4) for x in row])
    clip = {'fps': fps, 'n': len(frames), 'takeoff': (t_off - s)/fps, 'landing': (t_land - s)/fps, 'air': (t_land - t_off)/fps,
            'revs': round(revs,2), 'mirrored': mirror, 'src': os.path.relpath(path, ROOT), 'frames': frames}
    return clip

TYPE_CODE = {'Axel':'A','Lutz':'Lz','Flip':'F','Loop':'Lo','Salchow':'S','Toeloop':'T'}
lib = {}
report = []
for skater in sorted(os.listdir(ROOT)):
    sdir = os.path.join(ROOT, skater)
    if not os.path.isdir(sdir): continue
    for jt in sorted(os.listdir(sdir)):
        if jt not in TYPE_CODE: continue
        for f in sorted(os.listdir(os.path.join(sdir, jt))):
            if not f.endswith('.c3d'): continue
            p = os.path.join(sdir, jt, f)
            try:
                c = convert(p, jt)
            except Exception as ex:
                report.append((p, 'ERR', str(ex))); continue
            code = TYPE_CODE[jt]
            # declared rotations: skaters pre-rotate on the ice, so a triple shows ~2.4-2.9 turns in the air
            rv = c['revs'] - (0.5 if code=='A' else 0)
            revs_n = 1 if rv < 1.3 else 2 if rv < 2.35 else 3 if rv < 3.35 else 4
            report.append((p, code, revs_n, c['revs'], c['air'], c['n']))
            key = (code, revs_n)
            if not (0.3 <= c['air'] <= 0.85): continue          # implausible flight = bad detection
            c['_err'] = 0
            cur = lib.get(code, {}).get(str(revs_n))
            # keep the clip with the longest flight per (type, declared revs)
            if cur is None or c['air'] > cur['air']:
                lib.setdefault(code, {})[str(revs_n)] = c
for r in report: print(r)
# downsample frames to 30 fps to keep the file small
for code in lib:
    for k in lib[code]:
        c = lib[code][k]
        if c['fps'] >= 59:
            c['frames'] = c['frames'][::2]; c['fps'] = c['fps']/2; c['n'] = len(c['frames'])
for code in lib:
    for k in lib[code]: lib[code][k].pop('_err',None)
json.dump(lib, open(OUT,'w'), separators=(',',':'))
print('wrote', OUT, {c:{k:(v['revs'],round(v['air'],2),v['src']) for k,v in lib[c].items()} for c in lib})
