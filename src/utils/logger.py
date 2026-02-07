"""
Sistema de logging para el gestor financiero
"""
import logging
import sys
from pathlib import Path
from config.settings import LOG_LEVEL, LOG_FORMAT, LOG_FILE, LOGS_DIR

def setup_logger(name: str) -> logging.Logger:
    """
    Configura y retorna un logger personalizado
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # Evitar duplicación de handlers
    if logger.handlers:
        return logger
    
    # Formato
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Handler para archivo
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Añadir handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Logger principal
logger = setup_logger("GestorFinanciero")