# backend/services/__init__.py
"""
Servicios del sistema de gestión documental
"""

try:
    from .word_generator import generate_acuerdo_seguridad_word, generate_autorizacion_datos_word
    WORD_AVAILABLE = True
except ImportError:
    WORD_AVAILABLE = False
    print("python-docx no disponible. Usando generación de texto plano.")

__all__ = ['WORD_AVAILABLE']

if WORD_AVAILABLE:
    __all__.extend(['generate_acuerdo_seguridad_word', 'generate_autorizacion_datos_word'])