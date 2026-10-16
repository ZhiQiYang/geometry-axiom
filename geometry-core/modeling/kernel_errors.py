"""Legacy diagnostic associations for the neutral geometry kernel."""
from .common import ModelError

CLAUSES = {'FACE_FRAME': 'D2', 'FACE_DEGENERATE': 'I1', 'FACE_NONPLANAR': 'I1', 'EXTRUSION_SPAN': 'I26', 'EXTRUSION_RANGE': 'I26', 'BASE_SOLID': 'D7', 'SHELL_DEGENERATE': 'I27', 'SHELL_NONMANIFOLD_EDGE': 'I27', 'SHELL_ORIENTATION': 'I27', 'SHELL_VERTEX_LINK': 'I27', 'SHELL_VERTEX_PINCH': 'I27', 'SHELL_DISCONNECTED': 'I27', 'SHELL_FACE_OVERLAP': 'I27', 'SHELL_SELF_INTERSECTION': 'I27', 'SHELL_EMPTY': 'D21', 'SHELL_ZERO_VOLUME': 'I28', 'SHELL_INWARD': 'I28', 'BOOLEAN_NOT_SOLID': 'I29', 'BOOLEAN_OPERATION': 'D23', 'MISSING_FACE_SOURCE': 'R28', 'SOLID_OPEN_BOUNDARY': 'I28', 'SOLID_SHELL': 'I28', 'SOLID_VOLUME': 'I28', 'CAPACITY': 'I33', 'OPEN_SHELL': 'I28', 'UNICODE': 'D25', 'JSON_TYPE': 'D25', 'DUPLICATE_KEY': 'D25', 'JSON_PARSE': 'D25'}

def translate(error):
    message = error.message
    if error.code == "SHELL_INWARD":
        message = "A composite space shell must face out of its enclosed volume"
    elif error.code == "EXTRUSION_RANGE":
        message = message.replace("the supported range", "the D1 range" if message.startswith("Extrusion thickness") else "the D1 supported range")
    return ModelError(error.status, error.code, CLAUSES.get(error.code, "I1"), message)
