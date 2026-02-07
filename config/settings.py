"""
Configuración general del Gestor Financiero Inteligente
"""
import os
from pathlib import Path
from datetime import datetime

# Rutas del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Crear directorios si no existen
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configuración de la base de datos
DATABASE_PATH = DATA_DIR / "finanzas.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Categorías predefinidas
CATEGORIAS_GASTOS = [
    "Alimentación",
    "Transporte",
    "Vivienda",
    "Servicios",
    "Salud",
    "Entretenimiento",
    "Educación",
    "Ropa",
    "Tecnología",
    "Otros"
]

CATEGORIAS_INGRESOS = [
    "Salario",
    "Freelance",
    "Inversiones",
    "Negocios",
    "Bonos",
    "Otros"
]

METODOS_PAGO = [
    "Efectivo",
    "Tarjeta de Débito",
    "Tarjeta de Crédito",
    "Transferencia",
    "PayPal",
    "Yape/Plin",
    "Otros"
]

# Configuración de modelos de IA
MODEL_CONFIG = {
    "prediccion_gastos": {
        "model_path": MODELS_DIR / "prediccion_gastos.pkl",
        "lookback_days": 90,
        "forecast_days": 30
    },
    "clasificador_categorias": {
        "model_path": MODELS_DIR / "clasificador_categorias.pkl",
        "min_accuracy": 0.75
    },
    "detector_anomalias": {
        "model_path": MODELS_DIR / "detector_anomalias.pkl",
        "threshold": 2.5
    }
}

# Configuración de la API
API_CONFIG = {
    "host": "127.0.0.1",
    "port": 8000,
    "reload": True
}

# Configuración del Dashboard
DASHBOARD_CONFIG = {
    "port": 8501,
    "theme": "dark"
}

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_DIR / f"gestor_{datetime.now().strftime('%Y%m%d')}.log"

print("✅ Configuración cargada correctamente")