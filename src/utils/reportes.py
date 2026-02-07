"""
Generador de reportes en PDF y Excel
"""
import pandas as pd
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

from src.utils.database import db_manager
from src.data_processing.analysis import analisis
from src.utils.logger import logger
from config.settings import DATA_DIR

# Configurar estilo de gráficos
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

class GeneradorReportes:
    """Genera reportes financieros en diferentes formatos"""
    
    def __init__(self):
        self.reportes_dir = DATA_DIR / "reportes"
        self.reportes_dir.mkdir(exist_ok=True)
    
    def generar_excel_completo(self, filename=None):
        """
        Genera un reporte completo en Excel con múltiples hojas
        
        Returns:
            Path al archivo generado
        """
        if filename is None:
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reporte_financiero_{fecha}.xlsx"
        
        filepath = self.reportes_dir / filename
        
        logger.info(f"📊 Generando reporte Excel: {filename}")
        
        # Recargar datos
        analisis.cargar_datos()
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Hoja 1: Resumen General
            resumen = analisis.resumen_general()
            df_resumen = pd.DataFrame([resumen]).T
            df_resumen.columns = ['Valor']
            df_resumen.to_excel(writer, sheet_name='Resumen General')
            
            # Hoja 2: Todas las transacciones
            if not analisis.transacciones_df.empty:
                df_trans = analisis.transacciones_df.copy()
                df_trans['fecha'] = df_trans['fecha'].dt.strftime('%Y-%m-%d %H:%M:%S')
                df_trans.to_excel(writer, sheet_name='Transacciones', index=False)
            
            # Hoja 3: Gastos por Categoría
            gastos_cat = analisis.gastos_por_categoria()
            if not gastos_cat.empty:
                gastos_cat.to_excel(writer, sheet_name='Gastos por Categoría')
            
            # Hoja 4: Tendencia Mensual
            tendencia = analisis.tendencia_mensual()
            if not tendencia.empty:
                tendencia.to_excel(writer, sheet_name='Tendencia Mensual')
            
            # Hoja 5: Top Gastos
            top_gastos = analisis.top_gastos(20)
            if not top_gastos.empty:
                top_gastos.to_excel(writer, sheet_name='Top 20 Gastos', index=False)
            
            # Hoja 6: Análisis Métodos de Pago
            metodos = analisis.analisis_metodos_pago()
            if not metodos.empty:
                metodos.to_excel(writer, sheet_name='Métodos de Pago')
            
            # Hoja 7: Proyección
            proyeccion = analisis.proyeccion_simple(30)
            if proyeccion:
                df_proy = pd.DataFrame([proyeccion]).T
                df_proy.columns = ['Valor']
                df_proy.to_excel(writer, sheet_name='Proyección 30 días')
        
        logger.info(f"✅ Reporte Excel generado: {filepath}")
        return filepath
    
    def generar_csv_transacciones(self, fecha_inicio=None, fecha_fin=None, filename=None):
        """
        Exporta transacciones a CSV
        
        Args:
            fecha_inicio: Fecha inicio (opcional)
            fecha_fin: Fecha fin (opcional)
            filename: Nombre del archivo (opcional)
        """
        if filename is None:
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transacciones_{fecha}.csv"
        
        filepath = self.reportes_dir / filename
        
        # Obtener transacciones
        if fecha_inicio and fecha_fin:
            transacciones = db_manager.obtener_transacciones_por_fecha(fecha_inicio, fecha_fin)
        else:
            transacciones = db_manager.obtener_todas_transacciones()
        
        # Convertir a DataFrame
        datos = [t.to_dict() for t in transacciones]
        df = pd.DataFrame(datos)
        
        # Exportar
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        logger.info(f"✅ CSV generado: {filepath}")
        return filepath
    
    def generar_graficos_analisis(self, filename=None):
        """
        Genera un set de gráficos de análisis y los guarda como imagen
        
        Returns:
            Path al archivo de imagen
        """
        if filename is None:
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"graficos_analisis_{fecha}.png"
        
        filepath = self.reportes_dir / filename
        
        # Recargar datos
        analisis.cargar_datos()
        
        if analisis.transacciones_df.empty:
            logger.warning("No hay datos para generar gráficos")
            return None
        
        # Crear figura con subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Análisis Financiero Completo', fontsize=20, fontweight='bold')
        
        # 1. Gastos por Categoría (Pie)
        gastos = analisis.transacciones_df[
            analisis.transacciones_df['tipo'] == 'gasto'
        ].groupby('categoria')['monto'].sum().sort_values(ascending=False)
        
        axes[0, 0].pie(gastos.values, labels=gastos.index, autopct='%1.1f%%', startangle=90)
        axes[0, 0].set_title('Distribución de Gastos por Categoría', fontsize=14, fontweight='bold')
        
        # 2. Tendencia temporal (Line)
        df_temporal = analisis.transacciones_df.copy()
        df_temporal['fecha_mes'] = df_temporal['fecha'].dt.to_period('M')
        
        tendencia_data = df_temporal.groupby(['fecha_mes', 'tipo'])['monto'].sum().unstack(fill_value=0)
        
        if not tendencia_data.empty:
            tendencia_data.index = tendencia_data.index.astype(str)
            
            if 'ingreso' in tendencia_data.columns:
                axes[0, 1].plot(tendencia_data.index, tendencia_data['ingreso'], 
                              marker='o', linewidth=2, label='Ingresos', color='#2ecc71')
            
            if 'gasto' in tendencia_data.columns:
                axes[0, 1].plot(tendencia_data.index, tendencia_data['gasto'], 
                              marker='o', linewidth=2, label='Gastos', color='#e74c3c')
            
            axes[0, 1].set_title('Tendencia Mensual: Ingresos vs Gastos', fontsize=14, fontweight='bold')
            axes[0, 1].set_xlabel('Mes')
            axes[0, 1].set_ylabel('Monto ($)')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 3. Top 10 Gastos (Bar)
        top_gastos = analisis.top_gastos(10)
        if not top_gastos.empty:
            axes[1, 0].barh(range(len(top_gastos)), top_gastos['monto'], color='#e74c3c')
            axes[1, 0].set_yticks(range(len(top_gastos)))
            axes[1, 0].set_yticklabels([f"{row['categoria'][:15]}\n{row['fecha']}" 
                                        for _, row in top_gastos.iterrows()], fontsize=8)
            axes[1, 0].set_xlabel('Monto ($)')
            axes[1, 0].set_title('Top 10 Gastos Más Grandes', fontsize=14, fontweight='bold')
            axes[1, 0].invert_yaxis()
            axes[1, 0].grid(True, alpha=0.3, axis='x')
        
        # 4. Métodos de Pago (Bar)
        metodos = analisis.analisis_metodos_pago()
        if not metodos.empty:
            axes[1, 1].bar(range(len(metodos)), metodos['Total_Gastado'], color='#3498db')
            axes[1, 1].set_xticks(range(len(metodos)))
            axes[1, 1].set_xticklabels(metodos.index, rotation=45, ha='right', fontsize=9)
            axes[1, 1].set_ylabel('Monto Total ($)')
            axes[1, 1].set_title('Gastos por Método de Pago', fontsize=14, fontweight='bold')
            axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✅ Gráficos generados: {filepath}")
        return filepath
    
    def reporte_periodo(self, fecha_inicio, fecha_fin, formato='excel'):
        """
        Genera un reporte para un periodo específico
        
        Args:
            fecha_inicio: datetime
            fecha_fin: datetime
            formato: 'excel' o 'csv'
        """
        transacciones = db_manager.obtener_transacciones_por_fecha(fecha_inicio, fecha_fin)
        
        if not transacciones:
            logger.warning("No hay transacciones en el periodo especificado")
            return None
        
        # Crear DataFrame
        datos = [t.to_dict() for t in transacciones]
        df = pd.DataFrame(datos)
        
        # Calcular estadísticas
        ingresos = df[df['tipo'] == 'ingreso']['monto'].sum()
        gastos = df[df['tipo'] == 'gasto']['monto'].sum()
        balance = ingresos - gastos
        
        # Nombre del archivo
        fecha_str = f"{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}"
        
        if formato == 'excel':
            filename = f"reporte_periodo_{fecha_str}.xlsx"
            filepath = self.reportes_dir / filename
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Resumen
                resumen_data = {
                    'Concepto': ['Ingresos', 'Gastos', 'Balance', 'Num. Transacciones'],
                    'Valor': [ingresos, gastos, balance, len(df)]
                }
                pd.DataFrame(resumen_data).to_excel(writer, sheet_name='Resumen', index=False)
                
                # Transacciones
                df.to_excel(writer, sheet_name='Transacciones', index=False)
                
                # Por categoría
                gastos_cat = df[df['tipo'] == 'gasto'].groupby('categoria')['monto'].sum().reset_index()
                gastos_cat.columns = ['Categoría', 'Total']
                gastos_cat = gastos_cat.sort_values('Total', ascending=False)
                gastos_cat.to_excel(writer, sheet_name='Por Categoría', index=False)
        
        else:  # CSV
            filename = f"reporte_periodo_{fecha_str}.csv"
            filepath = self.reportes_dir / filename
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        logger.info(f"✅ Reporte de periodo generado: {filepath}")
        return filepath

# Instancia global
generador_reportes = GeneradorReportes()