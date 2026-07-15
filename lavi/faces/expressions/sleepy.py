from lavi.faces.base import Face
from lavi.faces.parts.eye import EyeType
from lavi.faces.parts.mouth import MouthType

class SleepyFace(Face):
    def __init__(self, config=None):
        super().__init__(config)
        self.name = "sleepy"

    def setup(self):
        self.left_eye.set_type(EyeType.SLEEPY)
        self.right_eye.set_type(EyeType.SLEEPY)
        self.mouth.set_type(MouthType.LINE)
