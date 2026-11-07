import csv
from decimal import Decimal
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'

def rows(name):
    with (DATA / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

class Specification:
    def __init__(self, predicate): self.predicate = predicate
    def __call__(self, obj): return bool(self.predicate(obj))
    def __and__(self, other): return Specification(lambda x: self(x) and other(x))
    def __or__(self, other): return Specification(lambda x: self(x) or other(x))
    def __invert__(self): return Specification(lambda x: not self(x))

class DomainError(Exception): pass

TRANSITIONS = {'CREADO': {'aceptar':'ACEPTADO', 'cancelar':'CANCELADO'}, 'ACEPTADO': {'preparar':'EN_PREPARACION', 'cancelar':'CANCELADO'}, 'EN_PREPARACION': {'entregar':'ENTREGADO'}, 'ENTREGADO': {}, 'CANCELADO': {}}

class Store:
    def __init__(self):
        self.actors = {x['actor_id']:x for x in rows('actores.csv')}
        self.catalog = {x['recurso_id']:x for x in rows('catalogo.csv')}
        self.orders = {x['operacion_id']:dict(x) for x in rows('operaciones.csv')}
        self.details = {}
        for d in rows('detalle_operaciones.csv'):
            self.details.setdefault(d['operacion_id'], []).append(d)
        self.events = []
        self.active = Specification(lambda x: x['actor']['activo'] == '1')
        self.has_lines = Specification(lambda x: bool(x['lines']))
        self.authorized = Specification(lambda x: x['order']['autorizado'] == '1')
        self.vip = Specification(lambda x: x['actor']['es_preferente'] == '1')
        self.min_total = Specification(lambda x: x['total'] >= Decimal('1500'))
        self.no_promo = ~Specification(lambda x: x['order']['promocion_activa'] == '1')

    def context(self, oid):
        if oid not in self.orders: raise KeyError(oid)
        order = self.orders[oid]
        actor = self.actors.get(order['actor_id'])
        if actor is None: raise DomainError('Actor inexistente')
        lines = self.details.get(oid, [])
        total = Decimal('0')
        for line in lines:
            item = self.catalog.get(line['recurso_id'])
            if item is None: raise DomainError('Producto inexistente')
            qty = int(line['cantidad'])
            if qty <= 0: raise DomainError('Cantidad invalida')
            price = Decimal(item['precio_mxn'])
            if price < 0: raise DomainError('Precio invalido')
            total += price * qty
        return {'order':order, 'actor':actor, 'lines':lines, 'total':total}

    def validate(self, oid):
        ctx = self.context(oid)
        if not (self.active & self.has_lines & self.authorized)(ctx):
            raise DomainError('Cliente inactivo, pedido vacio o no autorizado')
        needed = {}
        for line in ctx['lines']:
            pid = line['recurso_id']
            needed[pid] = needed.get(pid, 0) + int(line['cantidad'])
        for pid, qty in needed.items():
            item = self.catalog[pid]
            if item['habilitado'] != '1' or qty > int(item['capacidad_o_stock']):
                raise DomainError('Producto no disponible o stock insuficiente')
        return ctx

    def benefit(self, oid):
        ctx = self.context(oid)
        return (self.vip & self.min_total & self.no_promo)(ctx)

    def transition(self, oid, action):
        self.validate(oid)
        order = self.orders[oid]
        before = order['estado_inicial']
        after = TRANSITIONS.get(before, {}).get(action)
        if after is None: raise DomainError(f'Transicion invalida: {before} -> {action}')
        order['estado_inicial'] = after
        event = {'type':'PedidoEstadoCambiado', 'operacion_id':oid, 'anterior':before, 'nuevo':after}
        self.events.append(event)
        return event
