from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .core import Store, DomainError

app = FastAPI(title='Sazon Urbano PIA', version='1.0.0')
store = Store()

class Action(BaseModel):
    accion: str

def execute(fn):
    try: return fn()
    except KeyError: raise HTTPException(404, 'Pedido no encontrado')
    except (DomainError, ValueError) as e: raise HTTPException(422, str(e))

@app.get('/salud')
def health(): return {'estado':'ok'}

@app.get('/pedidos')
def orders(): return list(store.orders.values())

@app.get('/pedidos/{oid}')
def order(oid: str):
    def result():
        ctx = store.context(oid)
        return {'pedido':ctx['order'], 'detalle':ctx['lines'], 'total_mxn':str(ctx['total'])}
    return execute(result)

@app.get('/pedidos/{oid}/validacion')
def validation(oid: str):
    return execute(lambda: {'valido':bool(store.validate(oid))})

@app.get('/pedidos/{oid}/beneficio')
def benefit(oid: str):
    return execute(lambda: {'aplica':store.benefit(oid)})

@app.post('/pedidos/{oid}/transiciones')
def transition(oid: str, body: Action):
    try: return store.transition(oid, body.accion)
    except KeyError: raise HTTPException(404, 'Pedido no encontrado')
    except DomainError as e:
        code = 409 if 'Transicion invalida' in str(e) else 422
        raise HTTPException(code, str(e))
