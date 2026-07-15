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
