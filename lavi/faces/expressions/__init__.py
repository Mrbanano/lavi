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
