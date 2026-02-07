"""
Modelos de base de datos para el gestor financiero
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.settings import DATABASE_URL
from src.utils.logger import logger

Base = declarative_base()

class Transaccion(Base):
    """Modelo para transacciones (gastos e ingresos)"""
    __tablename__ = 'transacciones'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String(10), nullable=False)  # 'ingreso' o 'gasto'
    fecha = Column(DateTime, nullable=False, default=datetime.now)
    monto = Column(Float, nullable=False)
    categoria = Column(String(50), nullable=False)
    subcategoria = Column(String(50), nullable=True)
    metodo_pago = Column(String(50), nullable=False)
    motivo = Column(Text, nullable=True)
    notas = Column(Text, nullable=True)
    es_recurrente = Column(Integer, default=0)  # 0=No, 1=Sí
    creado_en = Column(DateTime, default=datetime.now)
    actualizado_en = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Transaccion(id={self.id}, tipo={self.tipo}, monto={self.monto}, categoria={self.categoria})>"
    
    def to_dict(self):
        """Convierte la transacción a diccionario"""
        return {
            'id': self.id,
            'tipo': self.tipo,
            'fecha': self.fecha.strftime('%Y-%m-%d %H:%M:%S'),
            'monto': self.monto,
            'categoria': self.categoria,
            'subcategoria': self.subcategoria,
            'metodo_pago': self.metodo_pago,
            'motivo': self.motivo,
            'notas': self.notas,
            'es_recurrente': bool(self.es_recurrente)
        }

class Presupuesto(Base):
    """Modelo para presupuestos por categoría"""
    __tablename__ = 'presupuestos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    categoria = Column(String(50), nullable=False, unique=True)
    monto_mensual = Column(Float, nullable=False)
    alerta_porcentaje = Column(Float, default=80.0)  # Alerta al 80%
    activo = Column(Integer, default=1)
    creado_en = Column(DateTime, default=datetime.now)
    actualizado_en = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Presupuesto(categoria={self.categoria}, monto={self.monto_mensual})>"

class DatabaseManager:
    """Gestor de base de datos"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.create_tables()
        logger.info("✅ Base de datos inicializada")
    
    def create_tables(self):
        """Crea las tablas en la base de datos"""
        Base.metadata.create_all(self.engine)
        logger.info("✅ Tablas creadas correctamente")
    
    def get_session(self):
        """Retorna una nueva sesión de base de datos"""
        return self.Session()
    
    def agregar_transaccion(self, tipo, fecha, monto, categoria, subcategoria=None, 
                           metodo_pago="Efectivo", motivo=None, notas=None, es_recurrente=False):
        """
        Agrega una nueva transacción a la base de datos
        
        Args:
            tipo: 'ingreso' o 'gasto'
            fecha: datetime object
            monto: float
            categoria: str
            subcategoria: str opcional
            metodo_pago: str
            motivo: str opcional
            notas: str opcional
            es_recurrente: bool
            
        Returns:
            ID de la transacción creada
        """
        session = self.get_session()
        try:
            transaccion = Transaccion(
                tipo=tipo,
                fecha=fecha,
                monto=monto,
                categoria=categoria,
                subcategoria=subcategoria,
                metodo_pago=metodo_pago,
                motivo=motivo,
                notas=notas,
                es_recurrente=1 if es_recurrente else 0
            )
            session.add(transaccion)
            session.commit()
            transaccion_id = transaccion.id
            logger.info(f"✅ Transacción agregada: {tipo} - ${monto} - {categoria}")
            return transaccion_id
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error al agregar transacción: {e}")
            raise
        finally:
            session.close()
    
    def obtener_todas_transacciones(self):
        """Retorna todas las transacciones"""
        session = self.get_session()
        try:
            return session.query(Transaccion).order_by(Transaccion.fecha.desc()).all()
        finally:
            session.close()
    
    def obtener_transacciones_por_tipo(self, tipo):
        """Retorna transacciones filtradas por tipo"""
        session = self.get_session()
        try:
            return session.query(Transaccion).filter(
                Transaccion.tipo == tipo
            ).order_by(Transaccion.fecha.desc()).all()
        finally:
            session.close()
    
    def obtener_transacciones_por_fecha(self, fecha_inicio, fecha_fin):
        """Retorna transacciones en un rango de fechas"""
        session = self.get_session()
        try:
            return session.query(Transaccion).filter(
                Transaccion.fecha >= fecha_inicio,
                Transaccion.fecha <= fecha_fin
            ).order_by(Transaccion.fecha.desc()).all()
        finally:
            session.close()
    
    def eliminar_transaccion(self, transaccion_id):
        """Elimina una transacción por ID"""
        session = self.get_session()
        try:
            transaccion = session.query(Transaccion).filter(
                Transaccion.id == transaccion_id
            ).first()
            if transaccion:
                session.delete(transaccion)
                session.commit()
                logger.info(f"✅ Transacción {transaccion_id} eliminada")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error al eliminar transacción: {e}")
            raise
        finally:
            session.close()

# Instancia global
db_manager = DatabaseManager()