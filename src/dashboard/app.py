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

# CSS personalizado mejorado
st.markdown("""
<style>
    /* Títulos principales */
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem;
        padding: 1rem 0;
    }
    
    /* Cards mejoradas */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Success box */
    .success-box {
        padding: 1.5rem;
        border-radius: 15px;
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Warning box */
    .warning-box {
        padding: 1.5rem;
        border-radius: 15px;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Info box */
    .info-box {
        padding: 1.5rem;
        border-radius: 15px;
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Alert card */
    .alert-card {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 5px solid;
        background: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .alert-critico { border-left-color: #dc3545; }
    .alert-warning { border-left-color: #ffc107; }
    .alert-info { border-left-color: #17a2b8; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Botones mejorados */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Ocultar índices de dataframes */
    .dataframe {
        font-size: 0.9rem;
    }
    
    /* Mejorar tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Estado de sesión para navegación
if 'pagina_actual' not in st.session_state:
    st.session_state.pagina_actual = "🏠 Dashboard"

def cargar_datos():
    """Carga y prepara los datos"""
    analisis.cargar_datos()
    
    # Si no hay datos, generar automáticamente
    if analisis.transacciones_df.empty:
        st.info("🔄 Generando datos de prueba automáticamente...")
        try:
            from src.data_processing.data_generator import data_generator
            data_generator.generar_datos_prueba(dias=90)
            analisis.cargar_datos()
            st.success("✅ Datos de prueba generados")
        except Exception as e:
            st.warning(f"No se pudieron generar datos automáticamente: {e}")
    
    return analisis.transacciones_df

def pagina_dashboard():
    """Página principal del dashboard con diseño mejorado"""
    st.markdown('<h1 class="main-header">💰 Dashboard Financiero Inteligente</h1>', unsafe_allow_html=True)
    
    # Recargar datos
    df = cargar_datos()
    
    if df.empty:
        st.markdown("""
        <div class="info-box">
            <h3>👋 ¡Bienvenido!</h3>
            <p>No hay datos disponibles. Genera datos de prueba o agrega transacciones manualmente.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Resumen general
    resumen = analisis.resumen_general()
    
    # Métricas principales con diseño mejorado
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.5rem; border-radius: 15px; color: white; text-align: center;">
            <h4 style="margin: 0; opacity: 0.9;">💵 Ingresos</h4>
            <h2 style="margin: 0.5rem 0;">${:,.0f}</h2>
            <p style="margin: 0; opacity: 0.8; font-size: 0.9rem;">{} transacciones</p>
        </div>
        """.format(resumen['total_ingresos'], resumen['num_transacciones']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 1.5rem; border-radius: 15px; color: white; text-align: center;">
            <h4 style="margin: 0; opacity: 0.9;">💸 Gastos</h4>
            <h2 style="margin: 0.5rem 0;">${:,.0f}</h2>
            <p style="margin: 0; opacity: 0.8; font-size: 0.9rem;">Promedio: ${:,.0f}</p>
        </div>
        """.format(resumen['total_gastos'], resumen['promedio_gasto']), unsafe_allow_html=True)
    
    with col3:
        balance_gradient = "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)" if resumen['balance'] >= 0 else "linear-gradient(135deg, #ee0979 0%, #ff6a00 100%)"
        st.markdown("""
        <div style="background: {}; 
                    padding: 1.5rem; border-radius: 15px; color: white; text-align: center;">
            <h4 style="margin: 0; opacity: 0.9;">💰 Balance</h4>
            <h2 style="margin: 0.5rem 0;">${:,.0f}</h2>
            <p style="margin: 0; opacity: 0.8; font-size: 0.9rem;">Ahorro: {:.1f}%</p>
        </div>
        """.format(balance_gradient, resumen['balance'], resumen['tasa_ahorro']), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 1.5rem; border-radius: 15px; color: white; text-align: center;">
            <h4 style="margin: 0; opacity: 0.9;">📊 Total</h4>
            <h2 style="margin: 0.5rem 0;">{}</h2>
            <p style="margin: 0; opacity: 0.8; font-size: 0.9rem;">Transacciones</p>
        </div>
        """.format(resumen['num_transacciones']), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Gráficos principales
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Distribución de Gastos")
        gastos_cat = analisis.gastos_por_categoria()
        
        if not gastos_cat.empty:
            fig = px.pie(
                values=gastos_cat['Total'],
                names=gastos_cat.index,
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                textfont_size=12,
                marker=dict(line=dict(color='white', width=2))
            )
            fig.update_layout(
                showlegend=False,
                height=400,
                margin=dict(t=30, b=30, l=30, r=30)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📈 Tendencia Mensual")
        tendencia = analisis.tendencia_mensual()
        
        if not tendencia.empty:
            fig = go.Figure()
            
            if 'ingreso' in tendencia.columns:
                fig.add_trace(go.Scatter(
                    x=tendencia.index,
                    y=tendencia['ingreso'],
                    name='Ingresos',
                    mode='lines+markers',
                    line=dict(color='#2ecc71', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(46, 204, 113, 0.1)'
                ))
            
            if 'gasto' in tendencia.columns:
                fig.add_trace(go.Scatter(
                    x=tendencia.index,
                    y=tendencia['gasto'],
                    name='Gastos',
                    mode='lines+markers',
                    line=dict(color='#e74c3c', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(231, 76, 60, 0.1)'
                ))
            
            fig.update_layout(
                xaxis_title="Mes",
                yaxis_title="Monto ($)",
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=400,
                margin=dict(t=50, b=30, l=30, r=30)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de gastos por categoría
    st.markdown("---")
    st.markdown("### 📋 Detalle por Categoría")
    
    if not gastos_cat.empty:
        # Crear gráfico de barras horizontal
        fig = px.bar(
            gastos_cat.reset_index(),
            y='categoria',
            x='Total',
            orientation='h',
            text='Porcentaje',
            color='Total',
            color_continuous_scale='Reds'
        )
        
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(
            xaxis_title="Monto Total ($)",
            yaxis_title="",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla resumen
        with st.expander("📊 Ver tabla detallada"):
            gastos_display = gastos_cat.copy()
            gastos_display['Total'] = gastos_display['Total'].apply(lambda x: f"${x:,.2f}")
            gastos_display['Promedio'] = gastos_display['Promedio'].apply(lambda x: f"${x:,.2f}")
            gastos_display['Porcentaje'] = gastos_display['Porcentaje'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(gastos_display, use_container_width=True, height=400)

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
    """Página de detección de anomalías con diseño mejorado"""
    st.markdown('<h1 class="main-header">🔍 Detector de Anomalías Inteligente</h1>', unsafe_allow_html=True)
    
    # Verificar entrenamiento
    if not detector.is_trained and not detector.cargar_modelo():
        st.markdown("""
        <div class="warning-box">
            <h3>⚠️ Modelo No Entrenado</h3>
            <p>El detector de anomalías necesita ser entrenado primero para funcionar correctamente.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🧠 Entrenar Detector Ahora", type="primary", use_container_width=True):
                with st.spinner("🔄 Entrenando detector de anomalías..."):
                    resultado = detector.entrenar()
                    if resultado:
                        st.success(f"✅ Detector entrenado exitosamente!")
                        st.info(f"📊 {resultado['anomalias_detectadas']} anomalías detectadas en datos históricos")
                        st.rerun()
        return
    
    # Tabs mejoradas
    tab1, tab2 = st.tabs(["🔍 Analizar Nuevo Gasto", "📊 Historial de Anomalías"])
    
    with tab1:
        st.markdown("### Verificar si un gasto es inusual")
        st.write("Ingresa los detalles del gasto para verificar si está dentro de tus patrones normales.")
        
        # Formulario mejorado
        with st.form("form_anomalia", clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                monto = st.number_input(
                    "💵 Monto del Gasto ($)", 
                    min_value=0.0, 
                    value=100.0, 
                    step=10.0,
                    help="Ingresa el monto que quieres analizar"
                )
                
                categoria = st.selectbox(
                    "📁 Categoría",
                    CATEGORIAS_GASTOS,
                    help="Selecciona la categoría del gasto"
                )
            
            with col2:
                fecha = st.date_input(
                    "📅 Fecha del Gasto",
                    datetime.now(),
                    help="Fecha en que se realizó el gasto"
                )
                
                st.write("")  # Espaciado
                st.write("")
                analizar_btn = st.form_submit_button(
                    "🔍 Analizar Gasto",
                    type="primary",
                    use_container_width=True
                )
            
            if analizar_btn:
                fecha_dt = datetime.combine(fecha, datetime.now().time())
                
                with st.spinner("🔄 Analizando..."):
                    try:
                        resultado = detector.detectar_anomalia(monto, categoria, fecha_dt)
                    except Exception as e:
                        st.error(f"❌ Error al analizar: {e}")
                        resultado = None
                
                if resultado:
                    st.markdown("---")
                    st.markdown("### 📊 Resultado del Análisis")
                    
                    # Verificar que tengamos los datos necesarios
                    if not resultado.get('promedio_categoria') and resultado.get('mensaje'):
                        # No hay histórico suficiente
                        st.markdown(f"""
                        <div class="info-box">
                            <h3>ℹ️ Información Insuficiente</h3>
                            <p>{resultado.get('mensaje', 'No hay suficiente histórico para esta categoría.')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    elif resultado.get('es_anomalia'):
                        # Alerta de anomalía
                        st.markdown(f"""
                        <div class="warning-box">
                            <h2 style="margin:0;">⚠️ GASTO INUSUAL DETECTADO</h2>
                            <p style="font-size:1.2rem; margin:0.5rem 0;">Este gasto está fuera de tus patrones normales</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Métricas en columnas
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                "Confianza de Detección",
                                f"{resultado.get('confianza', 0):.1f}%",
                                delta="Alta" if resultado.get('confianza', 0) > 70 else "Media"
                            )
                        
                        with col2:
                            promedio = resultado.get('promedio_categoria', monto)
                            st.metric(
                                "Promedio Normal",
                                f"${promedio:.2f}",
                                delta=f"+${monto - promedio:.2f}"
                            )
                        
                        with col3:
                            desv = resultado.get('desviaciones_std', 0)
                            st.metric(
                                "Desviación",
                                f"{abs(desv):.1f}σ",
                                delta="Muy alto" if abs(desv) > 3 else "Alto"
                            )
                        
                        # Explicación
                        st.info(f"💡 **Análisis:** {resultado.get('mensaje', 'Gasto inusual detectado')}")
                        
                        # Gráfico comparativo
                        if resultado.get('promedio_categoria'):
                            fig = go.Figure()
                            
                            fig.add_trace(go.Bar(
                                x=['Promedio', 'Tu Gasto'],
                                y=[resultado['promedio_categoria'], monto],
                                marker_color=['#2ecc71', '#e74c3c'],
                                text=[f"${resultado['promedio_categoria']:.2f}", f"${monto:.2f}"],
                                textposition='auto',
                            ))
                            
                            fig.update_layout(
                                title="Comparación con el Promedio",
                                yaxis_title="Monto ($)",
                                showlegend=False,
                                height=300
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    
                    else:
                        # Gasto normal
                        st.markdown(f"""
                        <div class="success-box">
                            <h2 style="margin:0;">✅ GASTO NORMAL</h2>
                            <p style="font-size:1.2rem; margin:0.5rem 0;">Este gasto está dentro de tus patrones habituales</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            promedio = resultado.get('promedio_categoria', monto)
                            st.metric(
                                "Promedio de Categoría",
                                f"${promedio:.2f}"
                            )
                        
                        with col2:
                            diferencia = monto - promedio
                            st.metric(
                                "Diferencia",
                                f"${abs(diferencia):.2f}",
                                delta="Por encima" if diferencia > 0 else "Por debajo"
                            )
                        
                        st.success(f"💡 **Análisis:** {resultado.get('mensaje', 'Gasto dentro del rango normal')}")
    
    with tab2:
        st.markdown("### Anomalías Detectadas en los Últimos 30 Días")
        
        # Selector de días
        col1, col2 = st.columns([1, 3])
        with col1:
            dias = st.selectbox("📅 Periodo", [7, 15, 30, 60, 90], index=2)
        
        with st.spinner("🔍 Buscando anomalías..."):
            anomalias_df = detector.analizar_anomalias_historicas(dias)
        
        if anomalias_df.empty:
            st.markdown("""
            <div class="success-box">
                <h3>✅ ¡Excelente!</h3>
                <p>No se detectaron gastos inusuales en los últimos {dias} días.</p>
            </div>
            """.format(dias=dias), unsafe_allow_html=True)
        else:
            # Resumen
            st.markdown(f"""
            <div class="warning-box">
                <h3>⚠️ {len(anomalias_df)} Anomalías Detectadas</h3>
                <p>Se encontraron gastos fuera de tus patrones normales.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Estadísticas rápidas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Anomalías", len(anomalias_df))
            
            with col2:
                monto_total = anomalias_df['monto'].sum()
                st.metric("Monto Total", f"${monto_total:,.2f}")
            
            with col3:
                confianza_prom = anomalias_df['confianza'].mean()
                st.metric("Confianza Promedio", f"{confianza_prom:.1f}%")
            
            with col4:
                categorias_afectadas = anomalias_df['categoria'].nunique()
                st.metric("Categorías Afectadas", categorias_afectadas)
            
            st.markdown("---")
            
            # Lista de anomalías con diseño mejorado
            st.markdown("#### 📋 Detalle de Anomalías")
            
            for idx, row in anomalias_df.iterrows():
                with st.expander(
                    f"⚠️ {row['categoria']} - ${row['monto']:,.2f} ({row['fecha'].strftime('%d/%m/%Y')})",
                    expanded=False
                ):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**📅 Fecha:** {row['fecha'].strftime('%d de %B, %Y a las %H:%M')}")
                        st.write(f"**📁 Categoría:** {row['categoria']}")
                        st.write(f"**💰 Monto:** ${row['monto']:,.2f}")
                        if row['motivo']:
                            st.write(f"**📝 Motivo:** {row['motivo']}")
                        st.info(f"💡 {row['mensaje']}")
                    
                    with col2:
                        st.metric("Confianza", f"{row['confianza']:.1f}%")
                        
                        # Indicador visual de confianza
                        confianza_normalizada = row['confianza'] / 100
                        st.progress(confianza_normalizada)
            
            # Gráfico de anomalías por categoría
            st.markdown("---")
            st.markdown("#### 📊 Anomalías por Categoría")
            
            anomalias_por_cat = anomalias_df.groupby('categoria').agg({
                'monto': ['count', 'sum']
            }).reset_index()
            anomalias_por_cat.columns = ['Categoría', 'Cantidad', 'Monto Total']
            
            fig = px.bar(
                anomalias_por_cat,
                x='Categoría',
                y='Cantidad',
                color='Monto Total',
                title="Distribución de Anomalías",
                color_continuous_scale='Reds',
                text='Cantidad'
            )
            
            fig.update_traces(textposition='outside')
            fig.update_layout(height=400)
            
            st.plotly_chart(fig, use_container_width=True)

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

# Sidebar con navegación mejorada
with st.sidebar:
    # Logo y título
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1 style="color: white; font-size: 2rem; margin: 0;">💰</h1>
        <h2 style="color: white; font-size: 1.3rem; margin: 0.5rem 0;">Gestor Financiero</h2>
        <p style="color: rgba(255,255,255,0.8); font-size: 0.9rem;">Inteligencia Artificial</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navegación principal
    st.markdown("### 📍 Navegación")
    
    # Botones de navegación estilo vertical
    if st.button("🏠 Dashboard Principal", use_container_width=True, 
                 type="primary" if st.session_state.pagina_actual == "🏠 Dashboard" else "secondary"):
        st.session_state.pagina_actual = "🏠 Dashboard"
        st.rerun()
    
    if st.button("➕ Agregar Transacción", use_container_width=True,
                 type="primary" if st.session_state.pagina_actual == "➕ Agregar Transacción" else "secondary"):
        st.session_state.pagina_actual = "➕ Agregar Transacción"
        st.rerun()
    
    st.markdown("#### 🤖 Inteligencia Artificial")
    
    if st.button("🔮 Predicciones IA", use_container_width=True,
                 type="primary" if st.session_state.pagina_actual == "🔮 Predicciones" else "secondary"):
        st.session_state.pagina_actual = "🔮 Predicciones"
        st.rerun()
    
    if st.button("🔍 Detector de Anomalías", use_container_width=True,
                 type="primary" if st.session_state.pagina_actual == "🔍 Anomalías" else "secondary"):
        st.session_state.pagina_actual = "🔍 Anomalías"
        st.rerun()
    
    if st.button("📊 Análisis Avanzado", use_container_width=True,
                 type="primary" if st.session_state.pagina_actual == "📊 Análisis Avanzado" else "secondary"):
        st.session_state.pagina_actual = "📊 Análisis Avanzado"
        st.rerun()
    
    st.markdown("#### 📄 Reportes y Gestión")
    
    if st.button("📑 Generar Reportes", use_container_width=True,
                 type="primary" if st.session_state.pagina_actual == "📑 Reportes" else "secondary"):
        st.session_state.pagina_actual = "📑 Reportes"
        st.rerun()
    
    if st.button("🔔 Ver Alertas", use_container_width=True,
                 type="primary" if st.session_state.pagina_actual == "🔔 Alertas" else "secondary"):
        st.session_state.pagina_actual = "🔔 Alertas"
        st.rerun()
    
    if st.button("💰 Presupuestos", use_container_width=True,
                 type="primary" if st.session_state.pagina_actual == "💰 Presupuestos" else "secondary"):
        st.session_state.pagina_actual = "💰 Presupuestos"
        st.rerun()
    
    st.markdown("---")
    
    # Resumen rápido
    st.markdown("### 📊 Resumen Rápido")
    df = cargar_datos()
    
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Transacciones", len(df), label_visibility="visible")
        
        with col2:
            balance = df[df['tipo']=='ingreso']['monto'].sum() - df[df['tipo']=='gasto']['monto'].sum()
            st.metric("Balance", f"${balance:,.0f}", label_visibility="visible")
        
        # Alertas pendientes
        try:
            reporte_alertas = sistema_alertas.generar_reporte_alertas()
            if reporte_alertas['total_alertas'] > 0:
                st.warning(f"⚠️ {reporte_alertas['total_alertas']} alertas")
        except:
            pass
    
    st.markdown("---")
    st.caption("v1.0.0 - Powered by IA")

# Enrutamiento basado en estado de sesión
pagina = st.session_state.pagina_actual

if "Dashboard" in pagina:
    pagina_dashboard()
elif "Agregar" in pagina:
    pagina_agregar_transaccion()
elif "Predicciones" in pagina:
    pagina_predicciones()
elif "Anomalías" in pagina:
    pagina_anomalias()
elif "Análisis" in pagina:
    pagina_analisis_avanzado()
elif "Reportes" in pagina:
    pagina_reportes()
elif "Alertas" in pagina:
    pagina_alertas()
elif "Presupuestos" in pagina:
    pagina_presupuestos()
else:
    pagina_dashboard()