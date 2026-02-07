"""
Detector de anomalías en gastos usando técnicas de ML
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from src.utils.database import db_manager
from src.utils.logger import logger
from config.settings import MODELS_DIR

class DetectorAnomalias:
    """Detecta gastos anómalos o inusuales usando Isolation Forest"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = MODELS_DIR / "detector_anomalias.pkl"
        self.is_trained = False
        self.umbral_contaminacion = 0.1  # 10% de datos considerados anómalos
    
    def preparar_datos(self):
        """Prepara datos para detección de anomalías"""
        transacciones = db_manager.obtener_todas_transacciones()
        
        if not transacciones or len(transacciones) < 30:
            logger.warning("No hay suficientes datos (mínimo 30 transacciones)")
            return None
        
        # Solo gastos
        datos = []
        for t in transacciones:
            if t.tipo == 'gasto':
                datos.append({
                    'monto': t.monto,
                    'categoria': t.categoria,
                    'dia_semana': t.fecha.weekday(),
                    'hora': t.fecha.hour,
                    'dia_mes': t.fecha.day
                })
        
        df = pd.DataFrame(datos)
        
        # Estadísticas por categoría
        categoria_stats = df.groupby('categoria')['monto'].agg(['mean', 'std']).reset_index()
        categoria_stats.columns = ['categoria', 'categoria_mean', 'categoria_std']
        
        df = df.merge(categoria_stats, on='categoria', how='left')
        
        # Features para detección
        df['desviacion_categoria'] = (df['monto'] - df['categoria_mean']) / (df['categoria_std'] + 1e-6)
        df['monto_log'] = np.log1p(df['monto'])
        df['es_fin_semana'] = (df['dia_semana'] >= 5).astype(int)
        df['es_noche'] = ((df['hora'] >= 22) | (df['hora'] <= 6)).astype(int)
        
        # Features finales
        features = df[[
            'monto', 'monto_log', 'desviacion_categoria',
            'dia_semana', 'hora', 'dia_mes', 'es_fin_semana', 'es_noche'
        ]]
        
        return features, df
    
    def entrenar(self):
        """Entrena el modelo de detección de anomalías"""
        logger.info("🔍 Entrenando detector de anomalías...")
        
        features, df_original = self.preparar_datos()
        
        if features is None or len(features) < 30:
            logger.error("❌ Datos insuficientes para entrenar")
            return False
        
        # Escalar features
        X_scaled = self.scaler.fit_transform(features)
        
        # Entrenar Isolation Forest
        self.model = IsolationForest(
            contamination=self.umbral_contaminacion,
            random_state=42,
            n_estimators=100
        )
        
        self.model.fit(X_scaled)
        
        # Detectar anomalías en datos de entrenamiento
        predicciones = self.model.predict(X_scaled)
        anomalias = (predicciones == -1).sum()
        
        logger.info(f"✅ Detector entrenado - {anomalias} anomalías detectadas de {len(features)} transacciones")
        
        # Guardar modelo
        self.guardar_modelo()
        self.is_trained = True
        
        return {
            'total_transacciones': len(features),
            'anomalias_detectadas': int(anomalias),
            'porcentaje_anomalias': round(anomalias / len(features) * 100, 2)
        }
    
    def detectar_anomalia(self, monto, categoria, fecha=None):
        """
        Detecta si un gasto es anómalo
        
        Args:
            monto: Monto del gasto
            categoria: Categoría del gasto
            fecha: Fecha del gasto (default: ahora)
            
        Returns:
            Dict con resultado de detección
        """
        if not self.is_trained:
            if not self.cargar_modelo():
                logger.warning("Modelo no entrenado, entrenando ahora...")
                resultado = self.entrenar()
                if not resultado:
                    return {'es_anomalia': False, 'confianza': 0, 'mensaje': 'Modelo no disponible'}
        
        if fecha is None:
            fecha = datetime.now()
        
        # Calcular estadísticas de la categoría
        transacciones = db_manager.obtener_todas_transacciones()
        gastos_categoria = [
            t.monto for t in transacciones 
            if t.tipo == 'gasto' and t.categoria == categoria
        ]
        
        if not gastos_categoria:
            return {
                'es_anomalia': False,
                'confianza': 0,
                'mensaje': 'No hay histórico de esta categoría'
            }
        
        categoria_mean = np.mean(gastos_categoria)
        categoria_std = np.std(gastos_categoria) if len(gastos_categoria) > 1 else 1
        
        # Crear features
        desviacion_categoria = (monto - categoria_mean) / (categoria_std + 1e-6)
        
        features = pd.DataFrame([{
            'monto': monto,
            'monto_log': np.log1p(monto),
            'desviacion_categoria': desviacion_categoria,
            'dia_semana': fecha.weekday(),
            'hora': fecha.hour,
            'dia_mes': fecha.day,
            'es_fin_semana': 1 if fecha.weekday() >= 5 else 0,
            'es_noche': 1 if (fecha.hour >= 22 or fecha.hour <= 6) else 0
        }])
        
        # Escalar
        X_scaled = self.scaler.transform(features)
        
        # Predecir
        prediccion = self.model.predict(X_scaled)[0]
        score = self.model.score_samples(X_scaled)[0]
        
        es_anomalia = (prediccion == -1)
        
        # Calcular nivel de confianza (convertir score a porcentaje)
        confianza = min(100, max(0, abs(score) * 50))
        
        # Generar mensaje
        if es_anomalia:
            if monto > categoria_mean * 2:
                razon = f"El monto es {monto/categoria_mean:.1f}x mayor al promedio de ${categoria_mean:.2f}"
            elif monto < categoria_mean * 0.3:
                razon = f"El monto es significativamente menor al promedio de ${categoria_mean:.2f}"
            else:
                razon = "Patrón inusual detectado en combinación de características"
        else:
            razon = f"Gasto dentro del rango normal (promedio: ${categoria_mean:.2f})"
        
        return {
            'es_anomalia': bool(es_anomalia),
            'confianza': round(confianza, 2),
            'score': round(float(score), 4),
            'mensaje': razon,
            'promedio_categoria': round(categoria_mean, 2),
            'desviaciones_std': round(desviacion_categoria, 2)
        }
    
    def analizar_anomalias_historicas(self, dias=30):
        """
        Analiza anomalías en los últimos N días
        
        Args:
            dias: Número de días a analizar
            
        Returns:
            DataFrame con anomalías detectadas
        """
        fecha_inicio = datetime.now() - timedelta(days=dias)
        transacciones = db_manager.obtener_transacciones_por_fecha(
            fecha_inicio, datetime.now()
        )
        
        anomalias = []
        
        for t in transacciones:
            if t.tipo == 'gasto':
                resultado = self.detectar_anomalia(t.monto, t.categoria, t.fecha)
                
                if resultado['es_anomalia']:
                    anomalias.append({
                        'fecha': t.fecha,
                        'categoria': t.categoria,
                        'monto': t.monto,
                        'motivo': t.motivo,
                        'confianza': resultado['confianza'],
                        'mensaje': resultado['mensaje']
                    })
        
        return pd.DataFrame(anomalias)
    
    def guardar_modelo(self):
        """Guarda el modelo entrenado"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler
                }, f)
            logger.info(f"✅ Detector guardado en {self.model_path}")
        except Exception as e:
            logger.error(f"❌ Error al guardar detector: {e}")
    
    def cargar_modelo(self):
        """Carga el modelo entrenado"""
        try:
            if not self.model_path.exists():
                return False
            
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.scaler = data['scaler']
            
            self.is_trained = True
            logger.info("✅ Detector cargado correctamente")
            return True
        except Exception as e:
            logger.error(f"❌ Error al cargar detector: {e}")
            return False

# Instancia global
detector = DetectorAnomalias()