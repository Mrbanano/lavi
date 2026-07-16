"""Código de terceros, copiado tal cual. No editar aquí.

mp_palmdet.py y mp_handpose.py vienen de OpenCV Zoo (Apache 2.0):
https://github.com/opencv/opencv_zoo/tree/main/models

Van versionados en vez de instalados porque el zoo no se publica en PyPI. Son
los modelos de MediaPipe exportados a ONNX: corren sobre cv2.dnn, así que no
hace falta el paquete `mediapipe`, que no tiene wheel para Linux ARM y por tanto
no instalaría en la Pi.

Decodificar las anclas SSD de la palma a mano sería pedir bugs: las 2000 líneas
de mp_palmdet.py son casi todas la tabla de anclas.
"""
