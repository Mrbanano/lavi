import time


class PresenceState:
    ASLEEP = "asleep"
    AWAKE = "awake"


class PresenceTracker:
    """Decide si hay alguien delante, aguantando el parpadeo del detector.

    Haar pierde la cara en frames sueltos aunque la persona siga ahí, y de vez
    en cuando saca un falso positivo. Por eso ninguna de las dos transiciones es
    inmediata: para despertar hace falta ver la cara sostenida, y para dormirse
    hace falta no verla durante bastante rato.

    El debounce va por tiempo y no por frames a propósito: el loop de render va
    a 30 FPS y la detección a 8, así que contar frames contaría el mismo
    resultado cuatro veces.
    """

    def __init__(self, config=None):
        config = config or {}
        presence_config = config.get("presence", {})

        self.wake_delay = presence_config.get("wake_delay", 0.4)
        self.sleep_delay = presence_config.get("sleep_delay", 8.0)
        # Cuánto antes de dormirse avisa de que le está entrando el sueño. Es lo
        # que da tiempo al bostezo: dormirse de golpe parecía que le bajaban el
        # brillo, no que se durmiera.
        self.drowsy_lead = presence_config.get("drowsy_lead", 2.5)

        self.state = PresenceState.ASLEEP
        self._first_seen = None
        self._last_seen = time.time()
        self._drowsy_sent = False

    def update(self, has_face):
        now = time.time()

        if has_face:
            if self._first_seen is None:
                self._first_seen = now
            self._last_seen = now
            self._drowsy_sent = False
        else:
            self._first_seen = None

        if self.state == PresenceState.ASLEEP:
            if self._first_seen is not None and now - self._first_seen >= self.wake_delay:
                self.state = PresenceState.AWAKE
                self._drowsy_sent = False
                return "wake"
        else:
            alone_for = now - self._last_seen
            if alone_for >= self.sleep_delay:
                self.state = PresenceState.ASLEEP
                self._first_seen = None
                return "sleep"
            # Una sola vez por siesta: si se repitiera, bostezaría en bucle.
            if not self._drowsy_sent and alone_for >= self.sleep_delay - self.drowsy_lead:
                self._drowsy_sent = True
                return "drowsy"

        return None

    def is_awake(self):
        return self.state == PresenceState.AWAKE

    def seconds_since_seen(self):
        return time.time() - self._last_seen
