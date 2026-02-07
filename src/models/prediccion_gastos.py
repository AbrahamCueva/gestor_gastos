"""
Modelos de predicción de gastos usando Machine Learning
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost no disponible, usando modelos alternativos")

from src.utils.database import db_manager
from src.utils.logger import logger
from config.settings import MODELS_DIR

class PrediccionGastos:
    """Modelo de predicción de gastos futuros"""
    
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.feature_columns = []
        self.model_path = MODELS_DIR / "prediccion_gastos.pkl"
        self.is_trained = False
    
    def preparar_datos(self):
        """Prepara los datos para el entrenamiento"""
        transacciones = db_manager.obtener_todas_transacciones()
        
        if not transacciones or len(transacciones) < 50:
            logger.warning("No hay suficientes datos para entrenar (mínimo 50)")
            return None, None
        
        # Convertir a DataFrame
        datos = []
        for t in transacciones:
            if t.tipo == 'gasto':  # Solo gastos
                datos.append({
                    'fecha': t.fecha,
                    'monto': t.monto,
                    'categoria': t.categoria,
                    'subcategoria': t.subcategoria or 'Sin subcategoría',
                    'metodo_pago': t.metodo_pago,
                    'es_recurrente': 1 if t.es_recurrente else 0
                })
        
        if not datos:
            return None, None
        
        df = pd.DataFrame(datos)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Features temporales
        df['dia_semana'] = df['fecha'].dt.dayofweek
        df['dia_mes'] = df['fecha'].dt.day
        df['mes'] = df['fecha'].dt.month
        df['trimestre'] = df['fecha'].dt.quarter
        df['es_fin_semana'] = (df['dia_semana'] >= 5).astype(int)
        df['es_inicio_mes'] = (df['dia_mes'] <= 5).astype(int)
        df['es_fin_mes'] = (df['dia_mes'] >= 25).astype(int)
        
        # Codificar variables categóricas
        categorical_features = ['categoria', 'subcategoria', 'metodo_pago']
        
        for col in categorical_features:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col])
            else:
                df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col])
        
        # Features finales
        self.feature_columns = [
            'dia_semana', 'dia_mes', 'mes', 'trimestre',
            'es_fin_semana', 'es_inicio_mes', 'es_fin_mes', 'es_recurrente',
            'categoria_encoded', 'subcategoria_encoded', 'metodo_pago_encoded'
        ]
        
        X = df[self.feature_columns]
        y = df['monto']
        
        logger.info(f"✅ Datos preparados: {len(X)} muestras")
        return X, y
    
    def entrenar(self):
        """Entrena el modelo de predicción"""
        logger.info("🤖 Iniciando entrenamiento del modelo...")
        
        X, y = self.preparar_datos()
        
        if X is None or len(X) < 50:
            logger.error("❌ No hay suficientes datos para entrenar")
            return False
        
        # Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Seleccionar modelo
        if XGBOOST_AVAILABLE and len(X_train) > 100:
            logger.info("📊 Usando XGBoost...")
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        else:
            logger.info("📊 Usando Random Forest...")
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        
        # Entrenar
        self.model.fit(X_train, y_train)
        
        # Evaluar
        y_pred = self.model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        logger.info(f"✅ Modelo entrenado - MAE: ${mae:.2f}, RMSE: ${rmse:.2f}, R²: {r2:.3f}")
        
        # Guardar modelo
        self.guardar_modelo()
        self.is_trained = True
        
        return {
            'mae': round(mae, 2),
            'rmse': round(rmse, 2),
            'r2': round(r2, 3),
            'muestras_entrenamiento': len(X_train),
            'muestras_prueba': len(X_test)
        }
    
    def predecir_gasto(self, categoria, subcategoria=None, metodo_pago="Efectivo", 
                      fecha=None, es_recurrente=False):
        """
        Predice el monto de un gasto
        
        Args:
            categoria: Categoría del gasto
            subcategoria: Subcategoría (opcional)
            metodo_pago: Método de pago
            fecha: Fecha del gasto (default: hoy)
            es_recurrente: Si es gasto recurrente
            
        Returns:
            Monto predicho
        """
        if not self.is_trained:
            if not self.cargar_modelo():
                logger.warning("Modelo no entrenado, entrenando ahora...")
                self.entrenar()
        
        if fecha is None:
            fecha = datetime.now()
        
        # Crear features
        features = {
            'dia_semana': fecha.weekday(),
            'dia_mes': fecha.day,
            'mes': fecha.month,
            'trimestre': (fecha.month - 1) // 3 + 1,
            'es_fin_semana': 1 if fecha.weekday() >= 5 else 0,
            'es_inicio_mes': 1 if fecha.day <= 5 else 0,
            'es_fin_mes': 1 if fecha.day >= 25 else 0,
            'es_recurrente': 1 if es_recurrente else 0
        }
        
        # Codificar categóricas
        try:
            features['categoria_encoded'] = self.label_encoders['categoria'].transform([categoria])[0]
            features['subcategoria_encoded'] = self.label_encoders['subcategoria'].transform(
                [subcategoria or 'Sin subcategoría']
            )[0]
            features['metodo_pago_encoded'] = self.label_encoders['metodo_pago'].transform([metodo_pago])[0]
        except ValueError as e:
            logger.error(f"Error al codificar: {e}")
            return None
        
        # Predecir
        X_pred = pd.DataFrame([features])[self.feature_columns]
        prediccion = self.model.predict(X_pred)[0]
        
        return max(0, round(prediccion, 2))  # No permitir negativos
    
    def predecir_gastos_mes(self, mes=None, año=None):
        """
        Predice gastos totales para un mes específico
        
        Args:
            mes: Mes (1-12), default: próximo mes
            año: Año, default: año actual
            
        Returns:
            Diccionario con predicciones por categoría
        """
        if mes is None:
            hoy = datetime.now()
            mes = hoy.month + 1 if hoy.month < 12 else 1
            año = hoy.year if hoy.month < 12 else hoy.year + 1
        
        if año is None:
            año = datetime.now().year
        
        # Obtener categorías históricas
        transacciones = db_manager.obtener_todas_transacciones()
        categorias = set(t.categoria for t in transacciones if t.tipo == 'gasto')
        
        predicciones = {}
        total = 0
        
        for categoria in categorias:
            # Predecir para el día 15 del mes (representativo)
            fecha = datetime(año, mes, 15)
            prediccion = self.predecir_gasto(categoria, fecha=fecha)
            
            if prediccion:
                # Estimar total mensual (aproximado)
                prediccion_mensual = prediccion * 20  # Asumiendo ~20 transacciones/mes
                predicciones[categoria] = round(prediccion_mensual, 2)
                total += prediccion_mensual
        
        predicciones['TOTAL'] = round(total, 2)
        
        return predicciones
    
    def guardar_modelo(self):
        """Guarda el modelo entrenado"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'label_encoders': self.label_encoders,
                    'feature_columns': self.feature_columns
                }, f)
            logger.info(f"✅ Modelo guardado en {self.model_path}")
        except Exception as e:
            logger.error(f"❌ Error al guardar modelo: {e}")
    
    def cargar_modelo(self):
        """Carga el modelo entrenado"""
        try:
            if not self.model_path.exists():
                return False
            
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.label_encoders = data['label_encoders']
                self.feature_columns = data['feature_columns']
            
            self.is_trained = True
            logger.info("✅ Modelo cargado correctamente")
            return True
        except Exception as e:
            logger.error(f"❌ Error al cargar modelo: {e}")
            return False

# Instancia global
predictor = PrediccionGastos()