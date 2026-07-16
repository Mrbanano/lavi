import sys
import json
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lavi.renderer import Renderer
from lavi.engine.state_machine import StateMachine
from lavi.engine.animator import Animator
from lavi.engine.presence import PresenceTracker
from lavi.engine.gaze import GazeTracker
from lavi.faces.expressions import create_face
from lavi.vision.service import VisionService
from lavi.vision.preview import CameraPreview

DEFAULT_EXPRESSIONS = ["happy", "laugh", "wink", "love", "sad", "surprised", "sleepy"]
WAKE_EXPRESSION = "surprised"
SLEEP_EXPRESSION = "sleepy"


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Lavi - kiosko de cara animada")
    parser.add_argument("--windowed", action="store_true",
                        help="ventana en vez de pantalla completa (para desarrollar en la mac)")
    parser.add_argument("--preview", action="store_true",
                        help="arranca con el preview de cámara abierto")
    parser.add_argument("--no-camera", action="store_true",
                        help="sin cámara ni detección: solo cicla expresiones")
    return parser.parse_args(argv)


def apply_args(config, args):
    if args.windowed:
        config.setdefault("display", {})["fullscreen"] = False
    if args.preview:
        config.setdefault("preview", {})["start_expanded"] = True
    if args.no_camera:
        config.setdefault("camera", {})["enabled"] = False
    return config


def main(argv=None):
    args = parse_args(argv)
    config = apply_args(load_config(), args)
    expression_names = config.get("expressions", DEFAULT_EXPRESSIONS)

    # sleepy queda fuera del ciclo: es la cara de "no hay nadie". Si además
    # saliera con alguien delante, no habría forma de distinguir los dos estados.
    cycle_names = [name for name in expression_names if name != SLEEP_EXPRESSION] or expression_names

    renderer = Renderer(config)
    state_machine = StateMachine(cycle_names, config)
    animator = Animator(config)
    presence = PresenceTracker(config)
    gaze = GazeTracker(config)
    preview = CameraPreview(config)

    vision = VisionService(config)
    vision_ok = vision.start()
    if not vision_ok:
        # Sin cámara Lavi se comporta como en el milestone 1: cara siempre
        # despierta ciclando. Un kiosko no se queda en negro por esto.
        print("[lavi] visión no disponible: %s" % vision.error)
        print("[lavi] sigo sin detección, ciclando expresiones")

    faces = {}
    for name in expression_names:
        face = create_face(name, config)
        if face:
            faces[name] = face

    # Arranca dormida y espera a que alguien llegue. Sin cámara no hay a quién
    # esperar, así que cicla desde el principio.
    sleeping = vision_ok and SLEEP_EXPRESSION in faces
    if sleeping:
        state_machine.pause()
        current_face = faces[SLEEP_EXPRESSION]
    else:
        current_face = faces[state_machine.get_current()]
    pending_face = None

    while renderer.running:
        for action in renderer.handle_events():
            if action == "toggle_preview":
                preview.toggle()

        dt = renderer.tick(30)

        if vision_ok:
            # Sin cara detectada el objetivo es (0, 0): la mirada vuelve sola al
            # frente en vez de quedarse clavada donde estaba la persona.
            box, frame_size = vision.primary_face()
            gaze.update(box, frame_size, dt)

            presence_event = presence.update(vision.has_face())
            if presence_event == "wake":
                state_machine.resume()
                state_machine.set_current(WAKE_EXPRESSION)
                pending_face = faces.get(WAKE_EXPRESSION) or faces.get(state_machine.get_current())
                animator.start_transition("pop")
            elif presence_event == "sleep":
                state_machine.pause()
                pending_face = faces.get(SLEEP_EXPRESSION)
                animator.start_transition("pop")

        if state_machine.update() == "expression_change":
            pending_face = faces.get(state_machine.get_current())
            animator.start_transition("pop")

        animator.update(dt)

        # El animator decide cuándo cambiar la cara: en el pop es el punto más
        # pequeño y transparente, que es lo que disimula el cambio.
        if pending_face is not None and animator.should_swap():
            current_face = pending_face
            pending_face = None

        current_face.set_blink(state_machine.get_blink_progress())
        current_face.set_gaze(*gaze.get())

        renderer.clear()
        renderer.draw_face(current_face, animator.get_alpha(), animator.get_scale(), animator.get_offset())
        preview.draw(renderer.screen, vision)
        renderer.update()

    vision.stop()
    renderer.quit()


if __name__ == "__main__":
    main()
