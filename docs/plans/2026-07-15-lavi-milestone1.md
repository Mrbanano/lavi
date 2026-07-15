# Lavi Milestone 1 - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-screen kiosk UI on Raspberry Pi 3B showing a modular animated face with smooth transitions.

**Architecture:** Python + Pygame, modular face parts (eyes, mouth), state machine cycling through expressions, smooth opacity transitions.

**Tech Stack:** Python 3, Pygame, JSON config

---

## File Structure

```
lavi/
├── main.py              # Entry point, fullscreen kiosk
├── config.json          # Default configuration
├── engine/
│   ├── __init__.py
│   ├── state_machine.py # Expression cycle control
│   └── animator.py      # Smooth transitions
├── faces/
│   ├── __init__.py
│   ├── base.py          # Face base class
│   ├── parts/
│   │   ├── __init__.py
│   │   ├── eye.py       # Eye rendering
│   │   └── mouth.py     # Mouth rendering
│   └── expressions/
│       ├── __init__.py
│       ├── happy.py
│       ├── laugh.py
│       ├── wink.py
│       ├── love.py
│       ├── sad.py
│       ├── surprised.py
│       └── sleepy.py
└── renderer.py          # Pygame rendering
```

---

### Task 1: Project Setup + Git Init

**Files:**
- Create: `lavi/config.json`
- Create: `lavi/engine/__init__.py`
- Create: `lavi/faces/__init__.py`
- Create: `lavi/faces/parts/__init__.py`
- Create: `lavi/faces/expressions/__init__.py`
- Create: `.gitignore`

- [ ] **Step 1: Initialize git repo**

```bash
cd /Users/alvarocastillo/dev/agents_try
git init
```

- [ ] **Step 2: Create .gitignore**

```
__pycache__/
*.pyc
.env
venv/
*.egg-info/
dist/
build/
.DS_Store
```

- [ ] **Step 3: Create folder structure**

```bash
mkdir -p lavi/engine lavi/faces/parts lavi/faces/expressions
touch lavi/engine/__init__.py lavi/faces/__init__.py lavi/faces/parts/__init__.py lavi/faces/expressions/__init__.py
```

- [ ] **Step 4: Create config.json**

```json
{
  "display": {
    "fullscreen": true,
    "bg_color": "#000000"
  },
  "animation": {
    "transition_speed": 0.4,
    "expression_duration": 3.5,
    "blink_interval_min": 3,
    "blink_interval_max": 5
  },
  "expressions": ["happy", "laugh", "wink", "love", "sad", "surprised", "sleepy"],
  "face": {
    "eye_color": "#ffffff",
    "mouth_color": "#ffffff",
    "heart_color": "#ff6b9d"
  }
}
```

- [ ] **Step 5: Initial commit**

```bash
git add .
git commit -m "feat: initial project structure with config"
```

---

### Task 2: Eye Part

**Files:**
- Create: `lavi/faces/parts/eye.py`

- [ ] **Step 1: Create Eye class**

```python
import pygame

class EyeType:
    NORMAL = "normal"
    CLOSED = "closed"
    HEART = "heart"
    WINK = "wink"
    SLEEPY = "sleepy"

class Eye:
    def __init__(self, color="#ffffff"):
        self.color = pygame.Color(color)
        self.current_type = EyeType.NORMAL
        self.alpha = 255
        self.blink_progress = 0.0

    def set_type(self, eye_type):
        self.current_type = eye_type

    def set_alpha(self, alpha):
        self.alpha = alpha

    def draw(self, surface, x, y, size):
        if self.alpha <= 0:
            return

        temp = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        radius = size // 2

        color = (*self.color[:3], int(self.alpha))

        if self.current_type == EyeType.NORMAL:
            pygame.draw.circle(temp, color, center, radius)

        elif self.current_type == EyeType.CLOSED:
            line_color = color
            pygame.draw.line(temp, line_color, (size * 0.2, center[1]), (size * 0.8, center[1]), max(2, size // 15))

        elif self.current_type == EyeType.HEART:
            self._draw_heart(temp, center, radius, color)

        elif self.current_type == EyeType.WINK:
            pygame.draw.circle(temp, color, center, radius)

        elif self.current_type == EyeType.SLEEPY:
            line_color = color
            pygame.draw.line(temp, line_color, (size * 0.15, center[1]), (size * 0.85, center[1]), max(2, size // 12))

        surface.blit(temp, (x, y))

    def _draw_heart(self, surface, center, radius, color):
        cx, cy = center
        r = radius * 0.8
        points = []
        for angle in range(360):
            import math
            t = math.radians(angle)
            x = r * 16 * math.sin(t) ** 3
            y = -r * (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
            points.append((cx + x/17, cy + y/17))
        if len(points) > 2:
            pygame.draw.polygon(surface, color, points)
```

- [ ] **Step 2: Test import**

```bash
cd /Users/alvarocastillo/dev/agents_try
python3 -c "from lavi.faces.parts.eye import Eye, EyeType; print('Eye OK')"
```

Expected: `Eye OK`

- [ ] **Step 3: Commit**

```bash
git add lavi/faces/parts/eye.py
git commit -m "feat: add Eye part with normal, closed, heart, sleepy types"
```

---

### Task 3: Mouth Part

**Files:**
- Create: `lavi/faces/parts/mouth.py`

- [ ] **Step 1: Create Mouth class**

```python
import pygame
import math

class MouthType:
    SMILE = "smile"
    OPEN = "open"
    SAD = "sad"
    SURPRISE = "surprise"
    LINE = "line"

class Mouth:
    def __init__(self, color="#ffffff"):
        self.color = pygame.Color(color)
        self.current_type = MouthType.SMILE
        self.alpha = 255

    def set_type(self, mouth_type):
        self.current_type = mouth_type

    def set_alpha(self, alpha):
        self.alpha = alpha

    def draw(self, surface, x, y, width, height):
        if self.alpha <= 0:
            return

        temp = pygame.Surface((width, height), pygame.SRCALPHA)
        color = (*self.color[:3], int(self.alpha))
        line_width = max(2, width // 15)

        cx, cy = width // 2, height // 2

        if self.current_type == MouthType.SMILE:
            rect = pygame.Rect(width * 0.1, 0, width * 0.8, height * 0.8)
            pygame.draw.arc(temp, color, rect, math.radians(200), math.radians(340), line_width)

        elif self.current_type == MouthType.OPEN:
            mouth_rect = pygame.Rect(width * 0.15, height * 0.1, width * 0.7, height * 0.8)
            pygame.draw.ellipse(temp, color, mouth_rect)

        elif self.current_type == MouthType.SAD:
            rect = pygame.Rect(width * 0.1, height * 0.2, width * 0.8, height * 0.8)
            pygame.draw.arc(temp, color, rect, math.radians(20), math.radians(160), line_width)

        elif self.current_type == MouthType.SURPRISE:
            pygame.draw.circle(temp, color, (cx, cy), min(width, height) // 3)

        elif self.current_type == MouthType.LINE:
            pygame.draw.line(temp, color, (width * 0.2, cy), (width * 0.8, cy), line_width)

        surface.blit(temp, (x, y))
```

- [ ] **Step 2: Test import**

```bash
python3 -c "from lavi.faces.parts.mouth import Mouth, MouthType; print('Mouth OK')"
```

Expected: `Mouth OK`

- [ ] **Step 3: Commit**

```bash
git add lavi/faces/parts/mouth.py
git commit -m "feat: add Mouth part with smile, open, sad, surprise, line types"
```

---

### Task 4: Base Face Class

**Files:**
- Create: `lavi/faces/base.py`

- [ ] **Step 1: Create Face base class**

```python
from lavi.faces.parts.eye import Eye, EyeType
from lavi.faces.parts.mouth import Mouth, MouthType

class Face:
    def __init__(self, config=None):
        config = config or {}
        face_config = config.get("face", {})

        self.left_eye = Eye(face_config.get("eye_color", "#ffffff"))
        self.right_eye = Eye(face_config.get("eye_color", "#ffffff"))
        self.mouth = Mouth(face_config.get("mouth_color", "#ffffff"))
        self.alpha = 255
        self.name = "base"

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.left_eye.set_alpha(alpha)
        self.right_eye.set_alpha(alpha)
        self.mouth.set_alpha(alpha)

    def setup(self):
        pass

    def draw(self, surface, face_rect):
        x, y, w, h = face_rect
        eye_size = int(w * 0.18)
        eye_y = int(y + h * 0.35)
        left_eye_x = int(x + w * 0.22)
        right_eye_x = int(x + w * 0.60)

        self.left_eye.draw(surface, left_eye_x, eye_y, eye_size)
        self.right_eye.draw(surface, right_eye_x, eye_y, eye_size)

        mouth_width = int(w * 0.28)
        mouth_height = int(h * 0.15)
        mouth_x = x + (w - mouth_width) // 2
        mouth_y = int(y + h * 0.60)

        self.mouth.draw(surface, mouth_x, mouth_y, mouth_width, mouth_height)
```

- [ ] **Step 2: Test import**

```bash
python3 -c "from lavi.faces.base import Face; print('Face OK')"
```

Expected: `Face OK`

- [ ] **Step 3: Commit**

```bash
git add lavi/faces/base.py
git commit -m "feat: add Face base class with eye/mouth positioning"
```

---

### Task 5: Expressions

**Files:**
- Create: `lavi/faces/expressions/happy.py`
- Create: `lavi/faces/expressions/laugh.py`
- Create: `lavi/faces/expressions/wink.py`
- Create: `lavi/faces/expressions/love.py`
- Create: `lavi/faces/expressions/sad.py`
- Create: `lavi/faces/expressions/surprised.py`
- Create: `lavi/faces/expressions/sleepy.py`
- Create: `lavi/faces/expressions/__init__.py`

- [ ] **Step 1: Create happy expression**

```python
from lavi.faces.base import Face
from lavi.faces.parts.eye import EyeType
from lavi.faces.parts.mouth import MouthType

class HappyFace(Face):
    def __init__(self, config=None):
        super().__init__(config)
        self.name = "happy"

    def setup(self):
        self.left_eye.set_type(EyeType.NORMAL)
        self.right_eye.set_type(EyeType.NORMAL)
        self.mouth.set_type(MouthType.SMILE)
```

- [ ] **Step 2: Create laugh expression**

```python
from lavi.faces.base import Face
from lavi.faces.parts.eye import EyeType
from lavi.faces.parts.mouth import MouthType

class LaughFace(Face):
    def __init__(self, config=None):
        super().__init__(config)
        self.name = "laugh"

    def setup(self):
        self.left_eye.set_type(EyeType.CLOSED)
        self.right_eye.set_type(EyeType.CLOSED)
        self.mouth.set_type(MouthType.OPEN)
```

- [ ] **Step 3: Create wink expression**

```python
from lavi.faces.base import Face
from lavi.faces.parts.eye import EyeType
from lavi.faces.parts.mouth import MouthType

class WinkFace(Face):
    def __init__(self, config=None):
        super().__init__(config)
        self.name = "wink"

    def setup(self):
        self.left_eye.set_type(EyeType.NORMAL)
        self.right_eye.set_type(EyeType.CLOSED)
        self.mouth.set_type(MouthType.SMILE)
```

- [ ] **Step 4: Create love expression**

```python
from lavi.faces.base import Face
from lavi.faces.parts.eye import EyeType
from lavi.faces.parts.mouth import MouthType

class LoveFace(Face):
    def __init__(self, config=None):
        super().__init__(config)
        self.name = "love"

    def setup(self):
        self.left_eye.set_type(EyeType.HEART)
        self.right_eye.set_type(EyeType.HEART)
        self.mouth.set_type(MouthType.LINE)
```

- [ ] **Step 5: Create sad expression**

```python
from lavi.faces.base import Face
from lavi.faces.parts.eye import EyeType
from lavi.faces.parts.mouth import MouthType

class SadFace(Face):
    def __init__(self, config=None):
        super().__init__(config)
        self.name = "sad"

    def setup(self):
        self.left_eye.set_type(EyeType.NORMAL)
        self.right_eye.set_type(EyeType.NORMAL)
        self.mouth.set_type(MouthType.SAD)
```

- [ ] **Step 6: Create surprised expression**

```python
from lavi.faces.base import Face
from lavi.faces.parts.eye import EyeType
from lavi.faces.parts.mouth import MouthType

class SurprisedFace(Face):
    def __init__(self, config=None):
        super().__init__(config)
        self.name = "surprised"

    def setup(self):
        self.left_eye.set_type(EyeType.NORMAL)
        self.right_eye.set_type(EyeType.NORMAL)
        self.mouth.set_type(MouthType.SURPRISE)
```

- [ ] **Step 7: Create sleepy expression**

```python
from lavi.faces.base import Face
from lavi.faces.parts.eye import EyeType
from lavi.faces.parts.mouth import MouthType

class SleepyFace(Face):
    def __init__(self, config=None):
        super().__init__(config)
        self.name = "sleepy"

    def setup(self):
        self.left_eye.set_type(EyeType.SLEEPY)
        self.right_eye.set_type(EyeType.SLEEPY)
        self.mouth.set_type(MouthType.LINE)
```

- [ ] **Step 8: Create expressions __init__.py**

```python
from lavi.faces.expressions.happy import HappyFace
from lavi.faces.expressions.laugh import LaughFace
from lavi.faces.expressions.wink import WinkFace
from lavi.faces.expressions.love import LoveFace
from lavi.faces.expressions.sad import SadFace
from lavi.faces.expressions.surprised import SurprisedFace
from lavi.faces.expressions.sleepy import SleepyFace

EXPRESSIONS = {
    "happy": HappyFace,
    "laugh": LaughFace,
    "wink": WinkFace,
    "love": LoveFace,
    "sad": SadFace,
    "surprised": SurprisedFace,
    "sleepy": SleepyFace,
}

def create_face(name, config=None):
    cls = EXPRESSIONS.get(name)
    if cls:
        face = cls(config)
        face.setup()
        return face
    return None
```

- [ ] **Step 9: Test imports**

```bash
python3 -c "from lavi.faces.expressions import create_face; f = create_face('happy'); print(f.name)"
```

Expected: `happy`

- [ ] **Step 10: Commit**

```bash
git add lavi/faces/expressions/
git commit -m "feat: add all face expressions (happy, laugh, wink, love, sad, surprised, sleepy)"
```

---

### Task 6: State Machine

**Files:**
- Create: `lavi/engine/state_machine.py`

- [ ] **Step 1: Create StateMachine class**

```python
import time
import random

class StateMachine:
    def __init__(self, expression_names, config=None):
        config = config or {}
        anim_config = config.get("animation", {})

        self.expression_names = expression_names
        self.current_index = 0
        self.current_name = expression_names[0]
        self.next_name = None

        self.expression_duration = anim_config.get("expression_duration", 3.5)
        self.blink_interval_min = anim_config.get("blink_interval_min", 3)
        self.blink_interval_max = anim_config.get("blink_interval_max", 5)

        self.last_change = time.time()
        self.next_blink = time.time() + random.uniform(self.blink_interval_min, self.blink_interval_max)
        self.is_blinking = False
        self.blink_start = 0
        self.blink_duration = 0.15

    def update(self):
        now = time.time()

        if self.is_blinking:
            if now - self.blink_start >= self.blink_duration:
                self.is_blinking = False
                self.next_blink = now + random.uniform(self.blink_interval_min, self.blink_interval_max)
            return "blink_end"

        if now - self.last_change >= self.expression_duration:
            self.current_index = (self.current_index + 1) % len(self.expression_names)
            self.current_name = self.expression_names[self.current_index]
            self.last_change = now
            return "expression_change"

        if now >= self.next_blink:
            self.is_blinking = True
            self.blink_start = now
            return "blink_start"

        return None

    def get_current(self):
        return self.current_name

    def get_next(self):
        idx = (self.current_index + 1) % len(self.expression_names)
        return self.expression_names[idx]
```

- [ ] **Step 2: Test StateMachine**

```bash
python3 -c "
from lavi.engine.state_machine import StateMachine
sm = StateMachine(['happy', 'laugh', 'wink'])
print(f'Current: {sm.get_current()}')
print(f'Next: {sm.get_next()}')
print('StateMachine OK')
"
```

Expected: `Current: happy`, `Next: laugh`, `StateMachine OK`

- [ ] **Step 3: Commit**

```bash
git add lavi/engine/state_machine.py
git commit -m "feat: add StateMachine for expression cycling and blink timing"
```

---

### Task 7: Animator

**Files:**
- Create: `lavi/engine/animator.py`

- [ ] **Step 1: Create Animator class**

```python
class Animator:
    def __init__(self, config=None):
        config = config or {}
        anim_config = config.get("animation", {})
        self.transition_speed = anim_config.get("transition_speed", 0.4)
        self.transition_progress = 1.0
        self.is_transitioning = False
        self.from_alpha = 0
        self.to_alpha = 255

    def start_transition(self, from_alpha=0, to_alpha=255):
        self.transition_progress = 0.0
        self.is_transitioning = True
        self.from_alpha = from_alpha
        self.to_alpha = to_alpha

    def update(self, dt):
        if not self.is_transitioning:
            return

        self.transition_progress += dt / self.transition_speed

        if self.transition_progress >= 1.0:
            self.transition_progress = 1.0
            self.is_transitioning = False

    def get_alpha(self):
        if not self.is_transitioning:
            return self.to_alpha

        t = self.transition_progress
        return int(self.from_alpha + (self.to_alpha - self.from_alpha) * t)

    def is_done(self):
        return not self.is_transitioning
```

- [ ] **Step 2: Test Animator**

```bash
python3 -c "
from lavi.engine.animator import Animator
a = Animator()
a.start_transition(0, 255)
a.update(0.2)
print(f'Alpha: {a.get_alpha()}, Done: {a.is_done()}')
print('Animator OK')
"
```

Expected: `Alpha: 127, Done: False` (approx), `Animator OK`

- [ ] **Step 3: Commit**

```bash
git add lavi/engine/animator.py
git commit -m "feat: add Animator for smooth alpha transitions"
```

---

### Task 8: Renderer

**Files:**
- Create: `lavi/renderer.py`

- [ ] **Step 1: Create Renderer class**

```python
import pygame

class Renderer:
    def __init__(self, config=None):
        config = config or {}
        display_config = config.get("display", {})

        self.bg_color = pygame.Color(display_config.get("bg_color", "#000000"))
        self.fullscreen = display_config.get("fullscreen", True)

        pygame.init()
        info = pygame.display.Info()
        self.width = info.current_w
        self.height = info.current_h

        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((800, 600))

        pygame.display.set_caption("Lavi")
        self.clock = pygame.time.Clock()
        self.running = True

    def clear(self):
        self.screen.fill(self.bg_color)

    def draw_face(self, face, alpha):
        face.set_alpha(alpha)
        face_rect = self._get_face_rect()
        face.draw(self.screen, face_rect)

    def _get_face_rect(self):
        w = self.screen.get_width()
        h = self.screen.get_height()
        size = min(w, h) * 0.6
        x = (w - size) / 2
        y = (h - size) / 2
        return (x, y, size, size)

    def update(self):
        pygame.display.flip()

    def tick(self, fps=30):
        return self.clock.tick(fps) / 1000.0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def quit(self):
        pygame.quit()
```

- [ ] **Step 2: Test Renderer init**

```bash
python3 -c "
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
from lavi.renderer import Renderer
r = Renderer({'display': {'fullscreen': False}})
print(f'Screen: {r.width}x{r.height}')
r.quit()
print('Renderer OK')
"
```

Expected: `Screen: ...x...`, `Renderer OK`

- [ ] **Step 3: Commit**

```bash
git add lavi/renderer.py
git commit -m "feat: add Renderer with Pygame fullscreen support"
```

---

### Task 9: Main Entry Point

**Files:**
- Create: `lavi/main.py`

- [ ] **Step 1: Create main.py**

```python
import sys
import json
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lavi.renderer import Renderer
from lavi.engine.state_machine import StateMachine
from lavi.engine.animator import Animator
from lavi.faces.expressions import create_face

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}

def main():
    config = load_config()
    expression_names = config.get("expressions", ["happy", "laugh", "wink", "love", "sad", "surprised", "sleepy"])

    renderer = Renderer(config)
    state_machine = StateMachine(expression_names, config)
    animator = Animator(config)

    faces = {}
    for name in expression_names:
        face = create_face(name, config)
        if face:
            faces[name] = face

    current_face = faces[state_machine.get_current()]
    next_face = None
    animator.start_transition(0, 255)

    while renderer.running:
        dt = renderer.handle_events() or renderer.tick(30)

        event = state_machine.update()

        if event == "expression_change":
            next_name = state_machine.get_current()
            next_face = faces.get(next_name)
            animator.start_transition(255, 0)

        if event == "blink_start":
            pass

        if event == "blink_end":
            pass

        animator.update(dt)

        if not animator.is_done():
            alpha = animator.get_alpha()
            if next_face and alpha < 128:
                current_face = next_face
                next_face = None
                animator.start_transition(0, 255)
        else:
            alpha = 255

        renderer.clear()
        renderer.draw_face(current_face, alpha)
        renderer.update()

    renderer.quit()

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test main.py import**

```bash
python3 -c "
import sys, os
sys.path.insert(0, '/Users/alvarocastillo/dev/agents_try')
from lavi.main import load_config
config = load_config()
print(f'Config loaded: {len(config)} keys')
print('Main OK')
"
```

Expected: `Config loaded: 4 keys`, `Main OK`

- [ ] **Step 3: Commit**

```bash
git add lavi/main.py
git commit -m "feat: add main entry point with state machine integration"
```

---

### Task 10: Final Integration Test

**Files:**
- Modify: `lavi/main.py` (if needed)

- [ ] **Step 1: Run full test (headless)**

```bash
cd /Users/alvarocastillo/dev/agents_try
SDL_VIDEODRIVER=dummy python3 -c "
import sys, os
sys.path.insert(0, '.')
from lavi.main import load_config
from lavi.renderer import Renderer
from lavi.engine.state_machine import StateMachine
from lavi.engine.animator import Animator
from lavi.faces.expressions import create_face

config = load_config()
r = Renderer({'display': {'fullscreen': False}})
sm = StateMachine(config['expressions'], config)
an = Animator(config)

faces = {name: create_face(name, config) for name in config['expressions']}
face = faces[sm.get_current()]
face.set_alpha(255)

for i in range(10):
    r.clear()
    r.draw_face(face, 255)
    r.update()
    r.tick(30)

r.quit()
print('Integration test OK')
"
```

Expected: `Integration test OK`

- [ ] **Step 2: Final commit**

```bash
git add .
git commit -m "feat: milestone 1 complete - animated face kiosk"
```

---

## Summary

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Project setup + git | `feat: initial project structure with config` |
| 2 | Eye part | `feat: add Eye part` |
| 3 | Mouth part | `feat: add Mouth part` |
| 4 | Base Face class | `feat: add Face base class` |
| 5 | All expressions | `feat: add all face expressions` |
| 6 | State machine | `feat: add StateMachine` |
| 7 | Animator | `feat: add Animator` |
| 8 | Renderer | `feat: add Renderer` |
| 9 | Main entry point | `feat: add main entry point` |
| 10 | Integration test | `feat: milestone 1 complete` |
