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
    transitioning = False

    while renderer.running:
        dt = renderer.handle_events() or renderer.tick(30)

        event = state_machine.update()

        if event == "expression_change" and not transitioning:
            next_name = state_machine.get_current()
            next_face = faces.get(next_name)
            animator.start_transition("pop")
            transitioning = True

        if event == "blink_start":
            pass

        if event == "blink_end":
            pass

        animator.update(dt)

        if transitioning and animator.get_scale() < 0.1 and next_face:
            current_face = next_face
            next_face = None

        if transitioning and animator.is_done():
            transitioning = False

        renderer.clear()
        scale = animator.get_scale()
        alpha = animator.get_alpha()
        offset = animator.get_offset()
        renderer.draw_face(current_face, alpha, scale, offset)
        renderer.update()

    renderer.quit()

if __name__ == "__main__":
    main()
