/* Skating positions, authored in character space (+X left, +Y up, +Z forward).
   Convention: skating (support) foot is LEFT unless noted; use SkaterRig.mirrorPose for the other side. */
(function(global){
const P=(o)=>Object.assign({hips:[0,0,0],torso:[0,0,0],head:[0,0,0],
  lArm:[.95,-.2,.2],lFore:[.95,-.2,.2],rArm:[-.95,-.2,.2],rFore:[-.95,-.2,.2],
  lThigh:[0,-1,0],lShin:[0,-1,0],lFoot:[0,-.45,1],rThigh:[0,-1,0],rShin:[0,-1,0],rFoot:[0,-.45,1]},o);
const POSE={
  // two-foot neutral glide
  stand:P({torso:[.05,0,0],lArm:[.8,-.55,.3],lFore:[.75,-.6,.35],rArm:[-.8,-.55,.3],rFore:[-.75,-.6,.35]}),
  // one-foot glide on left, right free leg extended behind
  glide:P({torso:[.12,0,0],hips:[.05,0,0],lArm:[.9,-.1,.4],lFore:[.9,-.05,.45],rArm:[-.9,-.1,.4],rFore:[-.9,-.05,.45],
    lThigh:[0,-1,.08],lShin:[0,-1,-.04],lFoot:[0,-.45,1],rThigh:[-.08,-.8,-.6],rShin:[-.08,-.75,-.66],rFoot:[-.05,-.55,-.85]}),
  // forward stroke: push with right, glide on bent left
  strokeL:P({torso:[.3,.12,0],hips:[.1,0,0],lArm:[.55,-.3,.75],lFore:[.5,-.25,.8],rArm:[-.75,-.35,-.5],rFore:[-.7,-.4,-.55],
    lThigh:[0,-.85,.5],lShin:[0,-1,-.15],lFoot:[0,-.45,1],rThigh:[-.35,-.7,-.65],rShin:[-.35,-.65,-.7],rFoot:[-.3,-.5,-.8]}),
  // forward crossover (counter-clockwise circle): right crosses over left
  crossA:P({torso:[.28,.25,-.12],hips:[.08,.15,-.1],lArm:[.3,-.25,.9],lFore:[.25,-.2,.95],rArm:[-.95,-.3,.1],rFore:[-.95,-.3,.1],
    lThigh:[.2,-.85,.45],lShin:[.15,-1,-.1],lFoot:[.15,-.45,1],rThigh:[.45,-.8,.35],rShin:[.45,-.85,.25],rFoot:[.4,-.5,.8]}),
  crossB:P({torso:[.28,.25,-.12],hips:[.08,.15,-.1],lArm:[.3,-.25,.9],lFore:[.25,-.2,.95],rArm:[-.95,-.3,.1],rFore:[-.95,-.3,.1],
    lThigh:[-.35,-.75,-.55],lShin:[-.35,-.7,-.62],lFoot:[-.3,-.5,-.8],rThigh:[.1,-.85,.5],rShin:[.1,-1,-.12],rFoot:[.1,-.45,1]}),
  // backward crossover (CCW): skating backwards, looking over left shoulder
  bcrossA:P({torso:[.1,.6,-.1],head:[0,.5,0],hips:[0,.2,-.08],lArm:[.5,-.3,-.8],lFore:[.45,-.3,-.85],rArm:[-.6,-.3,.75],rFore:[-.6,-.3,.8],
    lThigh:[.25,-.85,-.4],lShin:[.2,-1,.1],lFoot:[.2,-.45,.95],rThigh:[.5,-.8,-.3],rShin:[.5,-.85,-.2],rFoot:[.45,-.5,.75]}),
  bcrossB:P({torso:[.1,.6,-.1],head:[0,.5,0],hips:[0,.2,-.08],lArm:[.5,-.3,-.8],lFore:[.45,-.3,-.85],rArm:[-.6,-.3,.75],rFore:[-.6,-.3,.8],
    lThigh:[-.3,-.7,.6],lShin:[-.3,-.7,.65],lFoot:[-.25,-.4,.9],rThigh:[.1,-.85,-.45],rShin:[.1,-1,.1],rFoot:[.1,-.45,.95]}),
  // jump mechanics
  crouch:P({torso:[.4,0,0],hips:[.15,0,0],lArm:[.55,-.55,-.6],lFore:[.45,-.6,-.65],rArm:[-.55,-.55,-.6],rFore:[-.45,-.6,-.65],
    lThigh:[0,-.7,.7],lShin:[0,-1,-.3],lFoot:[0,-.45,1],rThigh:[0,-.7,.7],rShin:[0,-1,-.3],rFoot:[0,-.45,1]}),
  // toe pick: right toe reaches back and plants, left skating leg bent
  pick:P({torso:[.35,0,0],hips:[.1,0,0],lArm:[.6,-.5,-.55],lFore:[.5,-.5,-.6],rArm:[-.6,-.5,-.55],rFore:[-.5,-.5,-.6],
    lThigh:[0,-.75,.65],lShin:[0,-1,-.25],lFoot:[0,-.45,1],rThigh:[-.15,-.7,-.7],rShin:[-.15,-.95,-.3],rFoot:[-.1,-.95,.3]}),
  launch:P({torso:[-.05,0,0],lArm:[.35,.4,.8],lFore:[.3,.5,.8],rArm:[-.35,.4,.8],rFore:[-.3,.5,.8],
    lThigh:[0,-1,.1],lShin:[0,-1,.05],lFoot:[0,-.9,.45],rThigh:[-.05,-.85,.5],rShin:[-.05,-1,-.2],rFoot:[0,-.9,.45]}),
  tuck:P({torso:[0,0,0],lArm:[.3,-.9,.35],lFore:[-.85,.1,.5],rArm:[-.3,-.9,.35],rFore:[.85,.25,.45],
    lThigh:[.02,-1,.04],lShin:[.02,-1,0],lFoot:[0,-.9,.45],rThigh:[.22,-.95,.12],rShin:[.18,-.98,-.02],rFoot:[.1,-.92,.4]}),
  // landing on right back outside edge, left free leg extended back, arms out ("check")
  land:P({torso:[.22,-.35,0],hips:[.1,-.2,0],head:[0,-.3,0],lArm:[.95,-.1,.15],lFore:[.95,-.05,.15],rArm:[-.95,-.1,.15],rFore:[-.95,-.05,.15],
    rThigh:[0,-.88,.45],rShin:[0,-1,-.15],rFoot:[0,-.45,1],lThigh:[.15,-.55,-.8],lShin:[.12,-.5,-.85],lFoot:[.1,-.45,-.9]}),
  // spins (support foot left)
  camel:P({torso:[1.45,0,0],head:[-.95,0,0],hips:[.25,0,0],lArm:[.9,.05,.45],lFore:[.9,.1,.45],rArm:[-.9,.05,.45],rFore:[-.9,.1,.45],
    lThigh:[0,-1,.1],lShin:[0,-1,.02],lFoot:[0,-.45,1],rThigh:[-.12,.02,-1],rShin:[-.12,.05,-1],rFoot:[-.1,-.15,-1]}),
  sit:P({torso:[.65,0,0],hips:[.35,0,0],head:[-.4,0,0],lArm:[.3,-.25,.9],lFore:[.25,-.1,.95],rArm:[-.3,-.25,.9],rFore:[-.25,-.1,.95],
    lThigh:[.05,-.12,1],lShin:[0,-1,.1],lFoot:[0,-.45,1],rThigh:[-.2,-.15,1],rShin:[-.18,-.05,1],rFoot:[-.15,-.25,1]}),
  layback:P({torso:[-1.35,0,0],head:[-.75,0,0],hips:[-.15,0,0],lArm:[.55,.7,.0],lFore:[-.1,.95,-.1],rArm:[-.55,.7,0],rFore:[.1,.95,-.1],
    lThigh:[0,-1,.08],lShin:[0,-1,0],lFoot:[0,-.45,1],rThigh:[-.45,-.55,-.65],rShin:[-.3,.35,-.85],rFoot:[-.25,.1,-.95]}),
  biellmann:P({torso:[-.6,0,0],head:[-.4,0,0],hips:[-.15,0,0],lArm:[.3,.9,-.35],lFore:[-.15,.95,-.35],rArm:[-.3,.9,-.35],rFore:[.15,.95,-.35],
    lThigh:[0,-1,.08],lShin:[0,-1,0],lFoot:[0,-.45,1],rThigh:[-.12,.35,-.92],rShin:[-.05,1,-.12],rFoot:[0,.95,.3]}),
  upright:P({torso:[0,0,0],lArm:[.2,.95,.05],lFore:[-.1,1,.02],rArm:[-.2,.95,.05],rFore:[.1,1,.02],
    lThigh:[0,-1,.05],lShin:[0,-1,0],lFoot:[0,-.45,1],rThigh:[.12,-.92,.35],rShin:[.3,-.9,-.2],rFoot:[.25,-.8,.4]}),
  twizzle:P({torso:[.05,0,0],lArm:[.45,-.3,.5],lFore:[-.5,.1,.6],rArm:[-.45,-.3,.5],rFore:[.5,.1,.6],
    lThigh:[0,-1,.05],lShin:[0,-1,0],lFoot:[0,-.45,1],rThigh:[.08,-.9,.3],rShin:[.1,-.95,-.25],rFoot:[.05,-.85,.4]}),
  // field moves
  spiral:P({torso:[.7,0,0],head:[-.35,0,0],hips:[.2,0,0],lArm:[.75,.3,.55],lFore:[.75,.35,.55],rArm:[-.75,.3,.55],rFore:[-.75,.35,.55],
    lThigh:[0,-1,.1],lShin:[0,-1,.02],lFoot:[0,-.45,1],rThigh:[-.08,.3,-1],rShin:[-.08,.32,-1],rFoot:[-.05,.15,-1]}),
  eagle:P({torso:[-.25,0,0],head:[-.1,0,0],lArm:[.95,-.05,.05],lFore:[.95,-.05,.05],rArm:[-.95,-.05,.05],rFore:[-.95,-.05,.05],
    lThigh:[.55,-.85,0],lShin:[.55,-.85,0],lFoot:[1,-.3,0],rThigh:[-.55,-.85,0],rShin:[-.55,-.85,0],rFoot:[-1,-.3,0]}),
  bauer:P({torso:[-.95,0,0],head:[-.5,0,0],hips:[-.2,0,0],lArm:[.5,.75,-.3],lFore:[.2,.95,-.3],rArm:[-.5,.75,-.3],rFore:[-.2,.95,-.3],
    lThigh:[.45,-.7,.5],lShin:[.35,-.95,-.2],lFoot:[1,-.3,.15],rThigh:[-.5,-.85,-.25],rShin:[-.5,-.85,-.25],rFoot:[-1,-.3,-.05]}),
  cantilever:P({torso:[-1.45,0,0],head:[-.4,0,0],hips:[-.35,0,0],lArm:[.9,-.1,-.3],lFore:[.9,-.1,-.3],rArm:[-.9,-.1,-.3],rFore:[-.9,-.1,-.3],
    lThigh:[.3,-.3,.9],lShin:[.25,-1,-.3],lFoot:[.9,-.3,.3],rThigh:[-.3,-.3,.9],rShin:[-.25,-1,-.3],rFoot:[-.9,-.3,.3]}),
  hydro:P({torso:[.5,.4,.9],head:[-.2,.3,.2],hips:[.3,.3,.7],lArm:[.9,-.6,.1],lFore:[.9,-.8,.1],rArm:[-.4,-.9,.4],rFore:[-.5,-.9,.3],
    lThigh:[.2,-.2,.95],lShin:[.2,-1,-.2],lFoot:[.3,-.4,.85],rThigh:[-.6,-.5,.6],rShin:[-.6,-.6,.55],rFoot:[-.5,-.4,.75]}),
  // step sequence body positions with port de bras
  stepA:P({torso:[.15,.45,-.08],head:[0,.3,0],hips:[.05,.2,0],lArm:[.4,.5,.75],lFore:[.2,.7,.7],rArm:[-.9,-.3,-.3],rFore:[-.9,-.3,-.3],
    lThigh:[0,-.9,.4],lShin:[0,-1,-.12],lFoot:[0,-.45,1],rThigh:[-.25,-.85,-.45],rShin:[-.25,-.95,-.2],rFoot:[-.2,-.6,-.75]}),
  stepB:P({torso:[.12,-.45,.08],head:[0,-.3,0],hips:[.05,-.2,0],lArm:[.9,-.3,-.3],lFore:[.9,-.3,-.3],rArm:[-.4,.5,.75],rFore:[-.2,.7,.7],
    rThigh:[0,-.9,.4],rShin:[0,-1,-.12],rFoot:[0,-.45,1],lThigh:[.25,-.85,-.45],lShin:[.25,-.95,-.2],lFoot:[.2,-.6,-.75]}),
  // flying entry (air position of a flying camel)
  fly:P({torso:[.9,0,0],head:[-.5,0,0],lArm:[.9,.3,.3],lFore:[.9,.35,.3],rArm:[-.9,.3,.3],rFore:[-.9,.35,.3],
    lThigh:[.05,-.55,.85],lShin:[.05,-1,-.3],lFoot:[0,-.8,.6],rThigh:[-.12,.15,-1],rShin:[-.12,.15,-1],rFoot:[-.1,-.05,-1]}),
  // mohawk/turn transition: feet in a V, arms framing
  mohawk:P({torso:[.1,.5,0],head:[0,.4,0],hips:[0,.25,0],lArm:[.7,-.2,.65],lFore:[.65,-.1,.7],rArm:[-.8,-.25,-.5],rFore:[-.8,-.25,-.5],
    lThigh:[.15,-.95,.2],lShin:[.15,-1,-.05],lFoot:[.3,-.45,.9],rThigh:[-.2,-.95,-.1],rShin:[-.2,-1,-.1],rFoot:[-.9,-.45,-.25]}),
  // lunge (choreo)
  lunge:P({torso:[.35,0,0],head:[-.2,0,0],hips:[.2,0,0],lArm:[.6,.5,.6],lFore:[.5,.6,.6],rArm:[-.9,-.2,-.3],rFore:[-.9,-.2,-.3],
    lThigh:[0,-.55,.85],lShin:[0,-1,-.4],lFoot:[0,-.45,1],rThigh:[-.1,-.55,-.85],rShin:[-.1,-.5,-.87],rFoot:[-.05,-.45,-.9]}),
  // pairs: man pivot for death spiral (deep crouch, toe pick planted)
  pivot:P({torso:[.45,.6,0],head:[0,.6,0],hips:[.2,.3,0],lArm:[.95,-.3,.2],lFore:[.95,-.3,.2],rArm:[-.6,-.6,.6],rFore:[-.6,-.7,.5],
    lThigh:[.05,-.25,.98],lShin:[0,-1,.05],lFoot:[0,-.45,1],rThigh:[-.25,-.85,-.45],rShin:[-.25,-.95,-.3],rFoot:[-.2,-.95,.2]}),
  // pairs: lady laid out for death spiral (body near horizontal is applied by root roll)
  layout:P({torso:[-.35,0,0],head:[-.3,0,0],lArm:[.95,.1,.1],lFore:[.95,.1,.1],rArm:[-.2,-.95,.2],rFore:[-.2,-.95,.2],
    lThigh:[0,-1,.1],lShin:[0,-1,.05],lFoot:[0,-.45,1],rThigh:[-.15,-.95,-.3],rShin:[-.15,-.95,-.3],rFoot:[-.1,-.5,-.85]}),
  // pairs: man lifting overhead
  liftMan:P({torso:[-.05,0,0],head:[-.4,0,0],lArm:[.25,.95,.05],lFore:[.1,1,0],rArm:[-.25,.95,.05],rFore:[-.1,1,0],
    lThigh:[.08,-1,.1],lShin:[.08,-1,0],lFoot:[.1,-.45,1],rThigh:[-.08,-1,.1],rShin:[-.08,-1,0],rFoot:[-.1,-.45,1]}),
  // pairs: lady in lift (star / split position, horizontal applied by root)
  star:P({torso:[-.2,0,0],head:[-.2,0,0],lArm:[.95,.2,.05],lFore:[.95,.2,.05],rArm:[-.95,.2,.05],rFore:[-.95,.2,.05],
    lThigh:[.6,-.75,.1],lShin:[.6,-.75,.1],lFoot:[.6,-.75,.3],rThigh:[-.6,-.75,.1],rShin:[-.6,-.75,.1],rFoot:[-.6,-.75,.3]}),
  // pairs: catch/launch for twist
  catchArms:P({torso:[.1,0,0],head:[-.3,0,0],lArm:[.35,.85,.35],lFore:[.2,.9,.4],rArm:[-.35,.85,.35],rFore:[-.2,.9,.4],
    lThigh:[.1,-.85,.45],lShin:[.1,-1,-.2],lFoot:[.1,-.45,1],rThigh:[-.1,-.85,.45],rShin:[-.1,-1,-.2],rFoot:[-.1,-.45,1]}),
  // presentation
  openArms:P({torso:[-.08,0,0],head:[-.3,0,0],lArm:[.85,.45,.3],lFore:[.85,.5,.3],rArm:[-.85,.45,.3],rFore:[-.85,.5,.3],
    lThigh:[.08,-1,0],lShin:[.08,-1,0],lFoot:[.1,-.45,1],rThigh:[-.08,-1,0],rShin:[-.08,-1,0],rFoot:[-.1,-.45,1]}),
  bow:P({torso:[.9,0,0],head:[-.2,0,0],lArm:[.5,-.5,.6],lFore:[.1,-.3,.9],rArm:[-.7,-.6,-.2],rFore:[-.7,-.65,-.2],
    lThigh:[.05,-1,0],lShin:[.05,-1,0],rThigh:[-.25,-.8,-.5],rShin:[-.25,-.8,-.5],rFoot:[-.2,-.6,-.75]}),
  finish:P({torso:[-.15,0,0],head:[-.4,0,0],lArm:[.6,.75,.2],lFore:[.3,.95,.1],rArm:[-.6,.75,.2],rFore:[-.3,.95,.1],
    lThigh:[.1,-1,.05],lShin:[.1,-1,0],lFoot:[.1,-.45,1],rThigh:[-.2,-.85,-.45],rShin:[-.2,-.85,-.45],rFoot:[-.15,-.6,-.75]}),
};
global.SKATER_POSES=POSE;
})(window);
