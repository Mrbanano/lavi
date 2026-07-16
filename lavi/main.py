import sys
import json
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lavi.renderer import Renderer
from lavi.engine.mood import Mood
from lavi.engine.idle import IdleLife
from lavi.engine.presence import PresenceTracker
from lavi.engine.gaze import GazeTracker
from lavi.faces.face import Face
from lavi.faces.zzz import SleepZs
from lavi.faces.expressions import BASELINE, SLEEP
from lavi.vision.service import VisionService
from lavi.vision.preview import CameraPreview


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            return json.load(f)
    return {}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Lavi - kiosko de cara animada")
    parser.add_argument("--windowed", action="store_true",
                        help="ventana en vez de pantalla completa (para desarrollar en la mac)")
    parser.add_argument("--preview", action="store_true",
                        help="arranca con el preview de cámara abierto")
    parser.add_argument("--no-camera", action="store_true",
                        help="sin cámara ni detección: se queda despierta y tranquila")
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

    renderer = Renderer(config)
    face = Face(config)
    zzz = SleepZs(config)
    mood = Mood(config)
    idle = IdleLife(config)
    presence = PresenceTracker(config)
    gaze = GazeTracker(config)
    preview = CameraPreview(config)

    vision = VisionService(config)
    vision_ok = vision.start()
    if not vision_ok:
        # Sin cámara no hay a quién esperar, así que se queda despierta y
        # tranquila. Sigue viva: respira, parpadea y mira alrededor.
        print("[lavi] visión no disponible: %s" % vision.error)
        print("[lavi] sigo sin detección, despierta y tranquila")
    else:
        # Con cámara arranca dormida, esperando a que llegue alguien.
        mood.set_baseline(SLEEP)

    while renderer.running:
        for action in renderer.handle_events():
            if action == "toggle_preview":
                preview.toggle()

        dt = renderer.tick(30)
        box = None

        if vision_ok:
            box, frame_size = vision.primary_face()
            gaze.update(box, frame_size, dt)

            event = presence.update(vision.has_face())
            if event == "wake":
                mood.set_baseline(BASELINE)
                mood.push("sorpresa")
            elif event == "sleep":
                mood.set_baseline(SLEEP)

            gesture = vision.take_gesture()
            if gesture == "saludo":
                mood.push("emocionada")
            elif gesture == "amor_y_paz":
                mood.push("enamorada")
            elif gesture == "peineta":
                mood.push("enfadada")

        idle.update(dt)
        mood.update(dt)
        zzz.update(dt, mood.is_sleeping())

        # Con alguien delante, Lavi le mira. Sin nadie, la mirada deriva sola:
        # quedarse clavada al frente es lo que hace que algo parezca apagado.
        gaze_x, gaze_y = gaze.get()
        if box is None:
            drift_x, drift_y = idle.get_drift()
            gaze_x += drift_x
            gaze_y += drift_y

        face.set_features(mood.get())
        face.set_blink(idle.get_blink())
        face.set_gaze(gaze_x, gaze_y)

        renderer.clear()
        # La escala la lleva la respiración. Antes la ocupaba el pop, que era un
        # parche para tapar el cambiazo de cara; ya no hay cambiazo que tapar.
        breath = idle.breath_scale()
        renderer.draw_face(face, 255, breath, (0, 0))
        zzz.draw(renderer.screen, renderer.face_rect(breath))
        preview.draw(renderer.screen, vision)
        renderer.update()

    vision.stop()
    renderer.quit()


if __name__ == "__main__":
    main()
