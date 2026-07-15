import platform


class Platform:
    MAC = "mac"
    RASPBERRY = "raspberry"
    LINUX = "linux"
    UNKNOWN = "unknown"


def detect_platform():
    system = platform.system()
    if system == "Darwin":
        return Platform.MAC
    if system == "Linux":
        return Platform.RASPBERRY if _is_raspberry_pi() else Platform.LINUX
    return Platform.UNKNOWN


def _is_raspberry_pi():
    # El device-tree es la fuente fiable: dice "Raspberry Pi 3 Model B Rev 1.2".
    # Viene terminado en NUL, por eso se lee en binario.
    try:
        with open("/proc/device-tree/model", "rb") as f:
            if "raspberry pi" in f.read().decode("utf-8", "ignore").lower():
                return True
    except OSError:
        pass

    # Algunas imágenes de 64 bits no exponen el device-tree; ahí queda el SoC.
    try:
        with open("/proc/cpuinfo", "r") as f:
            info = f.read().lower()
        return "raspberry pi" in info or "bcm27" in info or "bcm28" in info
    except OSError:
        return False


def describe_platform():
    name = detect_platform()
    if name == Platform.RASPBERRY:
        try:
            with open("/proc/device-tree/model", "rb") as f:
                return f.read().decode("utf-8", "ignore").strip("\x00 ")
        except OSError:
            return "Raspberry Pi"
    if name == Platform.MAC:
        return "macOS %s (%s)" % (platform.mac_ver()[0], platform.machine())
    return "%s (%s)" % (platform.system(), platform.machine())
