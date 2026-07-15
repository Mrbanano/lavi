from lavi.faces.base import Face
from lavi.faces.parts.eye import EyeType
from lavi.faces.parts.mouth import MouthType

class LoveFace(Face):
    def __init__(self, config=None):
        super().__init__(config)
        self.name = "love"

    def setup(self):
        self.left_eye.set_type(EyeType.HEART)
        self.right_eye.set_type(EyeType.HEART)
        self.mouth.set_type(MouthType.LINE)
