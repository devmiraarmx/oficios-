"""Lógica de negocio del flujo de leads y créditos.

Se mantiene fuera de las vistas para que las rutas queden delgadas y la
operación de desbloqueo (cobro de un crédito) sea una sola transacción
atómica, fácil de razonar y de probar.
"""
from app.extensions import db
from app.models import (
    Desbloqueo,
    MovimientoCredito,
    Solicitud,
    TipoMovimiento,
)


class CreditosInsuficientes(Exception):
    """El profesional no tiene saldo suficiente para desbloquear el lead."""


def desbloquear_lead(profesional, solicitud, creditos_por_lead: int = 1):
    """Desbloquea el contacto de una solicitud para un profesional.

    - Idempotente: si ya lo había desbloqueado, NO se cobra de nuevo.
    - Atómico: el registro del desbloqueo, el movimiento de crédito y el
      descuento del saldo se confirman juntos.

    Devuelve (desbloqueo, cobrado) donde `cobrado` indica si se descontó
    un crédito en esta llamada.
    """
    existente = Desbloqueo.query.filter_by(
        profesional_id=profesional.id, solicitud_id=solicitud.id
    ).first()
    if existente:
        return existente, False

    if profesional.saldo_creditos < creditos_por_lead:
        raise CreditosInsuficientes()

    desbloqueo = Desbloqueo(profesional_id=profesional.id, solicitud_id=solicitud.id)
    db.session.add(desbloqueo)
    profesional.saldo_creditos -= creditos_por_lead
    db.session.add(
        MovimientoCredito(
            profesional_id=profesional.id,
            tipo=TipoMovimiento.CONSUMO,
            cantidad=creditos_por_lead,
        )
    )
    db.session.commit()
    return desbloqueo, True


def acreditar_compra(profesional, cantidad: int):
    """Suma créditos al saldo del profesional y registra el movimiento.

    Lo llama el flujo de compra una vez confirmado el pago. Mientras la
    pasarela (Stripe/Conekta) no está conectada, lo dispara la compra
    simulada del MVP.
    """
    profesional.saldo_creditos += cantidad
    db.session.add(
        MovimientoCredito(
            profesional_id=profesional.id,
            tipo=TipoMovimiento.COMPRA,
            cantidad=cantidad,
        )
    )
    db.session.commit()


def ids_desbloqueadas(profesional) -> set[int]:
    """IDs de solicitudes que el profesional ya desbloqueó (para no volver a
    cobrar y para mostrar el contacto directamente)."""
    return {d.solicitud_id for d in profesional.desbloqueos}


def leads_para(profesional):
    """Solicitudes que son leads válidos para este profesional:
    teléfono verificado y coincidencia por oficio y zona.

    El matching es laxo a propósito (nombres normalizados, contención en la
    zona) porque oficio/zona de la solicitud son texto libre del cliente.
    """
    nombres_oficio = {o.nombre.strip().lower() for o in profesional.oficios}
    nombres_zona = {z.nombre.strip().lower() for z in profesional.zonas}
    if profesional.zona:
        nombres_zona.add(profesional.zona.strip().lower())

    candidatas = (
        Solicitud.query.filter_by(telefono_verificado=True)
        .order_by(Solicitud.creado_en.desc())
        .all()
    )

    leads = []
    for s in candidatas:
        oficio_s = (s.oficio or "").strip().lower()
        zona_s = (s.zona or "").strip().lower()
        if nombres_oficio and oficio_s not in nombres_oficio:
            continue
        if nombres_zona and not any(z in zona_s or zona_s in z for z in nombres_zona):
            continue
        leads.append(s)
    return leads
