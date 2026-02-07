"""
Generador de datos de prueba para el gestor financiero
"""
import random
from datetime import datetime, timedelta
import pandas as pd
from config.settings import CATEGORIAS_GASTOS, CATEGORIAS_INGRESOS, METODOS_PAGO
from src.utils.database import db_manager
from src.utils.logger import logger

class DataGenerator:
    """Generador de datos financieros de prueba"""
    
    def __init__(self):
        self.subcategorias = {
            "Alimentación": ["Supermercado", "Restaurante", "Comida rápida", "Cafetería"],
            "Transporte": ["Gasolina", "Taxi/Uber", "Transporte público", "Mantenimiento"],
            "Vivienda": ["Alquiler", "Hipoteca", "Mantenimiento", "Muebles"],
            "Servicios": ["Luz", "Agua", "Internet", "Teléfono", "Gas"],
            "Salud": ["Médico", "Farmacia", "Gimnasio", "Seguro"],
            "Entretenimiento": ["Cine", "Streaming", "Videojuegos", "Salidas"],
            "Educación": ["Cursos", "Libros", "Material", "Matrícula"],
            "Ropa": ["Ropa casual", "Ropa formal", "Zapatos", "Accesorios"],
            "Tecnología": ["Software", "Hardware", "Accesorios", "Reparaciones"],
            "Otros": ["Regalos", "Donaciones", "Varios"]
        }
        
        self.motivos_gastos = {
            "Alimentación": [
                "Compra semanal del supermercado",
                "Almuerzo en restaurante",
                "Café con amigos",
                "Cena familiar",
                "Compra de snacks"
            ],
            "Transporte": [
                "Recarga de combustible",
                "Viaje en Uber al trabajo",
                "Boleto de transporte público",
                "Cambio de aceite del auto"
            ],
            "Servicios": [
                "Pago de recibo de luz",
                "Pago de internet mensual",
                "Recarga de celular"
            ],
            "Salud": [
                "Consulta médica",
                "Compra de medicamentos",
                "Pago de gimnasio mensual"
            ],
            "Entretenimiento": [
                "Boletos de cine",
                "Suscripción Netflix",
                "Salida nocturna"
            ]
        }
        
        self.motivos_ingresos = {
            "Salario": ["Pago de nómina mensual", "Pago quincenal"],
            "Freelance": ["Pago por proyecto web", "Consultoría", "Diseño gráfico"],
            "Inversiones": ["Dividendos", "Rendimientos", "Venta de acciones"],
            "Bonos": ["Bono de productividad", "Aguinaldo", "Comisión por ventas"]
        }
    
    def generar_datos_prueba(self, dias=90, transacciones_por_dia=(2, 8)):
        """
        Genera datos de prueba realistas
        
        Args:
            dias: Número de días hacia atrás
            transacciones_por_dia: Tupla (min, max) de transacciones por día
        """
        logger.info(f"🔄 Generando datos de prueba para {dias} días...")
        
        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=dias)
        
        total_transacciones = 0
        
        # Generar ingresos mensuales (salario)
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            # Salario el día 1 y 15 de cada mes
            if fecha_actual.day == 1:
                monto = random.uniform(3000, 5000)
                db_manager.agregar_transaccion(
                    tipo="ingreso",
                    fecha=fecha_actual + timedelta(hours=random.randint(8, 10)),
                    monto=round(monto, 2),
                    categoria="Salario",
                    subcategoria=None,
                    metodo_pago="Transferencia",
                    motivo="Pago de nómina mensual",
                    es_recurrente=True
                )
                total_transacciones += 1
            
            # Ingresos adicionales aleatorios
            if random.random() < 0.1:  # 10% de probabilidad
                categoria = random.choice(["Freelance", "Bonos", "Inversiones"])
                monto = random.uniform(200, 1500)
                motivo = random.choice(self.motivos_ingresos.get(categoria, ["Ingreso adicional"]))
                
                db_manager.agregar_transaccion(
                    tipo="ingreso",
                    fecha=fecha_actual + timedelta(hours=random.randint(8, 20)),
                    monto=round(monto, 2),
                    categoria=categoria,
                    metodo_pago=random.choice(["Transferencia", "PayPal"]),
                    motivo=motivo
                )
                total_transacciones += 1
            
            fecha_actual += timedelta(days=1)
        
        # Generar gastos diarios
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            num_transacciones = random.randint(*transacciones_por_dia)
            
            for _ in range(num_transacciones):
                categoria = random.choice(CATEGORIAS_GASTOS)
                subcategoria = random.choice(self.subcategorias.get(categoria, [None]))
                
                # Montos realistas según categoría
                rangos_monto = {
                    "Alimentación": (10, 150),
                    "Transporte": (5, 100),
                    "Vivienda": (500, 1500),
                    "Servicios": (20, 200),
                    "Salud": (30, 300),
                    "Entretenimiento": (15, 200),
                    "Educación": (50, 500),
                    "Ropa": (30, 300),
                    "Tecnología": (50, 1000),
                    "Otros": (10, 200)
                }
                
                monto_min, monto_max = rangos_monto.get(categoria, (10, 100))
                monto = random.uniform(monto_min, monto_max)
                
                # Motivo realista
                motivos = self.motivos_gastos.get(categoria, [f"Gasto en {categoria.lower()}"])
                motivo = random.choice(motivos)
                
                # Método de pago con distribución realista
                if monto > 500:
                    metodo = random.choice(["Tarjeta de Crédito", "Transferencia"])
                elif monto > 100:
                    metodo = random.choice(["Tarjeta de Débito", "Tarjeta de Crédito"])
                else:
                    metodo = random.choice(METODOS_PAGO)
                
                # Hora realista del día
                hora = random.randint(6, 23)
                minuto = random.randint(0, 59)
                
                db_manager.agregar_transaccion(
                    tipo="gasto",
                    fecha=fecha_actual + timedelta(hours=hora, minutes=minuto),
                    monto=round(monto, 2),
                    categoria=categoria,
                    subcategoria=subcategoria,
                    metodo_pago=metodo,
                    motivo=motivo,
                    es_recurrente=(categoria in ["Servicios", "Vivienda"] and random.random() < 0.3)
                )
                total_transacciones += 1
            
            fecha_actual += timedelta(days=1)
        
        logger.info(f"✅ Generadas {total_transacciones} transacciones de prueba")
        return total_transacciones
    
    def limpiar_datos(self):
        """Elimina todos los datos de la base de datos"""
        from src.utils.database import Transaccion, Presupuesto
        session = db_manager.get_session()
        try:
            session.query(Transaccion).delete()
            session.query(Presupuesto).delete()
            session.commit()
            logger.info("✅ Base de datos limpiada")
        finally:
            session.close()

# Instancia global
data_generator = DataGenerator()

if __name__ == "__main__":
    # Limpiar y generar datos de prueba
    data_generator.limpiar_datos()
    data_generator.generar_datos_prueba(dias=180)