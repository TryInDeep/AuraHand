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

# --- Gold & White Color Palette ---
GOLD_BRIGHT  = (0, 215, 255)   # BGR gold
GOLD_MID     = (0, 180, 220)
GOLD_DARK    = (0, 120, 160)
WHITE_BRIGHT = (240, 240, 255)
WHITE_MID    = (180, 180, 200)
WHITE_DIM    = (80, 80, 100)
CREAM        = (200, 230, 255)

WHEEL_COLORS = [
    (0, 200, 255),   # gold
    (0, 215, 255),   # bright gold
    (20, 200, 240),  # warm gold
    (0, 170, 210),   # deep gold
    (200, 220, 255), # white-gold
    (180, 200, 255), # cream white
    (240, 240, 255), # pure white
    (160, 190, 250), # cool white
]


class FloatingNumber:
    def __init__(self, cx, cy, orbit_r):
        self.orbit_r = orbit_r + random.randint(-20, 20)
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.003, 0.012) * random.choice([-1, 1])
        self.number = str(random.randint(0, 9))
        self.life = random.randint(80, 200)
        self.max_life = self.life
        self.size = random.uniform(0.3, 0.55)
        self.color = random.choice([GOLD_BRIGHT, GOLD_MID, WHITE_BRIGHT, CREAM])

    def update(self):
        self.angle += self.speed
        self.life -= 1

    def draw(self, frame, cx, cy):
        alpha = min(1.0, self.life / 40)
        x = cx + int(self.orbit_r * math.cos(self.angle))
        y = cy + int(self.orbit_r * math.sin(self.angle))
        color = tuple(int(c * alpha) for c in self.color)
        cv2.putText(frame, self.number, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, self.size, color, 1, cv2.LINE_AA)


class OrbitCircle:
    def __init__(self, cx, cy, orbit_r):
        self.orbit_r = orbit_r + random.randint(-15, 25)
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.008, 0.02) * random.choice([-1, 1])
        self.radius = random.randint(3, 7)
        self.life = random.randint(100, 250)
        self.max_life = self.life
        self.color = random.choice([GOLD_BRIGHT, WHITE_BRIGHT, CREAM])

    def update(self):
        self.angle += self.speed
        self.life -= 1

    def draw(self, frame, cx, cy):
        alpha = min(1.0, self.life / 40)
        x = cx + int(self.orbit_r * math.cos(self.angle))
        y = cy + int(self.orbit_r * math.sin(self.angle))
        color = tuple(int(c * alpha) for c in self.color)
        cv2.circle(frame, (x, y), self.radius, color, 1, cv2.LINE_AA)


class ChasingLoop:
    def __init__(self, cx, cy, orbit_r):
        self.orbit_r = orbit_r
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = 0.04
        self.life = random.randint(60, 150)
        self.max_life = self.life
        self.size = random.randint(4, 9)

    def update(self):
        self.angle += self.speed
        self.life -= 1

    def draw(self, frame, cx, cy):
        alpha = min(1.0, self.life / 30)
        x = cx + int(self.orbit_r * math.cos(self.angle))
        y = cy + int(self.orbit_r * math.sin(self.angle))
        color = tuple(int(c * alpha) for c in GOLD_MID)
        inner = tuple(int(c * alpha * 0.5) for c in CREAM)
        cv2.circle(frame, (x, y), self.size, color, 1, cv2.LINE_AA)
        cv2.circle(frame, (x, y), self.size // 2, inner, 1)


float_nums = []
orbit_circles = []
chasing_loops = []


def draw_color_wheel(frame, cx, cy, radius, angle_offset):
    num_segments = 48
    inner_r = int(radius * 0.28)
    outer_r = int(radius * 0.88)

    for i in range(num_segments):
        start_a = math.radians(i * (360 / num_segments) + angle_offset)
        end_a   = math.radians((i + 1) * (360 / num_segments) + angle_offset)

        # Cycle through gold/white shades only
        color = WHEEL_COLORS[i % len(WHEEL_COLORS)]

        for r in range(inner_r, outer_r, 2):
            x1 = cx + int(r * math.cos(start_a))
            y1 = cy + int(r * math.sin(start_a))
            x2 = cx + int(r * math.cos(end_a))
            y2 = cy + int(r * math.sin(end_a))
            cv2.line(frame, (x1, y1), (x2, y2), color, 2)

    # Dark center hub with gold dot
    hub_r = int(radius * 0.25)
    cv2.circle(frame, (cx, cy), hub_r, (5, 5, 10), -1)
    cv2.circle(frame, (cx, cy), int(hub_r * 0.5), GOLD_MID, -1)
    cv2.circle(frame, (cx, cy), int(hub_r * 0.25), WHITE_BRIGHT, -1)


def draw_spoke_lines(frame, cx, cy, radius, angle_offset):
    for i in range(24):
        angle = math.radians(i * 15 + angle_offset)
        r1 = int(radius * 0.88)
        r2 = int(radius * 1.06)
        x1 = cx + int(r1 * math.cos(angle))
        y1 = cy + int(r1 * math.sin(angle))
        x2 = cx + int(r2 * math.cos(angle))
        y2 = cy + int(r2 * math.sin(angle))
        brightness = int(100 + 80 * math.sin(math.radians(i * 15 + angle_offset)))
        color = (0, int(brightness * 0.8), brightness)  # gold-toned
        cv2.line(frame, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)


def draw_dotted_ring(frame, cx, cy, ring_r, angle_offset, color, dot_size=2, num_dots=72, gap=2):
    for i in range(num_dots):
        if i % gap == 0:
            angle = math.radians(i * (360 / num_dots) + angle_offset)
            x = cx + int(ring_r * math.cos(angle))
            y = cy + int(ring_r * math.sin(angle))
            cv2.circle(frame, (x, y), dot_size, color, -1, cv2.LINE_AA)


def draw_tick_ring(frame, cx, cy, ring_r, angle_offset):
    for i in range(36):
        angle = math.radians(i * 10 + angle_offset)
        tick_len = 8 if i % 3 == 0 else 4
        x1 = cx + int(ring_r * math.cos(angle))
        y1 = cy + int(ring_r * math.sin(angle))
        x2 = cx + int((ring_r + tick_len) * math.cos(angle))
        y2 = cy + int((ring_r + tick_len) * math.sin(angle))
        color = GOLD_MID if i % 3 == 0 else GOLD_DARK
        cv2.line(frame, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)


def draw_glow_ring(frame, cx, cy, ring_r, t):
    # Pulsing gold glow ring
    pulse = int(3 * math.sin(t * 0.08))
    for offset in range(3, 0, -1):
        alpha = 40 + offset * 15
        cv2.circle(frame, (cx, cy), ring_r + pulse + offset,
                   (0, alpha, int(alpha * 1.3)), 1, cv2.LINE_AA)


def get_hand_size(landmarks, fw, fh):
    w = landmarks.landmark[0]
    m = landmarks.landmark[12]
    return math.sqrt(((m.x - w.x) * fw) ** 2 + ((m.y - w.y) * fh) ** 2)


def get_rotation_angle(landmarks, fw, fh):
    wrist = landmarks.landmark[0]
    mid   = landmarks.landmark[9]
    dx = (mid.x - wrist.x) * fw
    dy = (mid.y - wrist.y) * fh
    return math.degrees(math.atan2(dy, dx))


print("✨ Gold Aura Effect — Press Q to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]

    dark = np.zeros_like(frame)
    frame = cv2.addWeighted(frame, 0.70, dark, 0.30, 0)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        lm = results.multi_hand_landmarks[0]
        cx = int(lm.landmark[9].x * w)
        cy = int(lm.landmark[9].y * h)

        hand_size    = get_hand_size(lm, w, h)
        rotation     = get_rotation_angle(lm, w, h)
        radius       = max(55, min(int(hand_size * 0.85), 210))
        angle_offset = rotation * 1.8

        # Wheel
        draw_color_wheel(frame, cx, cy, radius, angle_offset + t * 0.8)
        draw_spoke_lines(frame, cx, cy, radius, angle_offset + t * 0.8)

        # Rings
        ring1_r = int(radius * 1.12)
        draw_dotted_ring(frame, cx, cy, ring1_r, -angle_offset - t * 0.4,
                         WHITE_MID, dot_size=2, num_dots=80, gap=2)

        ring2_r = int(radius * 1.18)
        draw_tick_ring(frame, cx, cy, ring2_r, angle_offset * 0.5 + t * 0.2)

        ring3_r = int(radius * 1.38)
        draw_dotted_ring(frame, cx, cy, ring3_r, angle_offset * 0.3 - t * 0.25,
                         GOLD_BRIGHT, dot_size=2, num_dots=100, gap=2)

        ring4_r = int(radius * 1.55)
        draw_dotted_ring(frame, cx, cy, ring4_r, -angle_offset * 0.2 + t * 0.15,
                         GOLD_DARK, dot_size=1, num_dots=120, gap=3)

        draw_glow_ring(frame, cx, cy, ring3_r, t)

        # Spawn effects
        if t % 12 == 0:
            for _ in range(2):
                float_nums.append(FloatingNumber(cx, cy, ring3_r))
        if t % 20 == 0:
            orbit_circles.append(OrbitCircle(cx, cy, ring2_r))
            orbit_circles.append(OrbitCircle(cx, cy, ring3_r))
        if t % 8 == 0:
            chasing_loops.append(ChasingLoop(cx, cy, int(radius * 1.48)))

        float_nums[:] = [n for n in float_nums if n.life > 0]
        for n in float_nums:
            n.update()
            n.draw(frame, cx, cy)

        orbit_circles[:] = [o for o in orbit_circles if o.life > 0]
        for o in orbit_circles:
            o.update()
            o.draw(frame, cx, cy)

        chasing_loops[:] = [c for c in chasing_loops if c.life > 0]
        for c in chasing_loops:
            c.update()
            c.draw(frame, cx, cy)

    else:
        float_nums.clear()
        orbit_circles.clear()
        chasing_loops.clear()

    t += 1
    cv2.imshow("Gold Aura Effect", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()