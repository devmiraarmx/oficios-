"""Modelos SQLAlchemy — traducción del modelo de datos del CLAUDE.md.

Tablas principales del negocio:
    profesionales, solicitudes, desbloqueos, movimientos_credito, resenas

Catálogos de apoyo (necesarios para las landing pages SEO oficio × ciudad
y para el filtrado del directorio):
    oficios, zonas, y las asociaciones profesional_oficios / profesional_zonas

Convenciones:
    - Nombres de tablas y columnas en español, como el resto del proyecto.
    - Montos de crédito son enteros (un crédito = un lead desbloqueado).
"""
import secrets
from datetime import datetime
from enum import Enum

from app.extensions import db


def _nuevo_token() -> str:
    """Token de acceso del profesional (enlace mágico, sin login/contraseña)."""
    return secrets.token_urlsafe(16)


# --------------------------------------------------------------------------
# Enumeraciones
# --------------------------------------------------------------------------
class EstadoProfesional(str, Enum):
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"


class OrigenProfesional(str, Enum):
    AUTORREGISTRO = "autorregistro"      # llegó por el formulario público
    AGREGADO_MANUAL = "agregado_manual"  # lo dio de alta un socio (su red)


class TipoMovimiento(str, Enum):
    COMPRA = "compra"      # el profesional recarga créditos
    CONSUMO = "consumo"    # se descuenta un crédito al desbloquear un lead


class Urgencia(str, Enum):
    HOY = "hoy"
    ESTA_SEMANA = "esta_semana"
    SIN_PRISA = "sin_prisa"


# --------------------------------------------------------------------------
# Tablas de asociación (un profesional cubre varios oficios y varias zonas)
# --------------------------------------------------------------------------
profesional_oficios = db.Table(
    "profesional_oficios",
    db.Column("profesional_id", db.ForeignKey("profesionales.id"), primary_key=True),
    db.Column("oficio_id", db.ForeignKey("oficios.id"), primary_key=True),
)

profesional_zonas = db.Table(
    "profesional_zonas",
    db.Column("profesional_id", db.ForeignKey("profesionales.id"), primary_key=True),
    db.Column("zona_id", db.ForeignKey("zonas.id"), primary_key=True),
)


# --------------------------------------------------------------------------
# Catálogos
# --------------------------------------------------------------------------
class Oficio(db.Model):
    """Catálogo curado de oficios (plomero, electricista, albañil...).
    El `slug` alimenta las URLs SEO: /oficio/plomero/...
    """
    __tablename__ = "oficios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False, unique=True)
    slug = db.Column(db.String(80), nullable=False, unique=True, index=True)

    def __repr__(self) -> str:
        return f"<Oficio {self.slug}>"


class Zona(db.Model):
    """Catálogo de zonas/colonias/ciudades (Coyoacán, Cancún...).
    `slug` alimenta las URLs SEO: /oficio/plomero/coyoacan
    `ciudad` agrupa zonas para el arranque en CDMX y Cancún.
    """
    __tablename__ = "zonas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), nullable=False, unique=True, index=True)
    ciudad = db.Column(db.String(80), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Zona {self.slug}>"


# --------------------------------------------------------------------------
# Tablas principales
# --------------------------------------------------------------------------
class Profesional(db.Model):
    __tablename__ = "profesionales"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    # Zona de cobertura en texto libre para el alta rápida; la relación
    # normalizada con `zonas` alimenta el filtrado y el SEO.
    zona = db.Column(db.String(120))
    anios_experiencia = db.Column(db.Integer, default=0)
    estado = db.Column(
        db.Enum(EstadoProfesional, values_callable=lambda e: [x.value for x in e]),
        default=EstadoProfesional.PENDIENTE,
        nullable=False,
        index=True,
    )
    saldo_creditos = db.Column(db.Integer, default=0, nullable=False)
    foto_url = db.Column(db.String(300))
    descripcion = db.Column(db.Text)
    telefono_referencia = db.Column(db.String(20))
    # Cómo entró al directorio. Los agregados manualmente por un socio (su red
    # de contactos) entran directo con estado = aprobado, sin llamada.
    origen = db.Column(
        db.Enum(OrigenProfesional, values_callable=lambda e: [x.value for x in e]),
        default=OrigenProfesional.AUTORREGISTRO,
        nullable=False,
    )
    # Enlace mágico: da acceso a la bandeja de leads sin login ni contraseña.
    token_acceso = db.Column(
        db.String(43), unique=True, index=True, nullable=False, default=_nuevo_token
    )
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    oficios = db.relationship("Oficio", secondary=profesional_oficios, backref="profesionales")
    zonas = db.relationship("Zona", secondary=profesional_zonas, backref="profesionales")
    desbloqueos = db.relationship("Desbloqueo", back_populates="profesional")
    movimientos = db.relationship("MovimientoCredito", back_populates="profesional")
    resenas = db.relationship("Resena", back_populates="profesional")

    @property
    def aprobado(self) -> bool:
        return self.estado == EstadoProfesional.APROBADO

    @property
    def calificacion_promedio(self) -> float | None:
        if not self.resenas:
            return None
        return round(sum(r.calificacion for r in self.resenas) / len(self.resenas), 1)

    def __repr__(self) -> str:
        return f"<Profesional {self.id} {self.nombre} ({self.estado.value})>"


class Solicitud(db.Model):
    __tablename__ = "solicitudes"

    id = db.Column(db.Integer, primary_key=True)
    oficio = db.Column(db.String(80), nullable=False, index=True)
    zona = db.Column(db.String(120), nullable=False, index=True)
    descripcion = db.Column(db.Text, nullable=False)
    urgencia = db.Column(
        db.Enum(Urgencia, values_callable=lambda e: [x.value for x in e]),
        default=Urgencia.SIN_PRISA,
    )
    nombre_cliente = db.Column(db.String(120))
    telefono_cliente = db.Column(db.String(20), nullable=False)
    # Un lead solo cuenta como válido cuando el teléfono está verificado (SMS).
    telefono_verificado = db.Column(db.Boolean, default=False, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    desbloqueos = db.relationship("Desbloqueo", back_populates="solicitud")

    def __repr__(self) -> str:
        return f"<Solicitud {self.id} {self.oficio}@{self.zona}>"


class Desbloqueo(db.Model):
    """Cada compra de lead: un profesional desbloquea el contacto de una
    solicitud. Es la tabla que mide el negocio.
    """
    __tablename__ = "desbloqueos"

    id = db.Column(db.Integer, primary_key=True)
    profesional_id = db.Column(db.ForeignKey("profesionales.id"), nullable=False, index=True)
    solicitud_id = db.Column(db.ForeignKey("solicitudes.id"), nullable=False, index=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    profesional = db.relationship("Profesional", back_populates="desbloqueos")
    solicitud = db.relationship("Solicitud", back_populates="desbloqueos")

    __table_args__ = (
        # Un profesional no paga dos veces por el mismo lead.
        db.UniqueConstraint("profesional_id", "solicitud_id", name="uq_desbloqueo_prof_sol"),
    )

    def __repr__(self) -> str:
        return f"<Desbloqueo prof={self.profesional_id} sol={self.solicitud_id}>"


class MovimientoCredito(db.Model):
    """Historial completo del saldo, para auditoría. `cantidad` es positiva;
    el signo lo determina `tipo` (compra suma, consumo resta).
    """
    __tablename__ = "movimientos_credito"

    id = db.Column(db.Integer, primary_key=True)
    profesional_id = db.Column(db.ForeignKey("profesionales.id"), nullable=False, index=True)
    tipo = db.Column(
        db.Enum(TipoMovimiento, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    cantidad = db.Column(db.Integer, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    profesional = db.relationship("Profesional", back_populates="movimientos")

    def __repr__(self) -> str:
        return f"<MovimientoCredito {self.tipo.value} {self.cantidad}>"


class Resena(db.Model):
    __tablename__ = "resenas"

    id = db.Column(db.Integer, primary_key=True)
    profesional_id = db.Column(db.ForeignKey("profesionales.id"), nullable=False, index=True)
    calificacion = db.Column(db.Integer, nullable=False)  # 1..5 estrellas
    comentario = db.Column(db.Text)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    profesional = db.relationship("Profesional", back_populates="resenas")

    def __repr__(self) -> str:
        return f"<Resena prof={self.profesional_id} {self.calificacion}★>"
