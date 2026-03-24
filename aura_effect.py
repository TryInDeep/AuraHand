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

# ── Floating number ──────────────────────────
class FloatingNumber:
    def __init__(self, cx, cy, orbit_r):
        self.orbit_r = orbit_r + random.randint(-25, 30)
        self.angle   = random.uniform(0, 2*math.pi)
        self.speed   = random.uniform(0.004, 0.013) * random.choice([-1,1])
        self.num     = str(random.randint(0, 9))
        self.life    = random.randint(90, 220)
        self.max_life= self.life
        self.fs      = random.uniform(0.28, 0.52)
        self.color   = random.choice([
            (80, 255, 80),(100, 255, 160),(160, 255, 80),(200, 255, 120)
        ])

    def update(self): self.angle += self.speed; self.life -= 1

    def draw(self, frame, cx, cy):
        a = min(1.0, self.life / 40)
        x = cx + int(self.orbit_r * math.cos(self.angle))
        y = cy + int(self.orbit_r * math.sin(self.angle))
        cv2.putText(frame, self.num, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                    self.fs, tuple(int(c*a) for c in self.color), 1, cv2.LINE_AA)

# ── Hollow orbit circle ───────────────────────
class OrbitCircle:
    def __init__(self, cx, cy, orbit_r):
        self.orbit_r = orbit_r + random.randint(-20, 25)
        self.angle   = random.uniform(0, 2*math.pi)
        self.speed   = random.uniform(0.006, 0.018) * random.choice([-1,1])
        self.r       = random.randint(4, 9)
        self.life    = random.randint(120, 280)
        self.max_life= self.life

    def update(self): self.angle += self.speed; self.life -= 1

    def draw(self, frame, cx, cy):
        a = min(1.0, self.life / 50)
        x = cx + int(self.orbit_r * math.cos(self.angle))
        y = cy + int(self.orbit_r * math.sin(self.angle))
        b = int(210 * a)
        cv2.circle(frame, (x,y), self.r, (b,b,b), 1, cv2.LINE_AA)

# ── Chasing loop (double ring) ────────────────
class ChasingLoop:
    def __init__(self, cx, cy, orbit_r):
        self.orbit_r = orbit_r
        self.angle   = random.uniform(0, 2*math.pi)
        self.speed   = 0.045
        self.life    = random.randint(60, 160)
        self.max_life= self.life
        self.sz      = random.randint(5, 10)

    def update(self): self.angle += self.speed; self.life -= 1

    def draw(self, frame, cx, cy):
        a = min(1.0, self.life / 30)
        x = cx + int(self.orbit_r * math.cos(self.angle))
        y = cy + int(self.orbit_r * math.sin(self.angle))
        b = int(190 * a)
        cv2.circle(frame, (x,y), self.sz,    (b,b,b),      1, cv2.LINE_AA)
        cv2.circle(frame, (x,y), self.sz//2, (b//2,b//2,b//2), 1)

# ── Collections ──────────────────────────────
float_nums    = []
orbit_circles = []
chasing_loops = []

# ── Color wheel ──────────────────────────────
def draw_color_wheel(frame, cx, cy, radius, ao):
    seg   = 52
    inner = int(radius * 0.26)
    outer = int(radius * 0.86)
    for i in range(seg):
        sa = math.radians(i * (360/seg) + ao)
        ea = math.radians((i+1) * (360/seg) + ao)
        hue   = int(i * (180/seg))
        color = tuple(int(c) for c in cv2.cvtColor(
            np.uint8([[[hue, 230, 220]]]), cv2.COLOR_HSV2BGR)[0][0])
        for r in range(inner, outer, 2):
            x1 = cx + int(r * math.cos(sa)); y1 = cy + int(r * math.sin(sa))
            x2 = cx + int(r * math.cos(ea)); y2 = cy + int(r * math.sin(ea))
            cv2.line(frame, (x1,y1), (x2,y2), color, 2)
    # hub
    hub = int(radius * 0.23)
    cv2.circle(frame, (cx,cy), hub, (8,8,12), -1)
    cv2.circle(frame, (cx,cy), int(hub*0.45), (160,160,200), -1)
    cv2.circle(frame, (cx,cy), int(hub*0.22), (230,230,255), -1)

# ── Spoke lines ───────────────────────────────
def draw_spokes(frame, cx, cy, radius, ao):
    for i in range(26):
        angle = math.radians(i * (360/26) + ao)
        r1 = int(radius * 0.86); r2 = int(radius * 1.06)
        x1 = cx+int(r1*math.cos(angle)); y1 = cy+int(r1*math.sin(angle))
        x2 = cx+int(r2*math.cos(angle)); y2 = cy+int(r2*math.sin(angle))
        b  = int(110 + 90*math.sin(math.radians(i*14 + ao)))
        cv2.line(frame, (x1,y1), (x2,y2), (b,b,b), 1, cv2.LINE_AA)

# ── Dotted ring ───────────────────────────────
def dotted_ring(frame, cx, cy, r, ao, color, dot=2, n=80, gap=2):
    for i in range(n):
        if i % gap == 0:
            a  = math.radians(i*(360/n) + ao)
            x  = cx + int(r*math.cos(a))
            y  = cy + int(r*math.sin(a))
            cv2.circle(frame, (x,y), dot, color, -1, cv2.LINE_AA)

# ── Tick ring ─────────────────────────────────
def tick_ring(frame, cx, cy, r, ao):
    for i in range(40):
        angle = math.radians(i*9 + ao)
        tlen  = 9 if i%4==0 else 4
        x1 = cx+int(r*math.cos(angle));         y1 = cy+int(r*math.sin(angle))
        x2 = cx+int((r+tlen)*math.cos(angle));  y2 = cy+int((r+tlen)*math.sin(angle))
        b  = 160 if i%4==0 else 80
        cv2.line(frame, (x1,y1), (x2,y2), (b,b,b), 1, cv2.LINE_AA)

# ── Clock-style inner arc with numbers ───────
def inner_clock_arc(frame, cx, cy, radius, ao, t):
    arc_r = int(radius * 0.55)
    for i in range(12):
        angle = math.radians(i*30 + ao*0.4)
        ax = cx + int(arc_r*math.cos(angle))
        ay = cy + int(arc_r*math.sin(angle))
        num = str(i if i > 0 else 12)
        b   = int(80 + 60*math.sin(t*0.05 + i))
        cv2.putText(frame, num, (ax-5, ay+4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.28, (b,b,b), 1, cv2.LINE_AA)

# ── Hand helpers ─────────────────────────────
def get_hand_size(lm, fw, fh):
    w = lm.landmark[0]; m = lm.landmark[12]
    return math.sqrt(((m.x-w.x)*fw)**2 + ((m.y-w.y)*fh)**2)

def get_rotation(lm, fw, fh):
    w = lm.landmark[0]; m = lm.landmark[9]
    return math.degrees(math.atan2((m.y-w.y)*fh, (m.x-w.x)*fw))

# ─────────────────────────────────────────────
print("✨ Aura Effect | Move & rotate your hand | Q = quit")

while True:
    ret, frame = cap.read()
    if not ret: break

    frame = cv2.flip(frame, 1)
    h, w  = frame.shape[:2]
    frame = cv2.addWeighted(frame, 0.70, np.zeros_like(frame), 0.30, 0)

    rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        lm = results.multi_hand_landmarks[0]
        cx = int(lm.landmark[9].x * w)
        cy = int(lm.landmark[9].y * h)

        hand_size = get_hand_size(lm, w, h)
        rotation  = get_rotation(lm, w, h)
        radius    = max(55, min(int(hand_size * 0.88), 215))
        ao        = rotation * 1.8

        # --- Draw layers ---
        draw_color_wheel(frame, cx, cy, radius, ao + t*0.85)
        inner_clock_arc(frame, cx, cy, radius, ao + t*0.85, t)
        draw_spokes(frame, cx, cy, radius, ao + t*0.85)

        r1 = int(radius * 1.11)
        dotted_ring(frame, cx, cy, r1, -ao - t*0.45, (200,200,200), dot=2, n=80, gap=2)

        r2 = int(radius * 1.18)
        tick_ring(frame, cx, cy, r2, ao*0.5 + t*0.22)

        r3 = int(radius * 1.38)
        dotted_ring(frame, cx, cy, r3, ao*0.3 - t*0.28, (100,220,120), dot=2, n=100, gap=2)

        r4 = int(radius * 1.56)
        dotted_ring(frame, cx, cy, r4, -ao*0.2 + t*0.16, (55,140,75), dot=1, n=130, gap=3)

        # Pulsing glow on outer ring
        pulse = int(3*math.sin(t*0.08))
        for off in range(3,0,-1):
            b = 35 + off*18
            cv2.circle(frame, (cx,cy), r3+pulse+off, (b, int(b*1.8), b), 1, cv2.LINE_AA)

        # --- Spawn ---
        if t % 11 == 0:
            for _ in range(2): float_nums.append(FloatingNumber(cx, cy, r3))
        if t % 19 == 0:
            orbit_circles.append(OrbitCircle(cx, cy, r2))
            orbit_circles.append(OrbitCircle(cx, cy, r3))
        if t % 7 == 0:
            chasing_loops.append(ChasingLoop(cx, cy, int(radius*1.47)))

        # --- Update & draw ---
        float_nums[:] = [n for n in float_nums if n.life > 0]
        for n in float_nums: n.update(); n.draw(frame, cx, cy)

        orbit_circles[:] = [o for o in orbit_circles if o.life > 0]
        for o in orbit_circles: o.update(); o.draw(frame, cx, cy)

        chasing_loops[:] = [c for c in chasing_loops if c.life > 0]
        for c in chasing_loops: c.update(); c.draw(frame, cx, cy)

    else:
        float_nums.clear(); orbit_circles.clear(); chasing_loops.clear()

    t += 1
    cv2.imshow("Aura Effect", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()