# Sazón Urbano — PIA de Componentes de Lógica de Negocio

Implementación de referencia a partir de los CSV proporcionados. **No reemplaza el BRD ni los diagramas U2/U3 del equipo.** La persistencia actual es en memoria: el servicio PostgreSQL del Compose está preparado pero aún no está integrado a la aplicación.

## Ejecutar

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: http://localhost:8000/docs

Pruebas: `pytest -q --cov=app --cov-report=term-missing`

Docker: `docker compose up --build app` y `docker compose run --rm tests`.

## Reglas de referencia

- Procesar: actor activo AND pedido con líneas AND autorizado.
- Beneficio: preferente AND total >= 1500 MXN AND NOT promoción activa.
- Inventario: cantidades positivas, productos habilitados, stock suficiente.
- Estados: CREADO -> ACEPTADO -> EN_PREPARACION -> ENTREGADO; cancelación desde CREADO o ACEPTADO.
- Eventos de dominio: PedidoEstadoCambiado.

## Endpoints

`GET /salud`, `GET /pedidos`, `GET /pedidos/{id}`, `GET /pedidos/{id}/validacion`, `GET /pedidos/{id}/beneficio`, `POST /pedidos/{id}/transiciones` (JSON `{"accion":"aceptar"}`).

## Pendiente para conformidad con PIA oficial

Integrar reglas reales del BRD, al menos 15 historias Gherkin, BPMN, DDD/UML, matriz de trazabilidad real, persistencia en base de datos, pruebas de todos los casos CSV y evidencia de cobertura >=80%. No se afirma cumplimiento completo sin estas evidencias.
