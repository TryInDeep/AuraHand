import cv2
import mediapipe as mp
import numpy as np
import math
import random

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

t = 0

def hue2bgr(hue, sat=255, val=255):
    c = cv2.cvtColor(np.uint8([[[int(hue)%180, sat, val]]]), cv2.COLOR_HSV2BGR)
    return tuple(int(x) for x in c[0][0])

# Variable bar lengths for rose chart
BAR_LENGTHS = [0.60,0.80,0.95,0.72,1.0,0.65,0.88,0.75,
               0.92,0.55,0.83,0.70,0.96,0.62,0.78,0.88,
               0.68,0.93,0.58,0.85,0.76,0.99,0.64,0.80]
NUM_BARS = len(BAR_LENGTHS)

def draw_rose_wheel(frame, cx, cy, radius, ao):
    inner = int(radius * 0.18)
    for i in range(NUM_BARS):
        sa    = math.radians(i*(360/NUM_BARS) + ao)
        ea    = math.radians((i+1)*(360/NUM_BARS) + ao)
        bar_r = int(radius * BAR_LENGTHS[i])
        hue   = int(i*(180/NUM_BARS))
        color = hue2bgr(hue, sat=255, val=255)
        # Solid fill
        pts = []
        for r in range(inner, bar_r, 3):
            pts.append((cx+int(r*math.cos(sa)), cy+int(r*math.sin(sa))))
        for r in range(bar_r, inner, -3):
            pts.append((cx+int(r*math.cos(ea)), cy+int(r*math.sin(ea))))
        if len(pts) > 2:
            cv2.fillPoly(frame, [np.array(pts)], color)
        # Bright edge
        tip_x = cx+int(bar_r*math.cos((sa+ea)/2))
        tip_y = cy+int(bar_r*math.sin((sa+ea)/2))
        bright = tuple(min(255,c+80) for c in color)
        cv2.line(frame,(cx+int(inner*math.cos((sa+ea)/2)),
                        cy+int(inner*math.sin((sa+ea)/2))),(tip_x,tip_y),bright,1,cv2.LINE_AA)

    # Hub
    hub = int(radius*0.17)
    cv2.circle(frame,(cx,cy),hub,(0,0,0),-1)
    for r,b in [(hub,90),(int(hub*0.80),130),(int(hub*0.60),160),(int(hub*0.40),190),(int(hub*0.20),255)]:
        cv2.circle(frame,(cx,cy),r,(b,b,b),1,cv2.LINE_AA)
    cv2.circle(frame,(cx,cy),int(hub*0.12),(255,255,255),-1)

def draw_middle_ring(frame, cx, cy, radius, ao):
    r = int(radius*1.08)
    # Tick marks
    for i in range(72):
        angle = math.radians(i*5 + ao)
        tlen  = 12 if i%6==0 else (6 if i%3==0 else 3)
        x1=cx+int(r*math.cos(angle));        y1=cy+int(r*math.sin(angle))
        x2=cx+int((r+tlen)*math.cos(angle)); y2=cy+int((r+tlen)*math.sin(angle))
        b = 220 if i%6==0 else (140 if i%3==0 else 60)
        cv2.line(frame,(x1,y1),(x2,y2),(b,b,b),1,cv2.LINE_AA)
    # |X| at 8 compass points
    for i in range(8):
        angle = math.radians(i*45 + ao)
        sx = cx+int((r+20)*math.cos(angle))
        sy = cy+int((r+20)*math.sin(angle))
        cv2.putText(frame,"|X|",(sx-10,sy+4),
                    cv2.FONT_HERSHEY_SIMPLEX,0.32,(230,230,230),1,cv2.LINE_AA)
    # Hollow circles between compass
    for i in range(8):
        angle = math.radians(i*45+22.5+ao)
        sx=cx+int((r+16)*math.cos(angle)); sy=cy+int((r+16)*math.sin(angle))
        cv2.circle(frame,(sx,sy),6,(180,180,180),1,cv2.LINE_AA)
    # White dots at cardinal
    for i in range(4):
        angle=math.radians(i*90+ao)
        wx=cx+int((r-10)*math.cos(angle)); wy=cy+int((r-10)*math.sin(angle))
        cv2.circle(frame,(wx,wy),5,(255,255,255),-1,cv2.LINE_AA)

def draw_crosshairs(frame, cx, cy, radius, ao):
    for i in range(4):
        angle=math.radians(i*90+ao)
        x1=cx+int(radius*0.18*math.cos(angle)); y1=cy+int(radius*0.18*math.sin(angle))
        x2=cx+int(radius*1.12*math.cos(angle)); y2=cy+int(radius*1.12*math.sin(angle))
        cv2.line(frame,(x1,y1),(x2,y2),(60,60,60),1,cv2.LINE_AA)

def draw_rainbow_dotted_ring(frame, cx, cy, r, ao, n=120, gap=2, dot=2):
    for i in range(n):
        if i%gap==0:
            angle=math.radians(i*(360/n)+ao)
            x=cx+int(r*math.cos(angle)); y=cy+int(r*math.sin(angle))
            color=hue2bgr(int(i*(180/n)))
            cv2.circle(frame,(x,y),dot,color,-1,cv2.LINE_AA)

def draw_white_dotted_ring(frame, cx, cy, r, ao, n=90, gap=2, dot=2):
    for i in range(n):
        if i%gap==0:
            angle=math.radians(i*(360/n)+ao)
            x=cx+int(r*math.cos(angle)); y=cy+int(r*math.sin(angle))
            b=int(120+80*math.sin(math.radians(i*4+ao)))
            cv2.circle(frame,(x,y),dot,(b,b,b),-1,cv2.LINE_AA)

def draw_spike_bursts(frame, cx, cy, radius, ao, t):
    for i in range(8):
        angle=math.radians(i*45+ao)
        base_r=int(radius*1.18)
        tip_r =int(radius*1.48)
        hue   = int(i*(180/8)+t*1.5)%180
        color = hue2bgr(hue)
        # Dotted spike line
        steps=14
        for s in range(steps):
            frac = s/steps
            r_   = int(base_r + (tip_r-base_r)*frac)
            sx=cx+int(r_*math.cos(angle)); sy=cy+int(r_*math.sin(angle))
            sz = max(1, int(3-2*frac))
            cv2.circle(frame,(sx,sy),sz,color,-1,cv2.LINE_AA)
        # Arrowhead
        ax=cx+int(tip_r*math.cos(angle)); ay=cy+int(tip_r*math.sin(angle))
        cv2.circle(frame,(ax,ay),3,color,-1,cv2.LINE_AA)
        # Mini side spikes
        for side in [-0.07,0.07]:
            a2=angle+side
            s1x=cx+int((base_r+5)*math.cos(a2)); s1y=cy+int((base_r+5)*math.sin(a2))
            s2x=cx+int((base_r+20)*math.cos(a2));s2y=cy+int((base_r+20)*math.sin(a2))
            dim=tuple(max(0,c//2) for c in color)
            cv2.line(frame,(s1x,s1y),(s2x,s2y),dim,1,cv2.LINE_AA)

# ── Chasing loop chain ───────────────────────
class ChasingLoop:
    def __init__(self, cx, cy, orbit_r):
        self.orbit_r=orbit_r
        self.angle=random.uniform(0,2*math.pi)
        self.speed=0.05
        self.life=random.randint(80,200)
        self.sz=random.randint(5,9)

    def update(self): self.angle+=self.speed; self.life-=1

    def draw(self,frame,cx,cy):
        a=min(1.0,self.life/30)
        for k in range(6):
            da=self.angle-k*0.09
            x=cx+int(self.orbit_r*math.cos(da))
            y=cy+int(self.orbit_r*math.sin(da))
            b=int((190-k*28)*a)
            sz=max(1,self.sz-k//2)
            cv2.circle(frame,(x,y),sz,(b,b,b),1,cv2.LINE_AA)

# ── Flying arc ───────────────────────────────
class FlyingArc:
    def __init__(self, cx, cy, radius):
        ang=random.uniform(0,2*math.pi)
        dist=radius*random.uniform(1.5,2.0)
        self.cx=int(cx+dist*math.cos(ang))
        self.cy=int(cy+dist*math.sin(ang))
        self.start_a=random.uniform(0,360)
        self.span=random.uniform(50,110)
        self.r=random.randint(18,45)
        self.life=random.randint(50,110)
        self.max_life=self.life
        self.hue=random.randint(0,179)
        self.vx=random.uniform(-1.2,1.2)
        self.vy=random.uniform(-1.2,1.2)

    def update(self):
        self.cx+=int(self.vx); self.cy+=int(self.vy)
        self.start_a+=4; self.life-=1

    def draw(self,frame):
        a=min(1.0,self.life/30)
        col=hue2bgr(self.hue,val=int(220*a))
        cv2.ellipse(frame,(self.cx,self.cy),(self.r,self.r//2),0,
                    self.start_a,self.start_a+self.span,col,2,cv2.LINE_AA)

# ── Orbit symbol ─────────────────────────────
class OrbitSymbol:
    def __init__(self,cx,cy,orbit_r):
        self.orbit_r=orbit_r+random.randint(-12,12)
        self.angle=random.uniform(0,2*math.pi)
        self.speed=random.uniform(0.005,0.014)*random.choice([-1,1])
        self.life=random.randint(120,260)
        self.kind=random.choice(['circle','dot','double','diamond'])

    def update(self): self.angle+=self.speed; self.life-=1

    def draw(self,frame,cx,cy):
        a=min(1.0,self.life/40)
        x=cx+int(self.orbit_r*math.cos(self.angle))
        y=cy+int(self.orbit_r*math.sin(self.angle))
        b=int(200*a)
        if self.kind=='circle':
            cv2.circle(frame,(x,y),6,(b,b,b),1,cv2.LINE_AA)
        elif self.kind=='dot':
            cv2.circle(frame,(x,y),3,(b,b,b),-1)
        elif self.kind=='double':
            cv2.circle(frame,(x,y),7,(b,b,b),1,cv2.LINE_AA)
            cv2.circle(frame,(x,y),4,(b//2,b//2,b//2),1,cv2.LINE_AA)
        else:
            pts=np.array([(x,y-6),(x+5,y),(x,y+6),(x-5,y)])
            cv2.polylines(frame,[pts],True,(b,b,b),1,cv2.LINE_AA)

chasing_loops=[]; flying_arcs=[]; orbit_symbols=[]

def get_hand_size(lm,fw,fh):
    w=lm.landmark[0]; m=lm.landmark[12]
    return math.sqrt(((m.x-w.x)*fw)**2+((m.y-w.y)*fh)**2)

def get_rotation(lm,fw,fh):
    w=lm.landmark[0]; m=lm.landmark[9]
    return math.degrees(math.atan2((m.y-w.y)*fh,(m.x-w.x)*fw))

print("✨ Radiance Aura | Move & rotate hand | Q = quit")

while True:
    ret,frame=cap.read()
    if not ret: break

    frame=cv2.flip(frame,1)
    h,w=frame.shape[:2]

    # Dark background - key fix
    frame=cv2.addWeighted(frame,0.45,np.zeros_like(frame),0.55,0)

    rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    results=hands.process(rgb)

    if results.multi_hand_landmarks:
        lm=results.multi_hand_landmarks[0]
        cx=int(lm.landmark[9].x*w)
        cy=int(lm.landmark[9].y*h)

        hand_size=get_hand_size(lm,w,h)
        rotation=get_rotation(lm,w,h)
        radius=max(70,min(int(hand_size*1.0),240))
        ao=rotation*1.8

        # Draw in order
        draw_crosshairs(frame,cx,cy,radius,ao+t*0.5)
        draw_rose_wheel(frame,cx,cy,radius,ao+t*0.7)
        draw_middle_ring(frame,cx,cy,radius,ao+t*0.5)
        draw_spike_bursts(frame,cx,cy,radius,ao+t*0.5,t)

        r1=int(radius*1.30)
        draw_white_dotted_ring(frame,cx,cy,r1,-ao-t*0.35,n=90,gap=2,dot=2)

        r2=int(radius*1.50)
        draw_rainbow_dotted_ring(frame,cx,cy,r2,ao*0.4-t*0.28,n=140,gap=2,dot=2)

        r3=int(radius*1.68)
        draw_rainbow_dotted_ring(frame,cx,cy,r3,-ao*0.2+t*0.18,n=160,gap=3,dot=2)

        # Spawn
        if t%7==0:  chasing_loops.append(ChasingLoop(cx,cy,int(radius*1.58)))
        if t%22==0: flying_arcs.append(FlyingArc(cx,cy,radius))
        if t%14==0:
            orbit_symbols.append(OrbitSymbol(cx,cy,int(radius*1.12)))
            orbit_symbols.append(OrbitSymbol(cx,cy,int(radius*1.25)))

        chasing_loops[:]=[x for x in chasing_loops if x.life>0]
        for x in chasing_loops: x.update(); x.draw(frame,cx,cy)

        flying_arcs[:]=[x for x in flying_arcs if x.life>0]
        for x in flying_arcs: x.update(); x.draw(frame)

        orbit_symbols[:]=[x for x in orbit_symbols if x.life>0]
        for x in orbit_symbols: x.update(); x.draw(frame,cx,cy)

    else:
        chasing_loops.clear(); flying_arcs.clear(); orbit_symbols.clear()

    t+=1
    cv2.imshow("Radiance Aura",frame)
    if cv2.waitKey(1)&0xFF==ord('q'): break

cap.release()
cv2.destroyAllWindows()