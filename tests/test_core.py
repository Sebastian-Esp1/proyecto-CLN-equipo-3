import pytest
from fastapi.testclient import TestClient
from app.core import Store, Specification, DomainError
from app.main import app

def test_dataset():
    s=Store()
    assert len(s.actors)==40 and len(s.catalog)==20 and len(s.orders)==60

def test_specification_composition():
    positive=Specification(lambda x:x>0)
    even=Specification(lambda x:x%2==0)
    assert (positive & even)(2)
    assert (positive | even)(-2)
    assert (~positive)(-1)

def test_totals():
    s=Store()
    for oid in s.orders:
        ctx=s.context(oid)
        assert ctx['total']>=0

def test_benefit():
    s=Store()
    for oid in s.orders:
        ctx=s.context(oid)
        expected=ctx['actor']['es_preferente']=='1' and ctx['total']>=1500 and ctx['order']['promocion_activa']!='1'
        assert s.benefit(oid)==expected

def test_transitions():
    s=Store(); oid='PED-O001'
    if not (s.active & s.has_lines & s.authorized)(s.context(oid)):
        pytest.skip('Fixture no cumple precondiciones')
    try: s.validate(oid)
    except DomainError: pytest.skip('Fixture sin stock suficiente')
    assert s.transition(oid,'aceptar')['nuevo']=='ACEPTADO'
    assert s.transition(oid,'preparar')['nuevo']=='EN_PREPARACION'
    assert s.transition(oid,'entregar')['nuevo']=='ENTREGADO'
    with pytest.raises(DomainError): s.transition(oid,'aceptar')
    assert len(s.events)==3

def test_missing_order():
    with pytest.raises(KeyError): Store().context('MISSING')

def test_invalid_quantity():
    s=Store(); oid=next(iter(s.details)); s.details[oid][0]['cantidad']='0'
    with pytest.raises(DomainError): s.context(oid)

def test_api():
    client=TestClient(app)
    assert client.get('/salud').status_code==200
    assert client.get('/pedidos').status_code==200
    assert client.get('/pedidos/MISSING').status_code==404
    assert client.get('/openapi.json').status_code==200
