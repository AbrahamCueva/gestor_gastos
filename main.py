"""
GESTOR FINANCIERO INTELIGENTE
Archivo principal de prueba e inicialización
"""
import sys
from datetime import datetime, timedelta
from src.utils.logger import logger
from src.utils.database import db_manager
from src.data_processing.data_generator import data_generator
from src.data_processing.analysis import analisis
from src.models.prediccion_gastos import predictor
from src.models.detector_anomalias import detector
from src.utils.reportes import generador_reportes
from src.utils.alertas import sistema_alertas

def menu_principal():
    """Menú principal del gestor"""
    print("\n" + "="*60)
    print("💰 GESTOR FINANCIERO INTELIGENTE 💰")
    print("="*60)
    print("\n📊 GESTIÓN DE DATOS:")
    print("1. 📊 Generar datos de prueba")
    print("2. ➕ Agregar transacción manual")
    print("3. 📋 Ver todas las transacciones")
    print("4. 📈 Ver resumen financiero")
    print("\n🤖 INTELIGENCIA ARTIFICIAL:")
    print("5. 🧠 Entrenar modelos de IA")
    print("6. 🔮 Predicciones de gastos")
    print("7. 🔍 Detectar anomalías")
    print("8. 📊 Análisis avanzado")
    print("\n📄 REPORTES Y ALERTAS:")
    print("11. 📑 Generar reporte Excel")
    print("12. 📊 Exportar a CSV")
    print("13. 📷 Generar gráficos")
    print("14. 🔔 Ver alertas y notificaciones")
    print("15. 💰 Gestionar presupuestos")
    print("\n💻 INTERFACES:")
    print("9. 🚀 Iniciar Dashboard Web")
    print("\n⚙️  UTILIDADES:")
    print("10. 🗑️  Limpiar base de datos")
    print("0. ❌ Salir")
    print("="*60)

def agregar_transaccion_manual():
    """Agregar una transacción manualmente"""
    print("\n➕ AGREGAR TRANSACCIÓN")
    print("-" * 40)
    
    # Tipo
    print("\nTipo de transacción:")
    print("1. Ingreso")
    print("2. Gasto")
    tipo_opcion = input("Selecciona (1-2): ").strip()
    tipo = "ingreso" if tipo_opcion == "1" else "gasto"
    
    # Monto
    monto = float(input("Monto: $"))
    
    # Categoría
    from config.settings import CATEGORIAS_GASTOS, CATEGORIAS_INGRESOS
    categorias = CATEGORIAS_INGRESOS if tipo == "ingreso" else CATEGORIAS_GASTOS
    print("\nCategorías disponibles:")
    for i, cat in enumerate(categorias, 1):
        print(f"{i}. {cat}")
    cat_idx = int(input("Selecciona categoría: ")) - 1
    categoria = categorias[cat_idx]
    
    # Método de pago
    from config.settings import METODOS_PAGO
    print("\nMétodos de pago:")
    for i, metodo in enumerate(METODOS_PAGO, 1):
        print(f"{i}. {metodo}")
    metodo_idx = int(input("Selecciona método: ")) - 1
    metodo_pago = METODOS_PAGO[metodo_idx]
    
    # Motivo
    motivo = input("Motivo (opcional): ").strip() or None
    
    # Agregar a la BD
    transaccion_id = db_manager.agregar_transaccion(
        tipo=tipo,
        fecha=datetime.now(),
        monto=monto,
        categoria=categoria,
        metodo_pago=metodo_pago,
        motivo=motivo
    )
    
    print(f"\n✅ Transacción agregada con ID: {transaccion_id}")

def ver_todas_transacciones():
    """Muestra todas las transacciones"""
    transacciones = db_manager.obtener_todas_transacciones()
    
    if not transacciones:
        print("\n⚠️  No hay transacciones registradas")
        return
    
    print(f"\n📋 TOTAL DE TRANSACCIONES: {len(transacciones)}")
    print("-" * 100)
    print(f"{'ID':<5} {'Fecha':<20} {'Tipo':<10} {'Monto':<12} {'Categoría':<20} {'Método':<20}")
    print("-" * 100)
    
    for t in transacciones[:20]:  # Mostrar solo las primeras 20
        tipo_emoji = "📈" if t.tipo == "ingreso" else "📉"
        fecha_str = t.fecha.strftime("%Y-%m-%d %H:%M")
        monto_str = f"${t.monto:,.2f}"
        print(f"{t.id:<5} {fecha_str:<20} {tipo_emoji} {t.tipo:<8} {monto_str:<12} {t.categoria:<20} {t.metodo_pago:<20}")
    
    if len(transacciones) > 20:
        print(f"\n... y {len(transacciones) - 20} transacciones más")

def ver_resumen_financiero():
    """Muestra un resumen financiero"""
    transacciones = db_manager.obtener_todas_transacciones()
    
    if not transacciones:
        print("\n⚠️  No hay datos para mostrar")
        return
    
    # Calcular totales
    total_ingresos = sum(t.monto for t in transacciones if t.tipo == "ingreso")
    total_gastos = sum(t.monto for t in transacciones if t.tipo == "gasto")
    balance = total_ingresos - total_gastos
    
    # Resumen por categoría
    gastos_por_categoria = {}
    for t in transacciones:
        if t.tipo == "gasto":
            if t.categoria not in gastos_por_categoria:
                gastos_por_categoria[t.categoria] = 0
            gastos_por_categoria[t.categoria] += t.monto
    
    print("\n" + "="*60)
    print("📊 RESUMEN FINANCIERO")
    print("="*60)
    print(f"\n💵 Total Ingresos:  ${total_ingresos:,.2f}")
    print(f"💸 Total Gastos:    ${total_gastos:,.2f}")
    print(f"{'💰' if balance >= 0 else '⚠️ '} Balance:        ${balance:,.2f}")
    
    print("\n📊 GASTOS POR CATEGORÍA:")
    print("-" * 60)
    for categoria, monto in sorted(gastos_por_categoria.items(), key=lambda x: x[1], reverse=True):
        porcentaje = (monto / total_gastos * 100) if total_gastos > 0 else 0
        barra = "█" * int(porcentaje / 2)
        print(f"{categoria:<20} ${monto:>10,.2f} ({porcentaje:>5.1f}%) {barra}")
    
    # Últimos 30 días
    fecha_hace_30 = datetime.now() - timedelta(days=30)
    trans_30_dias = [t for t in transacciones if t.fecha >= fecha_hace_30]
    
    if trans_30_dias:
        ingresos_30 = sum(t.monto for t in trans_30_dias if t.tipo == "ingreso")
        gastos_30 = sum(t.monto for t in trans_30_dias if t.tipo == "gasto")
        
        print(f"\n📅 ÚLTIMOS 30 DÍAS:")
        print(f"   Ingresos: ${ingresos_30:,.2f}")
        print(f"   Gastos:   ${gastos_30:,.2f}")
        print(f"   Balance:  ${ingresos_30 - gastos_30:,.2f}")

def entrenar_modelos_ia():
    """Entrena todos los modelos de IA"""
    print("\n🤖 ENTRENAMIENTO DE MODELOS DE IA")
    print("="*60)
    
    # Verificar datos suficientes
    transacciones = db_manager.obtener_todas_transacciones()
    if len(transacciones) < 50:
        print(f"⚠️  Necesitas al menos 50 transacciones para entrenar")
        print(f"   Actualmente tienes: {len(transacciones)}")
        print("\n💡 Genera datos de prueba primero (opción 1)")
        return
    
    print(f"\n📊 Datos disponibles: {len(transacciones)} transacciones")
    print("\n🔄 Entrenando modelos... (puede tardar unos segundos)")
    
    # 1. Modelo de predicción
    print("\n1️⃣  Modelo de Predicción de Gastos...")
    resultado_pred = predictor.entrenar()
    if resultado_pred:
        print(f"   ✅ MAE: ${resultado_pred['mae']}")
        print(f"   ✅ R²: {resultado_pred['r2']}")
        print(f"   ✅ Muestras: {resultado_pred['muestras_entrenamiento']}")
    
    # 2. Detector de anomalías
    print("\n2️⃣  Detector de Anomalías...")
    resultado_det = detector.entrenar()
    if resultado_det:
        print(f"   ✅ Anomalías detectadas: {resultado_det['anomalias_detectadas']}")
        print(f"   ✅ Porcentaje: {resultado_det['porcentaje_anomalias']}%")
    
    print("\n" + "="*60)
    print("✅ ¡MODELOS ENTRENADOS EXITOSAMENTE!")
    print("="*60)

def menu_predicciones():
    """Menú de predicciones"""
    print("\n🔮 PREDICCIONES DE GASTOS")
    print("="*60)
    
    if not predictor.is_trained:
        if not predictor.cargar_modelo():
            print("⚠️  Los modelos no están entrenados")
            print("   Usa la opción 5 para entrenarlos primero")
            return
    
    print("\n1. Predecir gasto individual")
    print("2. Predicción mensual completa")
    print("3. Proyección próximos 30 días")
    print("0. Volver")
    
    opcion = input("\nSelecciona: ").strip()
    
    if opcion == "1":
        # Predecir gasto individual
        from config.settings import CATEGORIAS_GASTOS, METODOS_PAGO
        
        print("\nCategorías:")
        for i, cat in enumerate(CATEGORIAS_GASTOS, 1):
            print(f"{i}. {cat}")
        
        cat_idx = int(input("Categoría: ")) - 1
        categoria = CATEGORIAS_GASTOS[cat_idx]
        
        prediccion = predictor.predecir_gasto(categoria)
        
        if prediccion:
            print(f"\n💰 Predicción para {categoria}: ${prediccion:.2f}")
        else:
            print("\n❌ No se pudo generar predicción")
    
    elif opcion == "2":
        # Predicción mensual
        predicciones = predictor.predecir_gastos_mes()
        
        print("\n📅 PREDICCIÓN GASTOS PRÓXIMO MES:")
        print("-" * 60)
        
        for cat, monto in sorted(predicciones.items(), key=lambda x: x[1], reverse=True):
            if cat != 'TOTAL':
                print(f"{cat:<25} ${monto:>12,.2f}")
        
        print("-" * 60)
        print(f"{'TOTAL ESTIMADO':<25} ${predicciones['TOTAL']:>12,.2f}")
    
    elif opcion == "3":
        # Proyección simple
        proyeccion = analisis.proyeccion_simple(30)
        
        print("\n📊 PROYECCIÓN 30 DÍAS:")
        print("-" * 60)
        print(f"Gastos estimados:   ${proyeccion['gastos_estimados']:,.2f}")
        print(f"Ingresos estimados: ${proyeccion['ingresos_estimados']:,.2f}")
        print(f"Balance estimado:   ${proyeccion['balance_estimado']:,.2f}")
        print(f"\nPromedio diario:")
        print(f"  Gastos:  ${proyeccion['promedio_gasto_diario']:,.2f}")
        print(f"  Ingresos: ${proyeccion['promedio_ingreso_diario']:,.2f}")

def menu_anomalias():
    """Menú de detección de anomalías"""
    print("\n🔍 DETECCIÓN DE ANOMALÍAS")
    print("="*60)
    
    if not detector.is_trained:
        if not detector.cargar_modelo():
            print("⚠️  El detector no está entrenado")
            print("   Usa la opción 5 para entrenarlo primero")
            return
    
    print("\n1. Analizar gasto actual")
    print("2. Ver anomalías últimos 30 días")
    print("0. Volver")
    
    opcion = input("\nSelecciona: ").strip()
    
    if opcion == "1":
        # Analizar gasto
        from config.settings import CATEGORIAS_GASTOS
        
        monto = float(input("Monto del gasto: $"))
        
        print("\nCategorías:")
        for i, cat in enumerate(CATEGORIAS_GASTOS, 1):
            print(f"{i}. {cat}")
        
        cat_idx = int(input("Categoría: ")) - 1
        categoria = CATEGORIAS_GASTOS[cat_idx]
        
        resultado = detector.detectar_anomalia(monto, categoria)
        
        print("\n" + "="*60)
        if resultado['es_anomalia']:
            print("⚠️  ALERTA: GASTO INUSUAL DETECTADO")
        else:
            print("✅ GASTO NORMAL")
        print("="*60)
        print(f"\nConfianza: {resultado['confianza']:.1f}%")
        print(f"Promedio categoría: ${resultado['promedio_categoria']:.2f}")
        print(f"Desviaciones: {resultado['desviaciones_std']:.2f}σ")
        print(f"\n💡 {resultado['mensaje']}")
    
    elif opcion == "2":
        # Ver anomalías históricas
        anomalias_df = detector.analizar_anomalias_historicas(30)
        
        if anomalias_df.empty:
            print("\n✅ No se detectaron anomalías en los últimos 30 días")
        else:
            print(f"\n⚠️  ANOMALÍAS DETECTADAS: {len(anomalias_df)}")
            print("-" * 100)
            
            for _, row in anomalias_df.iterrows():
                fecha_str = row['fecha'].strftime('%Y-%m-%d %H:%M')
                print(f"\n📅 {fecha_str}")
                print(f"   Categoría: {row['categoria']}")
                print(f"   Monto: ${row['monto']:,.2f}")
                print(f"   Confianza: {row['confianza']:.1f}%")
                print(f"   💡 {row['mensaje']}")
                if row['motivo']:
                    print(f"   Motivo: {row['motivo']}")

def menu_analisis_avanzado():
    """Menú de análisis avanzado"""
    print("\n📊 ANÁLISIS AVANZADO")
    print("="*60)
    
    # Recargar datos
    analisis.cargar_datos()
    
    print("\n1. Tendencia mensual")
    print("2. Gastos por categoría (detallado)")
    print("3. Top 10 gastos más grandes")
    print("4. Análisis de métodos de pago")
    print("5. Gastos recurrentes")
    print("6. Gastos inusuales (estadístico)")
    print("0. Volver")
    
    opcion = input("\nSelecciona: ").strip()
    
    if opcion == "1":
        # Tendencia mensual
        tendencia = analisis.tendencia_mensual()
        
        if not tendencia.empty:
            print("\n📈 TENDENCIA MENSUAL:")
            print(tendencia.to_string())
    
    elif opcion == "2":
        # Gastos por categoría
        gastos_cat = analisis.gastos_por_categoria()
        
        if not gastos_cat.empty:
            print("\n💸 GASTOS POR CATEGORÍA:")
            print(gastos_cat.to_string())
    
    elif opcion == "3":
        # Top gastos
        top = analisis.top_gastos(10)
        
        if not top.empty:
            print("\n🏆 TOP 10 GASTOS MÁS GRANDES:")
            print("-" * 100)
            for idx, row in top.iterrows():
                print(f"\n{row['fecha']} - {row['categoria']}")
                print(f"   Monto: ${row['monto']:,.2f}")
                print(f"   Método: {row['metodo_pago']}")
                if row['motivo']:
                    print(f"   Motivo: {row['motivo']}")
    
    elif opcion == "4":
        # Métodos de pago
        metodos = analisis.analisis_metodos_pago()
        
        if not metodos.empty:
            print("\n💳 ANÁLISIS DE MÉTODOS DE PAGO:")
            print(metodos.to_string())
    
    elif opcion == "5":
        # Recurrentes
        recurrentes = analisis.analisis_recurrencia()
        
        if recurrentes:
            print("\n🔄 GASTOS RECURRENTES:")
            print(f"Total: ${recurrentes['total_gastos_recurrentes']:,.2f}")
            print(f"Cantidad: {recurrentes['numero_gastos_recurrentes']}")
            print("\nPor categoría:")
            for cat, monto in recurrentes['por_categoria'].items():
                print(f"  {cat}: ${monto:,.2f}")
        else:
            print("\n⚠️  No hay gastos recurrentes registrados")
    
    elif opcion == "6":
        # Gastos inusuales (método estadístico)
        inusuales = analisis.detectar_gastos_inusuales()
        
        if not inusuales.empty:
            print(f"\n⚠️  GASTOS INUSUALES DETECTADOS: {len(inusuales)}")
            print("-" * 100)
            for _, row in inusuales.iterrows():
                fecha_str = row['fecha'].strftime('%Y-%m-%d')
                print(f"\n📅 {fecha_str} - {row['categoria']}")
                print(f"   Monto: ${row['monto']:,.2f}")
                print(f"   Promedio: ${row['promedio_categoria']:,.2f}")
                print(f"   Desviación: {row['desviacion']:.2f}σ")
                if row['motivo']:
                    print(f"   Motivo: {row['motivo']}")
        else:
            print("\n✅ No se detectaron gastos inusuales")

def menu_reportes():
    """Menú de generación de reportes"""
    print("\n📑 GENERACIÓN DE REPORTES")
    print("="*60)
    print("\n1. Excel completo")
    print("2. CSV de transacciones")
    print("3. Gráficos de análisis")
    print("4. Reporte de periodo personalizado")
    print("0. Volver")
    
    opcion = input("\nSelecciona: ").strip()
    
    if opcion == "1":
        print("\n🔄 Generando reporte Excel...")
        filepath = generador_reportes.generar_excel_completo()
        print(f"✅ Reporte generado: {filepath}")
    
    elif opcion == "2":
        print("\n🔄 Generando CSV...")
        filepath = generador_reportes.generar_csv_transacciones()
        print(f"✅ CSV generado: {filepath}")
    
    elif opcion == "3":
        print("\n🔄 Generando gráficos...")
        filepath = generador_reportes.generar_graficos_analisis()
        if filepath:
            print(f"✅ Gráficos generados: {filepath}")
        else:
            print("❌ No hay datos para generar gráficos")
    
    elif opcion == "4":
        print("\nReporte de Periodo Personalizado")
        
        # Fecha inicio
        print("\nFecha inicio (YYYY-MM-DD):")
        fecha_inicio_str = input("  ").strip()
        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
        
        # Fecha fin
        print("Fecha fin (YYYY-MM-DD):")
        fecha_fin_str = input("  ").strip()
        fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
        
        # Formato
        print("\nFormato:")
        print("1. Excel")
        print("2. CSV")
        formato_op = input("Selecciona: ").strip()
        formato = 'excel' if formato_op == "1" else 'csv'
        
        print(f"\n🔄 Generando reporte {formato.upper()}...")
        filepath = generador_reportes.reporte_periodo(fecha_inicio, fecha_fin, formato)
        
        if filepath:
            print(f"✅ Reporte generado: {filepath}")
        else:
            print("❌ No hay datos en el periodo seleccionado")

def menu_alertas():
    """Menú de alertas y notificaciones"""
    print("\n🔔 ALERTAS Y NOTIFICACIONES")
    print("="*60)
    
    # Generar reporte de alertas
    reporte = sistema_alertas.generar_reporte_alertas()
    
    total = reporte['total_alertas']
    criticas = reporte['niveles']['CRÍTICO']
    advertencias = reporte['niveles']['ADVERTENCIA']
    info = reporte['niveles']['INFO']
    
    print(f"\n📊 RESUMEN DE ALERTAS:")
    print(f"   Total: {total}")
    print(f"   🔴 Críticas: {criticas}")
    print(f"   🟡 Advertencias: {advertencias}")
    print(f"   🔵 Información: {info}")
    
    if total == 0:
        print("\n✅ ¡No hay alertas! Todo está bajo control.")
        return
    
    print("\n" + "="*60)
    
    # Alertas de presupuesto
    if reporte['alertas_presupuesto']:
        print("\n💰 ALERTAS DE PRESUPUESTO:")
        print("-" * 60)
        for alerta in reporte['alertas_presupuesto']:
            emoji = "🔴" if alerta['nivel'] == "CRÍTICO" else "🟡"
            print(f"\n{emoji} {alerta['categoria']}")
            print(f"   Usado: ${alerta['gasto_actual']:,.2f} / ${alerta['presupuesto_total']:,.2f}")
            print(f"   Porcentaje: {alerta['porcentaje_usado']}%")
            print(f"   {alerta['mensaje']}")
    
    # Gastos inusuales
    if reporte['alertas_gastos_inusuales']:
        print("\n⚠️  GASTOS INUSUALES DETECTADOS:")
        print("-" * 60)
        for alerta in reporte['alertas_gastos_inusuales']:
            print(f"\n🟡 {alerta['categoria']} - ${alerta['monto']:,.2f}")
            print(f"   Confianza: {alerta['confianza']}%")
            print(f"   {alerta['mensaje']}")
    
    # Proyección fin de mes
    if reporte['alerta_proyeccion']:
        alerta = reporte['alerta_proyeccion']
        proy = alerta['proyeccion']
        
        print("\n📅 PROYECCIÓN FIN DE MES:")
        print("-" * 60)
        print(f"🟡 {alerta['mensaje']}")
        print(f"\n   Balance actual: ${proy['balance_actual']:,.2f}")
        print(f"   Balance proyectado: ${proy['balance_proyectado_fin_mes']:,.2f}")
        print(f"   Días restantes: {proy['dias_restantes']}")
    
    # Duplicados
    if reporte['alertas_duplicados']:
        print("\n🔵 POSIBLES DUPLICADOS:")
        print("-" * 60)
        for alerta in reporte['alertas_duplicados']:
            print(f"\n🔵 {alerta['mensaje']}")
            print(f"   Diferencia: {alerta['diferencia_minutos']} minutos")

def menu_presupuestos():
    """Menú de gestión de presupuestos"""
    print("\n💰 GESTIÓN DE PRESUPUESTOS")
    print("="*60)
    print("\n1. Crear/Actualizar presupuesto")
    print("2. Ver presupuestos actuales")
    print("3. Ver uso de presupuestos (mes actual)")
    print("0. Volver")
    
    opcion = input("\nSelecciona: ").strip()
    
    if opcion == "1":
        from config.settings import CATEGORIAS_GASTOS
        
        print("\nCategorías disponibles:")
        for i, cat in enumerate(CATEGORIAS_GASTOS, 1):
            print(f"{i}. {cat}")
        
        cat_idx = int(input("\nSelecciona categoría: ")) - 1
        categoria = CATEGORIAS_GASTOS[cat_idx]
        
        monto = float(input(f"Presupuesto mensual para {categoria}: $"))
        alerta = float(input("Porcentaje de alerta (default 80): ") or "80")
        
        if sistema_alertas.crear_presupuesto(categoria, monto, alerta):
            print(f"\n✅ Presupuesto configurado: {categoria} - ${monto:,.2f}")
        else:
            print("\n❌ Error al configurar presupuesto")
    
    elif opcion == "2":
        from src.utils.database import Presupuesto
        session = db_manager.get_session()
        
        try:
            presupuestos = session.query(Presupuesto).all()
            
            if not presupuestos:
                print("\n⚠️  No hay presupuestos configurados")
            else:
                print("\n📊 PRESUPUESTOS CONFIGURADOS:")
                print("-" * 60)
                for p in presupuestos:
                    estado = "✅ Activo" if p.activo else "❌ Inactivo"
                    print(f"\n{p.categoria}")
                    print(f"   Monto: ${p.monto_mensual:,.2f}/mes")
                    print(f"   Alerta: {p.alerta_porcentaje}%")
                    print(f"   Estado: {estado}")
        finally:
            session.close()
    
    elif opcion == "3":
        alertas = sistema_alertas.verificar_presupuestos()
        
        if not alertas:
            print("\n✅ Todos los presupuestos están en orden")
        else:
            print(f"\n⚠️  {len(alertas)} categorías con alertas:")
            print("-" * 60)
            for alerta in alertas:
                emoji = "🔴" if alerta['nivel'] == "CRÍTICO" else "🟡"
                print(f"\n{emoji} {alerta['categoria']}")
                print(f"   Usado: ${alerta['gasto_actual']:,.2f} / ${alerta['presupuesto_total']:,.2f}")
                print(f"   Porcentaje: {alerta['porcentaje_usado']}%")

def main():
    """Función principal"""
    logger.info("🚀 Iniciando Gestor Financiero Inteligente")
    
    while True:
        try:
            menu_principal()
            opcion = input("\nSelecciona una opción: ").strip()
            
            if opcion == "1":
                print("\n🔄 Generando datos de prueba...")
                confirmar = input("¿Estás seguro? Esto puede tardar unos segundos (s/n): ").lower()
                if confirmar == 's':
                    data_generator.generar_datos_prueba(dias=90)
                    print("✅ Datos generados correctamente")
            
            elif opcion == "2":
                agregar_transaccion_manual()
            
            elif opcion == "3":
                ver_todas_transacciones()
            
            elif opcion == "4":
                ver_resumen_financiero()
            
            elif opcion == "5":
                entrenar_modelos_ia()
            
            elif opcion == "6":
                menu_predicciones()
            
            elif opcion == "7":
                menu_anomalias()
            
            elif opcion == "8":
                menu_analisis_avanzado()
            
            elif opcion == "9":
                print("\n🚀 Iniciando Dashboard...")
                print("Ejecuta en otra terminal: streamlit run src/dashboard/app.py")
                print("\nO presiona CTRL+C aquí y ejecuta:")
                print("  python -m streamlit run src/dashboard/app.py")
            
            elif opcion == "10":
                confirmar = input("⚠️  ¿Seguro que quieres eliminar todos los datos? (s/n): ").lower()
                if confirmar == 's':
                    data_generator.limpiar_datos()
                    print("✅ Base de datos limpiada")
            
            elif opcion == "11":
                menu_reportes()
            
            elif opcion == "12":
                print("\n🔄 Exportando a CSV...")
                filepath = generador_reportes.generar_csv_transacciones()
                print(f"✅ CSV generado: {filepath}")
            
            elif opcion == "13":
                print("\n🔄 Generando gráficos...")
                filepath = generador_reportes.generar_graficos_analisis()
                if filepath:
                    print(f"✅ Gráficos generados: {filepath}")
                else:
                    print("❌ No hay datos suficientes")
            
            elif opcion == "14":
                menu_alertas()
            
            elif opcion == "15":
                menu_presupuestos()
            
            elif opcion == "0":
                print("\n👋 ¡Hasta luego!")
                logger.info("✅ Aplicación cerrada correctamente")
                break
            
            else:
                print("\n❌ Opción inválida")
            
            input("\nPresiona ENTER para continuar...")
        
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            print(f"\n❌ Error: {e}")
            input("\nPresiona ENTER para continuar...")

if __name__ == "__main__":
    main()