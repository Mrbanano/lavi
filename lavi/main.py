import sys
import json
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
