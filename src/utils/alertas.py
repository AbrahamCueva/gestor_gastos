"""
Sistema de Alertas y Notificaciones Inteligentes
"""
from datetime import datetime, timedelta
from typing import List, Dict
import json

from src.utils.database import db_manager, Presupuesto
from src.data_processing.analysis import analisis
from src.models.detector_anomalias import detector
from src.utils.logger import logger
from config.settings import DATA_DIR

class SistemaAlertas:
    """Gestiona alertas y notificaciones del sistema"""
    
    def __init__(self):
        self.alertas_file = DATA_DIR / "alertas.json"
        self.alertas_activas = []
    
    def verificar_presupuestos(self) -> List[Dict]:
        """
        Verifica si se han excedido los presupuestos por categoría
        
        Returns:
            Lista de alertas de presupuesto
        """
        alertas = []
        session = db_manager.get_session()
        
        try:
            presupuestos = session.query(Presupuesto).filter(Presupuesto.activo == 1).all()
            
            if not presupuestos:
                return alertas
            
            # Obtener gastos del mes actual
            hoy = datetime.now()
            inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            transacciones_mes = db_manager.obtener_transacciones_por_fecha(inicio_mes, hoy)
            
            # Calcular gastos por categoría
            gastos_categoria = {}
            for t in transacciones_mes:
                if t.tipo == 'gasto':
                    if t.categoria not in gastos_categoria:
                        gastos_categoria[t.categoria] = 0
                    gastos_categoria[t.categoria] += t.monto
            
            # Verificar cada presupuesto
            for presupuesto in presupuestos:
                gasto_actual = gastos_categoria.get(presupuesto.categoria, 0)
                porcentaje_usado = (gasto_actual / presupuesto.monto_mensual * 100) if presupuesto.monto_mensual > 0 else 0
                
                if porcentaje_usado >= presupuesto.alerta_porcentaje:
                    nivel = "CRÍTICO" if porcentaje_usado >= 100 else "ADVERTENCIA"
                    
                    alertas.append({
                        'tipo': 'presupuesto',
                        'nivel': nivel,
                        'categoria': presupuesto.categoria,
                        'porcentaje_usado': round(porcentaje_usado, 1),
                        'gasto_actual': round(gasto_actual, 2),
                        'presupuesto_total': round(presupuesto.monto_mensual, 2),
                        'mensaje': f"Has usado {porcentaje_usado:.1f}% del presupuesto de {presupuesto.categoria}",
                        'fecha': datetime.now().isoformat()
                    })
            
        finally:
            session.close()
        
        return alertas
    
    def verificar_gastos_inusuales(self, dias=7) -> List[Dict]:
        """
        Verifica gastos inusuales recientes
        
        Args:
            dias: Días a revisar
            
        Returns:
            Lista de alertas de gastos inusuales
        """
        alertas = []
        
        if not detector.is_trained:
            return alertas
        
        try:
            anomalias_df = detector.analizar_anomalias_historicas(dias)
            
            for _, row in anomalias_df.iterrows():
                alertas.append({
                    'tipo': 'anomalia',
                    'nivel': 'ADVERTENCIA',
                    'categoria': row['categoria'],
                    'monto': round(row['monto'], 2),
                    'confianza': round(row['confianza'], 1),
                    'fecha_gasto': row['fecha'].isoformat(),
                    'mensaje': row['mensaje'],
                    'fecha': datetime.now().isoformat()
                })
        
        except Exception as e:
            logger.error(f"Error al verificar anomalías: {e}")
        
        return alertas
    
    def proyectar_fin_mes(self) -> Dict:
        """
        Proyecta si el balance será positivo o negativo al final del mes
        
        Returns:
            Dict con proyección y alerta si es necesario
        """
        hoy = datetime.now()
        inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calcular días transcurridos y restantes
        import calendar
        dias_mes = calendar.monthrange(hoy.year, hoy.month)[1]
        dias_transcurridos = hoy.day
        dias_restantes = dias_mes - dias_transcurridos
        
        if dias_restantes <= 0:
            return {}
        
        # Obtener transacciones del mes
        transacciones_mes = db_manager.obtener_transacciones_por_fecha(inicio_mes, hoy)
        
        ingresos_mes = sum(t.monto for t in transacciones_mes if t.tipo == 'ingreso')
        gastos_mes = sum(t.monto for t in transacciones_mes if t.tipo == 'gasto')
        
        # Promedios diarios
        promedio_gasto_diario = gastos_mes / dias_transcurridos if dias_transcurridos > 0 else 0
        promedio_ingreso_diario = ingresos_mes / dias_transcurridos if dias_transcurridos > 0 else 0
        
        # Proyección
        gastos_proyectados_restantes = promedio_gasto_diario * dias_restantes
        ingresos_proyectados_restantes = promedio_ingreso_diario * dias_restantes
        
        gastos_total_proyectado = gastos_mes + gastos_proyectados_restantes
        ingresos_total_proyectado = ingresos_mes + ingresos_proyectados_restantes
        
        balance_proyectado = ingresos_total_proyectado - gastos_total_proyectado
        
        proyeccion = {
            'dias_restantes': dias_restantes,
            'gastos_actual': round(gastos_mes, 2),
            'ingresos_actual': round(ingresos_mes, 2),
            'balance_actual': round(ingresos_mes - gastos_mes, 2),
            'gastos_proyectado_fin_mes': round(gastos_total_proyectado, 2),
            'ingresos_proyectado_fin_mes': round(ingresos_total_proyectado, 2),
            'balance_proyectado_fin_mes': round(balance_proyectado, 2)
        }
        
        # Generar alerta si el balance proyectado es negativo
        if balance_proyectado < 0:
            return {
                'tipo': 'proyeccion',
                'nivel': 'ADVERTENCIA',
                'mensaje': f"Proyección: Balance negativo al fin de mes (${balance_proyectado:.2f})",
                'proyeccion': proyeccion,
                'fecha': datetime.now().isoformat()
            }
        
        return {}
    
    def verificar_gastos_duplicados(self, ventana_horas=1) -> List[Dict]:
        """
        Detecta posibles gastos duplicados (mismo monto, categoría y tiempo cercano)
        
        Args:
            ventana_horas: Ventana de tiempo en horas para considerar duplicado
        """
        alertas = []
        
        # Obtener transacciones recientes
        hace_24h = datetime.now() - timedelta(hours=24)
        transacciones = db_manager.obtener_transacciones_por_fecha(hace_24h, datetime.now())
        
        gastos = [t for t in transacciones if t.tipo == 'gasto']
        
        # Buscar duplicados
        for i, gasto1 in enumerate(gastos):
            for gasto2 in gastos[i+1:]:
                # Mismo monto y categoría
                if (abs(gasto1.monto - gasto2.monto) < 0.01 and 
                    gasto1.categoria == gasto2.categoria):
                    
                    # Tiempo cercano
                    diff_tiempo = abs((gasto1.fecha - gasto2.fecha).total_seconds() / 3600)
                    
                    if diff_tiempo <= ventana_horas:
                        alertas.append({
                            'tipo': 'duplicado',
                            'nivel': 'INFO',
                            'monto': round(gasto1.monto, 2),
                            'categoria': gasto1.categoria,
                            'fecha1': gasto1.fecha.isoformat(),
                            'fecha2': gasto2.fecha.isoformat(),
                            'diferencia_minutos': round(diff_tiempo * 60, 1),
                            'mensaje': f"Posible gasto duplicado: ${gasto1.monto:.2f} en {gasto1.categoria}",
                            'fecha': datetime.now().isoformat()
                        })
        
        return alertas
    
    def generar_reporte_alertas(self) -> Dict:
        """
        Genera un reporte completo de todas las alertas
        
        Returns:
            Dict con todas las alertas categorizadas
        """
        logger.info("🔔 Generando reporte de alertas...")
        
        alertas_presupuesto = self.verificar_presupuestos()
        alertas_inusuales = self.verificar_gastos_inusuales(7)
        alerta_proyeccion = self.proyectar_fin_mes()
        alertas_duplicados = self.verificar_gastos_duplicados()
        
        reporte = {
            'fecha_generacion': datetime.now().isoformat(),
            'total_alertas': (
                len(alertas_presupuesto) + 
                len(alertas_inusuales) + 
                (1 if alerta_proyeccion else 0) +
                len(alertas_duplicados)
            ),
            'alertas_presupuesto': alertas_presupuesto,
            'alertas_gastos_inusuales': alertas_inusuales,
            'alerta_proyeccion': alerta_proyeccion if alerta_proyeccion else None,
            'alertas_duplicados': alertas_duplicados,
            'niveles': {
                'CRÍTICO': sum(1 for a in alertas_presupuesto if a['nivel'] == 'CRÍTICO'),
                'ADVERTENCIA': (
                    sum(1 for a in alertas_presupuesto if a['nivel'] == 'ADVERTENCIA') +
                    len(alertas_inusuales) +
                    (1 if alerta_proyeccion else 0)
                ),
                'INFO': len(alertas_duplicados)
            }
        }
        
        # Guardar reporte
        self.guardar_alertas(reporte)
        
        logger.info(f"✅ Reporte generado: {reporte['total_alertas']} alertas")
        return reporte
    
    def guardar_alertas(self, reporte: Dict):
        """Guarda el reporte de alertas en JSON"""
        try:
            with open(self.alertas_file, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error al guardar alertas: {e}")
    
    def cargar_alertas(self) -> Dict:
        """Carga el último reporte de alertas"""
        try:
            if self.alertas_file.exists():
                with open(self.alertas_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error al cargar alertas: {e}")
        
        return {}
    
    def crear_presupuesto(self, categoria: str, monto_mensual: float, alerta_porcentaje: float = 80.0):
        """
        Crea un nuevo presupuesto para una categoría
        
        Args:
            categoria: Nombre de la categoría
            monto_mensual: Monto del presupuesto mensual
            alerta_porcentaje: Porcentaje para generar alerta (default: 80%)
        """
        session = db_manager.get_session()
        
        try:
            # Verificar si ya existe
            existe = session.query(Presupuesto).filter(
                Presupuesto.categoria == categoria
            ).first()
            
            if existe:
                # Actualizar
                existe.monto_mensual = monto_mensual
                existe.alerta_porcentaje = alerta_porcentaje
                existe.actualizado_en = datetime.now()
                logger.info(f"✅ Presupuesto actualizado: {categoria} - ${monto_mensual}")
            else:
                # Crear nuevo
                presupuesto = Presupuesto(
                    categoria=categoria,
                    monto_mensual=monto_mensual,
                    alerta_porcentaje=alerta_porcentaje
                )
                session.add(presupuesto)
                logger.info(f"✅ Presupuesto creado: {categoria} - ${monto_mensual}")
            
            session.commit()
            return True
        
        except Exception as e:
            session.rollback()
            logger.error(f"Error al crear presupuesto: {e}")
            return False
        
        finally:
            session.close()

# Instancia global
sistema_alertas = SistemaAlertas()