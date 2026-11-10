/* Skater rig: aim-based posing on a Mixamo skeleton.
   Character space: +Y up, +Z forward (facing), +X = skater's LEFT.
   A pose = { hips:[pitch,yaw,roll], torso:[p,y,r], head:[p,y,r],
              lArm,lFore,rArm,rFore,lThigh,lShin,lFoot,rThigh,rShin,rFoot : [x,y,z] directions,
              lArmTw,rArmTw : twist radians (optional), lift: extra height (m) }               */
(function(global){
const V3=THREE.Vector3,QT=THREE.Quaternion,EU=THREE.Euler;
const Y=new V3(0,1,0);
const AIM=[['LeftArm','lArm','LeftForeArm'],['LeftForeArm','lFore','LeftHand'],['RightArm','rArm','RightForeArm'],['RightForeArm','rFore','RightHand'],
           ['LeftUpLeg','lThigh','LeftLeg'],['LeftLeg','lShin','LeftFoot'],['LeftFoot','lFoot','LeftToeBase'],['RightUpLeg','rThigh','RightLeg'],['RightLeg','rShin','RightFoot'],['RightFoot','rFoot','RightToeBase']];
const EUL=[['Hips','hips',1],['Spine','torso',.34],['Spine1','torso',.33],['Spine2','torso',.33],['Neck','head',.4],['Head','head',.6]];
const DIRKEYS=['lArm','lFore','rArm','rFore','lThigh','lShin','lFoot','rThigh','rShin','rFoot'];
const EULKEYS=['hips','torso','head'];
const FEET=['LeftFoot','LeftToeBase','LeftToe_End','RightFoot','RightToeBase','RightToe_End'];
const _q=new QT(),_q2=new QT(),_e=new EU(),_v=new V3(),_v2=new V3(),_p=new V3();

function makeRig(model,opts){
  opts=opts||{};
  const b={};model.traverse(o=>{if(o.isBone)b[o.name.replace('mixamorig','')]=o});
  const rest={};for(const k in b)rest[k]=b[k].quaternion.clone();
  // rest direction of each aim bone = direction to its child, in the bone's parent space
  const restDir={};for(const [bone,key,child] of AIM){restDir[bone]=b[child].position.clone().normalize().applyQuaternion(rest[bone])}
  const rig={model,b,rest,restDir,bladeOffset:opts.bladeOffset||0.0};
  return rig;
}
function nrm(d){return _v.set(d[0],d[1],d[2]).normalize()}
function applyPose(rig,p,air){
  const {b,rest,model}=rig;
  for(const [bone,key,f] of EUL){const e=p[key]||[0,0,0];_e.set(e[0]*f,e[1]*f,e[2]*f,'YXZ');b[bone].quaternion.copy(rest[bone]).multiply(_q.setFromEuler(_e))}
  model.position.y=0;
  model.updateMatrixWorld(true);
  const qRoot=model.getWorldQuaternion(new QT());
  for(const [bone,key,child] of AIM){const d=p[key];if(!d)continue;const B=b[bone];
    const dw=nrm(d).applyQuaternion(qRoot);
    const qp=B.parent.getWorldQuaternion(_q2).invert();
    const dl=dw.applyQuaternion(qp);
    _q.setFromUnitVectors(rig.restDir[bone],dl);
    B.quaternion.copy(rest[bone]).premultiply(_q);
    const tw=p[key+'Tw'];if(tw){_v2.copy(b[child].position).normalize();B.quaternion.multiply(_q.setFromAxisAngle(_v2,tw))}
    B.updateMatrixWorld(true);
  }
  // ground contact: lowest foot point sits on the ice (plus air)
  let minY=Infinity;for(const n of FEET){const B=b[n];if(!B)continue;B.getWorldPosition(_p);if(model.parent)model.parent.worldToLocal(_p);if(_p.y<minY)minY=_p.y}
  const lift=(p.lift||0)+(air||0);
  model.position.y=-minY+rig.bladeOffset+lift;
  model.updateMatrixWorld(true);
}
function mixPose(a,b,t){
  const o={};
  for(const k of EULKEYS){const A=a[k]||[0,0,0],B=b[k]||[0,0,0];o[k]=[A[0]+(B[0]-A[0])*t,A[1]+(B[1]-A[1])*t,A[2]+(B[2]-A[2])*t]}
  for(const k of DIRKEYS){const A=a[k],B=b[k];if(!A&&!B)continue;if(!A){o[k]=B;continue}if(!B){o[k]=A;continue}
    // slerp-ish: normalized lerp with fallback for opposite vectors
    let x=A[0]+(B[0]-A[0])*t,y=A[1]+(B[1]-A[1])*t,z=A[2]+(B[2]-A[2])*t;const L=Math.hypot(x,y,z);
    if(L<1e-3){x=A[0]+.01;y=A[1];z=A[2]+.01}o[k]=[x,y,z];
    const tk=k+'Tw';if(a[tk]||b[tk])o[tk]=(a[tk]||0)+((b[tk]||0)-(a[tk]||0))*t}
  o.lift=(a.lift||0)+((b.lift||0)-(a.lift||0))*t;
  return o;
}
function mirrorPose(a){
  const o={};
  for(const k of EULKEYS){const A=a[k]||[0,0,0];o[k]=[A[0],-A[1],-A[2]]}
  const sw={lArm:'rArm',rArm:'lArm',lFore:'rFore',rFore:'lFore',lThigh:'rThigh',rThigh:'lThigh',lShin:'rShin',rShin:'lShin',lFoot:'rFoot',rFoot:'lFoot'};
  for(const k of DIRKEYS){const A=a[sw[k]];if(A)o[k]=[-A[0],A[1],A[2]];const tk=sw[k]+'Tw';if(a[tk])o[k+'Tw']=-a[tk]}
  o.lift=a.lift||0;return o;
}
global.SkaterRig={makeRig,applyPose,mixPose,mirrorPose};
})(window);
