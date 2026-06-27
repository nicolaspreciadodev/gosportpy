"""
Conftest raíz del proyecto GoSport.

Proporciona fixtures globales reutilizables para las pruebas unitarias y de integración.
"""
import os
import sys
import pytest
from django.test import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GoSport.settings')

import django
django.setup()

# Mock de transaction.atomic global para evitar que se contacte a la base de datos
# durante las pruebas unitarias de los servicios.
import django.db.transaction

class MockAtomicContextManager:
    def __call__(self, func):
        return func
    def __enter__(self):
        pass
    def __exit__(self, exc_type, exc_value, traceback):
        pass

def mock_atomic(*args, **kwargs):
    if len(args) == 1 and callable(args[0]):
        return args[0]
    return MockAtomicContextManager()

# Solo aplicamos el mock de base de datos si NO estamos corriendo pruebas de integración
if 'integration' not in ' '.join(sys.argv):
    django.db.transaction.atomic = mock_atomic


# ==========================================
# Fixtures Globales de Integración
# ==========================================

@pytest.fixture(scope="session")
def app_cliente():
    """
    Cliente de pruebas de Django instanciado una vez por sesión.
    Útil para interactuar con las vistas mediante HTTP.
    """
    return Client()
