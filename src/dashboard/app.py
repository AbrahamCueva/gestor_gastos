"""
Dashboard Web Interactivo - Gestor Financiero Inteligente
Ejecutar con: streamlit run src/dashboard/app.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Agregar la raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils.database import db_manager, Presupuesto
from src.data_processing.analysis import analisis
from src.models.prediccion_gastos import predictor
from src.models.detector_anomalias import detector
from src.utils.reportes import generador_reportes
from src.utils.alertas import sistema_alertas
from config.settings import CATEGORIAS_GASTOS, CATEGORIAS_INGRESOS, METODOS_PAGO

# Configuración de la página
st.set_page_config(
    page_title="Gestor Financiero IA",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

def cargar_datos():
    """Carga y prepara los datos"""
    analisis.cargar_datos()
    return analisis.transacciones_df

def pagina_dashboard():
    """Página principal del dashboard"""
    st.markdown('<h1 class="main-header">💰 Gestor Financiero Inteligente</h1>', unsafe_allow_html=True)
    
    # Recargar datos
    df = cargar_datos()
    
    if df.empty:
        st.warning("⚠️ No hay datos disponibles. Genera datos de prueba o agrega transacciones manualmente.")
        return
    
    # Resumen general
    resumen = analisis.resumen_general()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💵 Total Ingresos",
            f"${resumen['total_ingresos']:,.2f}",
            delta=f"{resumen['num_transacciones']} trans."
        )
    
    with col2:
        st.metric(
            "💸 Total Gastos",
            f"${resumen['total_gastos']:,.2f}",
            delta=f"-{resumen['promedio_gasto']:.0f} promedio"
        )
    
    with col3:
        balance_color = "normal" if resumen['balance'] >= 0 else "inverse"
        st.metric(
            "💰 Balance",
            f"${resumen['balance']:,.2f}",
            delta=f"{resumen['tasa_ahorro']:.1f}% ahorro",
            delta_color=balance_color
        )
    
    with col4:
        st.metric(
            "📊 Transacciones",
            resumen['num_transacciones'],
            delta="Total registradas"
        )
    
    st.markdown("---")
    
    # Gráficos principales
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de gastos por categoría
        st.subheader("📊 Gastos por Categoría")
        gastos_cat = analisis.gastos_por_categoria()
        
        if not gastos_cat.empty:
            fig = px.pie(
                values=gastos_cat['Total'],
                names=gastos_cat.index,
                title="Distribución de Gastos",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Tendencia mensual
        st.subheader("📈 Tendencia Mensual")
        tendencia = analisis.tendencia_mensual()
        
        if not tendencia.empty:
            fig = go.Figure()
            
            if 'ingreso' in tendencia.columns:
                fig.add_trace(go.Scatter(
                    x=tendencia.index,
                    y=tendencia['ingreso'],
                    name='Ingresos',
                    mode='lines+markers',
                    line=dict(color='#2ecc71', width=3)
                ))
            
            if 'gasto' in tendencia.columns:
                fig.add_trace(go.Scatter(
                    x=tendencia.index,
                    y=tendencia['gasto'],
                    name='Gastos',
                    mode='lines+markers',
                    line=dict(color='#e74c3c', width=3)
                ))
            
            fig.update_layout(
                title="Ingresos vs Gastos",
                xaxis_title="Mes",
                yaxis_title="Monto ($)",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de gastos por categoría
    st.markdown("---")
    st.subheader("📋 Detalle por Categoría")
    
    if not gastos_cat.empty:
        # Formatear para mostrar
        gastos_display = gastos_cat.copy()
        gastos_display['Total'] = gastos_display['Total'].apply(lambda x: f"${x:,.2f}")
        gastos_display['Promedio'] = gastos_display['Promedio'].apply(lambda x: f"${x:,.2f}")
        gastos_display['Porcentaje'] = gastos_display['Porcentaje'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(gastos_display, use_container_width=True)

def pagina_predicciones():
    """Página de predicciones"""
    st.markdown('<h1 class="main-header">🔮 Predicciones Inteligentes</h1>', unsafe_allow_html=True)
    
    # Verificar si el modelo está entrenado
    if not predictor.is_trained and not predictor.cargar_modelo():
        st.warning("⚠️ Los modelos no están entrenados. Entrena los modelos primero desde el menú principal.")
        
        if st.button("🧠 Entrenar Modelos Ahora"):
            with st.spinner("Entrenando modelos..."):
                resultado = predictor.entrenar()
                if resultado:
                    st.success(f"✅ Modelo entrenado - R²: {resultado['r2']}")
                    st.experimental_rerun()
        return
    
    tab1, tab2, tab3 = st.tabs(["🎯 Predicción Individual", "📅 Predicción Mensual", "📊 Proyección"])
    
    with tab1:
        st.subheader("Predecir Gasto Individual")
        
        col1, col2 = st.columns(2)
        
        with col1:
            categoria = st.selectbox("Categoría", CATEGORIAS_GASTOS)
            fecha = st.date_input("Fecha", datetime.now())
        
        with col2:
            metodo = st.selectbox("Método de Pago", METODOS_PAGO)
            es_recurrente = st.checkbox("¿Es recurrente?")
        
        if st.button("🔮 Predecir"):
            fecha_dt = datetime.combine(fecha, datetime.min.time())
            prediccion = predictor.predecir_gasto(
                categoria, 
                metodo_pago=metodo,
                fecha=fecha_dt,
                es_recurrente=es_recurrente
            )
            
            if prediccion:
                st.success(f"### 💰 Predicción: ${prediccion:,.2f}")
            else:
                st.error("No se pudo generar la predicción")
    
    with tab2:
        st.subheader("Predicción de Gastos Mensual")
        
        col1, col2 = st.columns(2)
        with col1:
            mes = st.selectbox("Mes", list(range(1, 13)), index=datetime.now().month % 12)
        with col2:
            año = st.number_input("Año", min_value=2024, max_value=2030, value=datetime.now().year)
        
        if st.button("📊 Generar Predicción Mensual"):
            predicciones = predictor.predecir_gastos_mes(mes, año)
            
            # Crear gráfico
            cats = [k for k in predicciones.keys() if k != 'TOTAL']
            valores = [predicciones[k] for k in cats]
            
            fig = px.bar(
                x=cats,
                y=valores,
                title=f"Predicción de Gastos - {mes}/{año}",
                labels={'x': 'Categoría', 'y': 'Monto ($)'},
                color=valores,
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.metric("💰 Total Estimado", f"${predicciones['TOTAL']:,.2f}")
    
    with tab3:
        st.subheader("Proyección Próximos 30 Días")
        
        proyeccion = analisis.proyeccion_simple(30)
        
        if proyeccion:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💸 Gastos Estimados", f"${proyeccion['gastos_estimados']:,.2f}")
            with col2:
                st.metric("💵 Ingresos Estimados", f"${proyeccion['ingresos_estimados']:,.2f}")
            with col3:
                st.metric("💰 Balance Estimado", f"${proyeccion['balance_estimado']:,.2f}")
            
            # Gráfico comparativo
            fig = go.Figure(data=[
                go.Bar(name='Gastos', x=['Estimado'], y=[proyeccion['gastos_estimados']], marker_color='#e74c3c'),
                go.Bar(name='Ingresos', x=['Estimado'], y=[proyeccion['ingresos_estimados']], marker_color='#2ecc71')
            ])
            fig.update_layout(barmode='group', title="Comparación 30 días")
            st.plotly_chart(fig, use_container_width=True)

def pagina_anomalias():
    """Página de detección de anomalías"""
    st.markdown('<h1 class="main-header">🔍 Detección de Anomalías</h1>', unsafe_allow_html=True)
    
    if not detector.is_trained and not detector.cargar_modelo():
        st.warning("⚠️ El detector no está entrenado.")
        
        if st.button("🧠 Entrenar Detector"):
            with st.spinner("Entrenando detector..."):
                resultado = detector.entrenar()
                if resultado:
                    st.success(f"✅ Detector entrenado - {resultado['anomalias_detectadas']} anomalías detectadas")
                    st.experimental_rerun()
        return
    
    tab1, tab2 = st.tabs(["🔍 Analizar Gasto", "📋 Historial de Anomalías"])
    
    with tab1:
        st.subheader("Analizar Nuevo Gasto")
        
        col1, col2 = st.columns(2)
        
        with col1:
            monto = st.number_input("Monto ($)", min_value=0.0, value=100.0, step=10.0)
            categoria = st.selectbox("Categoría", CATEGORIAS_GASTOS, key="anomalia_cat")
        
        with col2:
            fecha = st.date_input("Fecha", datetime.now(), key="anomalia_fecha")
        
        if st.button("🔍 Analizar"):
            fecha_dt = datetime.combine(fecha, datetime.now().time())
            resultado = detector.detectar_anomalia(monto, categoria, fecha_dt)
            
            # Usamos .get() para evitar que el programa falle si falta alguna llave
            es_anomalia = resultado.get('es_anomalia', False)
            promedio = resultado.get('promedio_categoria', 0.0)
            confianza = resultado.get('confianza', 0.0)
            desviaciones = resultado.get('desviaciones_std', 0.0)
            mensaje = resultado.get('mensaje', 'Análisis completado')

            if es_anomalia:
                st.markdown(f"""
                <div class="warning-box">
                    <h3>⚠️ ALERTA: GASTO INUSUAL</h3>
                    <p><strong>Confianza:</strong> {confianza:.1f}%</p>
                    <p><strong>Promedio categoría:</strong> ${promedio:.2f}</p>
                    <p><strong>Desviaciones:</strong> {desviaciones:.2f}σ</p>
                    <p><strong>Razón:</strong> {mensaje}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="success-box">
                    <h3>✅ GASTO NORMAL</h3>
                    <p><strong>Promedio categoría:</strong> ${promedio:.2f}</p>
                    <p>{mensaje}</p>
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        st.subheader("Anomalías Detectadas (Últimos 30 días)")
        
        anomalias_df = detector.analizar_anomalias_historicas(30)
        
        if anomalias_df.empty:
            st.info("✅ No se detectaron anomalías en los últimos 30 días")
        else:
            st.warning(f"⚠️ {len(anomalias_df)} anomalías detectadas")
            
            # Mostrar tabla
            display_df = anomalias_df.copy()
            display_df['fecha'] = display_df['fecha'].dt.strftime('%Y-%m-%d %H:%M')
            display_df['monto'] = display_df['monto'].apply(lambda x: f"${x:,.2f}")
            display_df['confianza'] = display_df['confianza'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(display_df, use_container_width=True)

def pagina_agregar_transaccion():
    """Página para agregar transacciones"""
    st.markdown('<h1 class="main-header">➕ Agregar Transacción</h1>', unsafe_allow_html=True)
    
    tipo = st.radio("Tipo", ["💵 Ingreso", "💸 Gasto"], horizontal=True)
    tipo_limpio = "ingreso" if "Ingreso" in tipo else "gasto"
    
    col1, col2 = st.columns(2)
    
    with col1:
        monto = st.number_input("Monto ($)", min_value=0.01, value=100.0, step=10.0)
        categorias = CATEGORIAS_INGRESOS if tipo_limpio == "ingreso" else CATEGORIAS_GASTOS
        categoria = st.selectbox("Categoría", categorias)
    
    with col2:
        metodo_pago = st.selectbox("Método de Pago", METODOS_PAGO)
        fecha = st.date_input("Fecha", datetime.now())
    
    motivo = st.text_area("Motivo (opcional)")
    es_recurrente = st.checkbox("¿Es recurrente?")
    
    if st.button("💾 Guardar Transacción", type="primary"):
        fecha_dt = datetime.combine(fecha, datetime.now().time())
        
        try:
            transaccion_id = db_manager.agregar_transaccion(
                tipo=tipo_limpio,
                fecha=fecha_dt,
                monto=monto,
                categoria=categoria,
                metodo_pago=metodo_pago,
                motivo=motivo if motivo else None,
                es_recurrente=es_recurrente
            )
            
            st.success(f"✅ Transacción #{transaccion_id} agregada correctamente")
            
            # Recargar datos
            analisis.cargar_datos()
        
        except Exception as e:
            st.error(f"❌ Error: {e}")

def pagina_reportes():
    """Página de generación de reportes"""
    st.markdown('<h1 class="main-header">📑 Reportes y Exportación</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Excel Completo", "📄 CSV", "📷 Gráficos", "📅 Periodo Personalizado"])
    
    with tab1:
        st.subheader("Generar Reporte Excel Completo")
        st.info("Genera un archivo Excel con múltiples hojas: Resumen, Transacciones, Categorías, Tendencias, etc.")
        
        if st.button("📊 Generar Excel Completo", type="primary"):
            with st.spinner("Generando reporte Excel..."):
                try:
                    filepath = generador_reportes.generar_excel_completo()
                    st.success(f"✅ Reporte generado exitosamente!")
                    st.code(f"Ubicación: {filepath}")
                    
                    # Botón para descargar
                    with open(filepath, 'rb') as f:
                        st.download_button(
                            label="⬇️ Descargar Excel",
                            data=f,
                            file_name=filepath.name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with tab2:
        st.subheader("Exportar Transacciones a CSV")
        
        col1, col2 = st.columns(2)
        with col1:
            usar_fechas = st.checkbox("Filtrar por fechas")
        
        if usar_fechas:
            with col1:
                fecha_inicio = st.date_input("Fecha inicio", datetime.now() - timedelta(days=30))
            with col2:
                fecha_fin = st.date_input("Fecha fin", datetime.now())
        
        if st.button("📄 Generar CSV", type="primary"):
            with st.spinner("Generando CSV..."):
                try:
                    if usar_fechas:
                        fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
                        fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
                        filepath = generador_reportes.generar_csv_transacciones(fecha_inicio_dt, fecha_fin_dt)
                    else:
                        filepath = generador_reportes.generar_csv_transacciones()
                    
                    st.success("✅ CSV generado exitosamente!")
                    st.code(f"Ubicación: {filepath}")
                    
                    with open(filepath, 'rb') as f:
                        st.download_button(
                            label="⬇️ Descargar CSV",
                            data=f,
                            file_name=filepath.name,
                            mime="text/csv"
                        )
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with tab3:
        st.subheader("Generar Gráficos de Análisis")
        st.info("Genera una imagen PNG con 4 gráficos: Distribución por categoría, Tendencia mensual, Top gastos y Métodos de pago")
        
        if st.button("📷 Generar Gráficos", type="primary"):
            with st.spinner("Generando gráficos..."):
                try:
                    filepath = generador_reportes.generar_graficos_analisis()
                    if filepath:
                        st.success("✅ Gráficos generados!")
                        st.code(f"Ubicación: {filepath}")
                        
                        # Mostrar imagen
                        st.image(str(filepath), caption="Análisis Financiero Completo")
                        
                        with open(filepath, 'rb') as f:
                            st.download_button(
                                label="⬇️ Descargar PNG",
                                data=f,
                                file_name=filepath.name,
                                mime="image/png"
                            )
                    else:
                        st.warning("⚠️ No hay suficientes datos para generar gráficos")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with tab4:
        st.subheader("Reporte de Periodo Personalizado")
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha inicio", datetime.now() - timedelta(days=30), key="periodo_inicio")
        with col2:
            fecha_fin = st.date_input("Fecha fin", datetime.now(), key="periodo_fin")
        
        formato = st.radio("Formato", ["Excel", "CSV"], horizontal=True)
        
        if st.button("📅 Generar Reporte de Periodo", type="primary"):
            with st.spinner("Generando reporte..."):
                try:
                    fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
                    fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
                    
                    filepath = generador_reportes.reporte_periodo(
                        fecha_inicio_dt, 
                        fecha_fin_dt, 
                        formato.lower()
                    )
                    
                    if filepath:
                        st.success("✅ Reporte generado!")
                        st.code(f"Ubicación: {filepath}")
                        
                        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if formato == "Excel" else "text/csv"
                        
                        with open(filepath, 'rb') as f:
                            st.download_button(
                                label=f"⬇️ Descargar {formato}",
                                data=f,
                                file_name=filepath.name,
                                mime=mime_type
                            )
                    else:
                        st.warning("⚠️ No hay datos en el periodo seleccionado")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

def pagina_alertas():
    """Página de alertas y notificaciones"""
    st.markdown('<h1 class="main-header">🔔 Alertas y Notificaciones</h1>', unsafe_allow_html=True)
    
    # Generar reporte de alertas
    with st.spinner("Analizando..."):
        reporte = sistema_alertas.generar_reporte_alertas()
    
    # Resumen de alertas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Alertas", reporte['total_alertas'])
    with col2:
        st.metric("🔴 Críticas", reporte['niveles']['CRÍTICO'])
    with col3:
        st.metric("🟡 Advertencias", reporte['niveles']['ADVERTENCIA'])
    with col4:
        st.metric("🔵 Información", reporte['niveles']['INFO'])
    
    if reporte['total_alertas'] == 0:
        st.success("✅ ¡No hay alertas! Todo está bajo control.")
        return
    
    st.markdown("---")
    
    # Pestañas de alertas
    tabs = []
    if reporte['alertas_presupuesto']:
        tabs.append("💰 Presupuestos")
    if reporte['alertas_gastos_inusuales']:
        tabs.append("⚠️ Gastos Inusuales")
    if reporte['alerta_proyeccion']:
        tabs.append("📅 Proyección")
    if reporte['alertas_duplicados']:
        tabs.append("🔄 Duplicados")
    
    if tabs:
        tab_objects = st.tabs(tabs)
        tab_index = 0
        
        # Tab Presupuestos
        if reporte['alertas_presupuesto']:
            with tab_objects[tab_index]:
                st.subheader("Alertas de Presupuesto")
                
                for alerta in reporte['alertas_presupuesto']:
                    nivel_emoji = "🔴" if alerta['nivel'] == "CRÍTICO" else "🟡"
                    nivel_color = "#dc3545" if alerta['nivel'] == "CRÍTICO" else "#ffc107"
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="padding: 1rem; border-left: 4px solid {nivel_color}; background-color: #f8f9fa; margin-bottom: 1rem;">
                            <h4>{nivel_emoji} {alerta['categoria']}</h4>
                            <p><strong>Usado:</strong> ${alerta['gasto_actual']:,.2f} / ${alerta['presupuesto_total']:,.2f}</p>
                            <p><strong>Porcentaje:</strong> {alerta['porcentaje_usado']}%</p>
                            <p>{alerta['mensaje']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Barra de progreso
                        st.progress(min(alerta['porcentaje_usado'] / 100, 1.0))
            
            tab_index += 1
        
        # Tab Gastos Inusuales
        if reporte['alertas_gastos_inusuales']:
            with tab_objects[tab_index]:
                st.subheader("Gastos Inusuales Detectados")
                
                for alerta in reporte['alertas_gastos_inusuales']:
                    with st.expander(f"🟡 {alerta['categoria']} - ${alerta['monto']:,.2f}"):
                        st.write(f"**Confianza:** {alerta['confianza']}%")
                        st.write(f"**Fecha:** {alerta['fecha_gasto']}")
                        st.write(f"**Razón:** {alerta['mensaje']}")
            
            tab_index += 1
        
        # Tab Proyección
        if reporte['alerta_proyeccion']:
            with tab_objects[tab_index]:
                st.subheader("Proyección Fin de Mes")
                
                alerta = reporte['alerta_proyeccion']
                proy = alerta['proyeccion']
                
                st.warning(alerta['mensaje'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Balance Actual", f"${proy['balance_actual']:,.2f}")
                with col2:
                    st.metric("Balance Proyectado", f"${proy['balance_proyectado_fin_mes']:,.2f}")
                with col3:
                    st.metric("Días Restantes", proy['dias_restantes'])
                
                # Gráfico de comparación
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='Actual',
                    x=['Ingresos', 'Gastos'],
                    y=[proy['ingresos_actual'], proy['gastos_actual']],
                    marker_color=['#2ecc71', '#e74c3c']
                ))
                fig.add_trace(go.Bar(
                    name='Proyectado',
                    x=['Ingresos', 'Gastos'],
                    y=[proy['ingresos_proyectado_fin_mes'], proy['gastos_proyectado_fin_mes']],
                    marker_color=['#27ae60', '#c0392b']
                ))
                fig.update_layout(barmode='group', title="Comparación Actual vs Proyectado")
                st.plotly_chart(fig, use_container_width=True)
            
            tab_index += 1
        
        # Tab Duplicados
        if reporte['alertas_duplicados']:
            with tab_objects[tab_index]:
                st.subheader("Posibles Gastos Duplicados")
                
                for alerta in reporte['alertas_duplicados']:
                    with st.expander(f"🔵 {alerta['mensaje']}"):
                        st.write(f"**Monto:** ${alerta['monto']:,.2f}")
                        st.write(f"**Categoría:** {alerta['categoria']}")
                        st.write(f"**Diferencia de tiempo:** {alerta['diferencia_minutos']} minutos")
                        st.write(f"**Fecha 1:** {alerta['fecha1']}")
                        st.write(f"**Fecha 2:** {alerta['fecha2']}")

def pagina_presupuestos():
    """Página de gestión de presupuestos"""
    st.markdown('<h1 class="main-header">💰 Gestión de Presupuestos</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["➕ Crear/Editar", "📋 Ver Presupuestos", "📊 Uso Actual"])
    
    with tab1:
        st.subheader("Crear o Actualizar Presupuesto")
        
        col1, col2 = st.columns(2)
        
        with col1:
            categoria = st.selectbox("Categoría", CATEGORIAS_GASTOS, key="presupuesto_cat")
            monto_mensual = st.number_input("Presupuesto Mensual ($)", min_value=0.0, value=1000.0, step=100.0)
        
        with col2:
            alerta_porcentaje = st.slider("Porcentaje de Alerta (%)", 0, 100, 80)
            st.info(f"Recibirás alertas cuando uses el {alerta_porcentaje}% del presupuesto")
        
        if st.button("💾 Guardar Presupuesto", type="primary"):
            if sistema_alertas.crear_presupuesto(categoria, monto_mensual, alerta_porcentaje):
                st.success(f"✅ Presupuesto configurado: {categoria} - ${monto_mensual:,.2f}")
            else:
                st.error("❌ Error al configurar presupuesto")
    
    with tab2:
        st.subheader("Presupuestos Configurados")
        
        session = db_manager.get_session()
        try:
            presupuestos = session.query(Presupuesto).all()
            
            if not presupuestos:
                st.info("⚠️ No hay presupuestos configurados")
            else:
                for p in presupuestos:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        estado = "✅ Activo" if p.activo else "❌ Inactivo"
                        st.write(f"**{p.categoria}** - {estado}")
                    
                    with col2:
                        st.write(f"${p.monto_mensual:,.2f}/mes")
                    
                    with col3:
                        st.write(f"Alerta: {p.alerta_porcentaje}%")
        finally:
            session.close()
    
    with tab3:
        st.subheader("Uso de Presupuestos (Mes Actual)")
        
        alertas = sistema_alertas.verificar_presupuestos()
        
        if not alertas:
            st.success("✅ Todos los presupuestos están en orden")
        else:
            for alerta in alertas:
                nivel_emoji = "🔴" if alerta['nivel'] == "CRÍTICO" else "🟡"
                
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"{nivel_emoji} **{alerta['categoria']}**")
                        st.write(f"{alerta['mensaje']}")
                    
                    with col2:
                        st.metric(
                            "Usado",
                            f"{alerta['porcentaje_usado']}%",
                            delta=f"${alerta['gasto_actual']:,.2f}"
                        )
                    
                    st.progress(min(alerta['porcentaje_usado'] / 100, 1.0))
                    st.caption(f"${alerta['gasto_actual']:,.2f} / ${alerta['presupuesto_total']:,.2f}")

def pagina_analisis_avanzado():
    """Página de análisis avanzado"""
    st.markdown('<h1 class="main-header">📊 Análisis Avanzado</h1>', unsafe_allow_html=True)
    
    # Recargar datos
    analisis.cargar_datos()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Tendencias", "🏆 Top Gastos", "💳 Métodos de Pago", "🔄 Recurrentes"])
    
    with tab1:
        st.subheader("Tendencia Mensual Detallada")
        
        tendencia = analisis.tendencia_mensual()
        
        if not tendencia.empty:
            st.dataframe(tendencia, use_container_width=True)
            
            # Gráfico de balance
            if 'balance' in tendencia.columns:
                fig = px.line(
                    x=tendencia.index,
                    y=tendencia['balance'],
                    title="Balance Mensual",
                    labels={'x': 'Mes', 'y': 'Balance ($)'},
                    markers=True
                )
                fig.add_hline(y=0, line_dash="dash", line_color="red")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("⚠️ No hay suficientes datos para análisis de tendencias")
    
    with tab2:
        st.subheader("Top 20 Gastos Más Grandes")
        
        top_gastos = analisis.top_gastos(20)
        
        if not top_gastos.empty:
            # Tabla
            st.dataframe(top_gastos, use_container_width=True)
            
            # Gráfico
            fig = px.bar(
                top_gastos,
                x='categoria',
                y='monto',
                color='monto',
                title="Top Gastos por Categoría",
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("⚠️ No hay gastos registrados")
    
    with tab3:
        st.subheader("Análisis de Métodos de Pago")
        
        metodos = analisis.analisis_metodos_pago()
        
        if not metodos.empty:
            st.dataframe(metodos, use_container_width=True)
            
            # Gráfico de pastel
            fig = px.pie(
                values=metodos['Total_Gastado'],
                names=metodos.index,
                title="Distribución por Método de Pago",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("⚠️ No hay datos de métodos de pago")
    
    with tab4:
        st.subheader("Gastos Recurrentes")
        
        recurrentes = analisis.analisis_recurrencia()
        
        if recurrentes:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("💰 Total Gastos Recurrentes", f"${recurrentes['total_gastos_recurrentes']:,.2f}")
            
            with col2:
                st.metric("🔢 Cantidad", recurrentes['numero_gastos_recurrentes'])
            
            st.subheader("Por Categoría")
            
            # Crear DataFrame para mostrar
            df_rec = pd.DataFrame([
                {'Categoría': cat, 'Monto': monto}
                for cat, monto in recurrentes['por_categoria'].items()
            ]).sort_values('Monto', ascending=False)
            
            st.dataframe(df_rec, use_container_width=True)
            
            # Gráfico
            fig = px.bar(
                df_rec,
                x='Categoría',
                y='Monto',
                title="Gastos Recurrentes por Categoría",
                color='Monto',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("⚠️ No hay gastos recurrentes registrados")

# Sidebar
# --- SECCIÓN DE NAVEGACIÓN UNIFICADA (Sustituye desde el Sidebar hasta el final) ---

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/money-bag.png", width=80)
    st.title("Gestor Financiero")
    
    # Unificamos todas las opciones en una sola lista para evitar conflictos de estado
    opciones = [
        "🏠 Dashboard", 
        "➕ Agregar Transacción",
        "🔮 Predicciones", 
        "🔍 Anomalías", 
        "📊 Análisis Avanzado",
        "📑 Reportes", 
        "🔔 Alertas", 
        "💰 Presupuestos"
    ]
    
    pagina_seleccionada = st.radio(
        "Seleccione una sección:",
        opciones,
        index=0,
        key="navegacion_principal"
    )
    
    st.markdown("---")
    
    # Estadísticas rápidas
    st.markdown("### 📊 Resumen Rápido")
    df = cargar_datos()
    if not df.empty:
        st.metric("Transacciones", len(df))
        balance = df[df['tipo']=='ingreso']['monto'].sum() - df[df['tipo']=='gasto']['monto'].sum()
        st.metric("Balance Total", f"${balance:,.2f}")
        
        reporte_alertas = sistema_alertas.generar_reporte_alertas()
        if reporte_alertas['total_alertas'] > 0:
            st.warning(f"⚠️ {reporte_alertas['total_alertas']} alertas pendientes")

# --- ENRUTAMIENTO CORREGIDO ---
if "Dashboard" in pagina_seleccionada:
    pagina_dashboard()
elif "Agregar Transacción" in pagina_seleccionada:
    pagina_agregar_transaccion()
elif "Predicciones" in pagina_seleccionada:
    pagina_predicciones()
elif "Anomalías" in pagina_seleccionada:
    pagina_anomalias()
elif "Análisis Avanzado" in pagina_seleccionada:
    pagina_analisis_avanzado()
elif "Reportes" in pagina_seleccionada:
    pagina_reportes()
elif "Alertas" in pagina_seleccionada:
    pagina_alertas()
elif "Presupuestos" in pagina_seleccionada:
    pagina_presupuestos()