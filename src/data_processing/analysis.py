"""
Análisis avanzado de datos financieros
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.utils.database import db_manager
from src.utils.logger import logger
from typing import Dict, List, Tuple

class AnalisisFinanciero:
    """Análisis estadístico y de tendencias de datos financieros"""
    
    def __init__(self):
        self.transacciones_df = None
        self.cargar_datos()
    
    def cargar_datos(self):
        """Carga las transacciones en un DataFrame de pandas"""
        transacciones = db_manager.obtener_todas_transacciones()
        
        if not transacciones:
            logger.warning("No hay transacciones para analizar")
            self.transacciones_df = pd.DataFrame()
            return
        
        # Convertir a DataFrame
        datos = []
        for t in transacciones:
            datos.append({
                'id': t.id,
                'tipo': t.tipo,
                'fecha': t.fecha,
                'monto': t.monto,
                'categoria': t.categoria,
                'subcategoria': t.subcategoria,
                'metodo_pago': t.metodo_pago,
                'motivo': t.motivo,
                'es_recurrente': bool(t.es_recurrente)
            })
        
        self.transacciones_df = pd.DataFrame(datos)
        self.transacciones_df['fecha'] = pd.to_datetime(self.transacciones_df['fecha'])
        
        logger.info(f"✅ Datos cargados: {len(self.transacciones_df)} transacciones")
    
    def resumen_general(self) -> Dict:
        """Genera un resumen general de las finanzas"""
        if self.transacciones_df.empty:
            return {}
        
        ingresos = self.transacciones_df[self.transacciones_df['tipo'] == 'ingreso']['monto'].sum()
        gastos = self.transacciones_df[self.transacciones_df['tipo'] == 'gasto']['monto'].sum()
        balance = ingresos - gastos
        
        # Promedios
        promedio_ingreso = self.transacciones_df[
            self.transacciones_df['tipo'] == 'ingreso'
        ]['monto'].mean()
        
        promedio_gasto = self.transacciones_df[
            self.transacciones_df['tipo'] == 'gasto'
        ]['monto'].mean()
        
        return {
            'total_ingresos': round(ingresos, 2),
            'total_gastos': round(gastos, 2),
            'balance': round(balance, 2),
            'promedio_ingreso': round(promedio_ingreso, 2) if not pd.isna(promedio_ingreso) else 0,
            'promedio_gasto': round(promedio_gasto, 2) if not pd.isna(promedio_gasto) else 0,
            'num_transacciones': len(self.transacciones_df),
            'tasa_ahorro': round((balance / ingresos * 100), 2) if ingresos > 0 else 0
        }
    
    def gastos_por_categoria(self) -> pd.DataFrame:
        """Agrupa gastos por categoría con estadísticas"""
        gastos = self.transacciones_df[self.transacciones_df['tipo'] == 'gasto']
        
        if gastos.empty:
            return pd.DataFrame()
        
        resumen = gastos.groupby('categoria').agg({
            'monto': ['sum', 'mean', 'count', 'std']
        }).round(2)
        
        resumen.columns = ['Total', 'Promedio', 'Cantidad', 'Desv_Std']
        resumen = resumen.sort_values('Total', ascending=False)
        
        # Añadir porcentaje
        total_gastos = gastos['monto'].sum()
        resumen['Porcentaje'] = (resumen['Total'] / total_gastos * 100).round(2)
        
        return resumen
    
    def tendencia_mensual(self) -> pd.DataFrame:
        """Calcula tendencias mensuales de ingresos y gastos"""
        if self.transacciones_df.empty:
            return pd.DataFrame()
        
        df = self.transacciones_df.copy()
        df['mes'] = df['fecha'].dt.to_period('M')
        
        # Agrupar por mes y tipo
        tendencia = df.groupby(['mes', 'tipo'])['monto'].sum().unstack(fill_value=0)
        
        # Calcular balance mensual
        if 'ingreso' in tendencia.columns and 'gasto' in tendencia.columns:
            tendencia['balance'] = tendencia['ingreso'] - tendencia['gasto']
        elif 'ingreso' in tendencia.columns:
            tendencia['balance'] = tendencia['ingreso']
        elif 'gasto' in tendencia.columns:
            tendencia['balance'] = -tendencia['gasto']
        
        # Convertir periodo a string para mejor visualización
        tendencia.index = tendencia.index.astype(str)
        
        return tendencia.round(2)
    
    def analisis_metodos_pago(self) -> pd.DataFrame:
        """Analiza el uso de métodos de pago"""
        if self.transacciones_df.empty:
            return pd.DataFrame()
        
        analisis = self.transacciones_df.groupby('metodo_pago').agg({
            'monto': ['sum', 'count', 'mean']
        }).round(2)
        
        analisis.columns = ['Total_Gastado', 'Num_Transacciones', 'Monto_Promedio']
        analisis = analisis.sort_values('Total_Gastado', ascending=False)
        
        return analisis
    
    def detectar_gastos_inusuales(self, num_desv=2.5) -> pd.DataFrame:
        """
        Detecta gastos que están fuera del rango normal usando desviación estándar
        
        Args:
            num_desv: Número de desviaciones estándar para considerar inusual
        """
        gastos = self.transacciones_df[self.transacciones_df['tipo'] == 'gasto'].copy()
        
        if gastos.empty or len(gastos) < 10:
            return pd.DataFrame()
        
        # Por categoría
        gastos_inusuales = []
        
        for categoria in gastos['categoria'].unique():
            cat_data = gastos[gastos['categoria'] == categoria]
            
            if len(cat_data) < 3:
                continue
            
            media = cat_data['monto'].mean()
            std = cat_data['monto'].std()
            
            # Gastos que exceden la media + num_desv * desviación estándar
            umbral = media + (num_desv * std)
            
            inusuales = cat_data[cat_data['monto'] > umbral]
            
            for _, row in inusuales.iterrows():
                gastos_inusuales.append({
                    'fecha': row['fecha'],
                    'categoria': row['categoria'],
                    'monto': row['monto'],
                    'promedio_categoria': round(media, 2),
                    'desviacion': round((row['monto'] - media) / std, 2) if std > 0 else 0,
                    'motivo': row['motivo']
                })
        
        return pd.DataFrame(gastos_inusuales)
    
    def proyeccion_simple(self, dias_futuro=30) -> Dict:
        """
        Proyección simple basada en promedios históricos
        
        Args:
            dias_futuro: Días a proyectar
        """
        if self.transacciones_df.empty:
            return {}
        
        # Calcular promedios diarios
        df = self.transacciones_df.copy()
        df['dia'] = df['fecha'].dt.date
        
        gastos_diarios = df[df['tipo'] == 'gasto'].groupby('dia')['monto'].sum()
        ingresos_diarios = df[df['tipo'] == 'ingreso'].groupby('dia')['monto'].sum()
        
        promedio_gasto_diario = gastos_diarios.mean()
        promedio_ingreso_diario = ingresos_diarios.mean()
        
        # Proyección
        gastos_proyectados = promedio_gasto_diario * dias_futuro
        ingresos_proyectados = promedio_ingreso_diario * dias_futuro
        
        return {
            'dias_proyectados': dias_futuro,
            'gastos_estimados': round(gastos_proyectados, 2),
            'ingresos_estimados': round(ingresos_proyectados, 2),
            'balance_estimado': round(ingresos_proyectados - gastos_proyectados, 2),
            'promedio_gasto_diario': round(promedio_gasto_diario, 2),
            'promedio_ingreso_diario': round(promedio_ingreso_diario, 2)
        }
    
    def top_gastos(self, n=10) -> pd.DataFrame:
        """Retorna los N gastos más grandes"""
        gastos = self.transacciones_df[self.transacciones_df['tipo'] == 'gasto']
        
        if gastos.empty:
            return pd.DataFrame()
        
        top = gastos.nlargest(n, 'monto')[
            ['fecha', 'categoria', 'monto', 'motivo', 'metodo_pago']
        ].copy()
        
        top['fecha'] = top['fecha'].dt.strftime('%Y-%m-%d')
        
        return top
    
    def analisis_recurrencia(self) -> Dict:
        """Analiza gastos recurrentes"""
        recurrentes = self.transacciones_df[
            self.transacciones_df['es_recurrente'] == True
        ]
        
        if recurrentes.empty:
            return {}
        
        total_recurrente = recurrentes[recurrentes['tipo'] == 'gasto']['monto'].sum()
        num_recurrente = len(recurrentes[recurrentes['tipo'] == 'gasto'])
        
        por_categoria = recurrentes[recurrentes['tipo'] == 'gasto'].groupby(
            'categoria'
        )['monto'].sum().to_dict()
        
        return {
            'total_gastos_recurrentes': round(total_recurrente, 2),
            'numero_gastos_recurrentes': num_recurrente,
            'por_categoria': {k: round(v, 2) for k, v in por_categoria.items()}
        }

# Instancia global
analisis = AnalisisFinanciero()