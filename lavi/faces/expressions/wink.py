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
