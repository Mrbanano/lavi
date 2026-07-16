import sys
import json
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lavi.renderer import Renderer
from lavi.engine.mood import Mood
from lavi.engine.idle import IdleLife, IdleMoods
from lavi.engine.body import Body
from lavi.engine.presence import PresenceTracker
from lavi.engine.gaze import GazeTracker
from lavi.faces.face import Face
from lavi.faces.particles import FloatingGlyphs
from lavi.faces.expressions import BASELINE, SLEEP
from lavi.vision.service import VisionService
from lavi.vision.preview import CameraPreview
from lavi.profiler import Profiler


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
    parser.add_argument("--profile", action="store_true",
                        help="guarda logs de rendimiento (FPS, CPU, RAM, visión) a un CSV")
    return parser.parse_args(argv)


def apply_args(config, args):
    if args.windowed:
        config.setdefault("display", {})["fullscreen"] = False
    if args.preview:
        config.setdefault("preview", {})["start_expanded"] = True
    if args.no_camera:
        config.setdefault("camera", {})["enabled"] = False
    config["_profile"] = args.profile
    return config


def main(argv=None):
    args = parse_args(argv)
    config = apply_args(load_config(), args)

    renderer = Renderer(config)
    face = Face(config)
    # Las Z salen de la sien; las notas, de más abajo y hacia los dos lados.
    # Entre las Z se cuela un ♥ o un ♪ de vez en cuando: está soñando con algo.
    # Una Z dice que duerme; una Z que de pronto es un corazón dice que tiene
    # interior. Sale gratis, porque FloatingGlyphs ya elige entre varios glifos.
    zzz = FloatingGlyphs(config.get("zzz", {}).get("glyphs", "ZZZZZZZZ♥♪"),
                         (0.72, 0.30), config.get("zzz", {}))
    notes = FloatingGlyphs("♪♫♩♬", (0.50, 0.55), config.get("notes", {}))
    mood = Mood(config)
    idle = IdleLife(config)
    idle_moods = IdleMoods(config)
    body = Body(config)
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

    profiler = Profiler() if config.get("_profile") else None

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
                was_asleep = mood.is_sleeping()
                mood.set_baseline(BASELINE)
                mood.push("sorpresa")
                # Solo se despereza si venía de dormir. Si estaba despierta y la
                # detección la perdió un momento, desperezarse sería absurdo.
                if was_asleep:
                    body.stretch()
            elif event == "drowsy":
                # Un bostezo dura lo que dura: con el decaimiento normal se
                # quedaría bostezando como si fuera un estado de ánimo.
                mood.push("bostezo", decay=2.2)
            elif event == "sleep":
                mood.set_baseline(SLEEP)

            gesture = vision.take_gesture()
            if gesture == "saludo":
                mood.push("emocionada")
            elif gesture == "amor_y_paz":
                mood.push("enamorada")
            elif gesture == "peineta":
                mood.push("enfadada")

        # De puro aburrimiento: empanarse si está sola, suspirar si tiene a
        # alguien delante que no le hace ni caso.
        bored = idle_moods.update(dt, mood.is_calm(), box is not None)
        if bored == "suspiro":
            mood.push("suspiro", decay=3.0)
            body.sigh()
        elif bored == "empanada":
            mood.push("empanada", intensity=0.85, decay=5.0)

        idle.update(dt)
        mood.update(dt)

        # Baila solo si no está pasando nada: ni dormida, ni con una emoción
        # encima. En cuanto pasa algo, deja de bailar.
        body.update(dt, mood.is_calm(), mood.is_sleeping())
        zzz.update(dt, mood.is_sleeping())
        notes.update(dt, body.is_dancing())

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
        breath = idle.breath_scale() + body.get_scale()
        offset = body.get_offset()
        renderer.draw_face(face, 255, breath, offset)

        # Las Z y las notas se mueven con la cara: si se quedaran quietas
        # mientras ella baila, se verían pegadas al fondo.
        rect = renderer.face_rect(breath, offset)
        zzz.draw(renderer.screen, rect)
        notes.draw(renderer.screen, rect)
        preview.draw(renderer.screen, vision)
        if profiler:
            profiler.tick(vision.stats())
        renderer.update()

    vision.stop()
    if profiler:
        print("[lavi] perfil guardado en %s" % profiler.path)
        profiler.stop()
    renderer.quit()


if __name__ == "__main__":
    main()
