"""
API de Yoshi's World.

La API no guarda partidas: el frontend envía el estado completo en cada petición
y recibe el estado siguiente. Así funciona igual en local y en Vercel (serverless).

Endpoints:
    POST /api/partida/nueva            -> posiciones aleatorias, empieza la máquina
    POST /api/partida/jugada-humano    -> el rojo salta a una casilla
    POST /api/partida/jugada-maquina   -> el verde decide con minimax y salta
"""

from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from juego import (
    Estado, VERDE, ROJO,
    estado_inicial, movimientos, aplicar_movimiento, pasar_turno,
    es_terminal, contar_casillas, ganador,
)
from heuristica import detalle
from minimax import decidir, PROFUNDIDAD_POR_NIVEL

app = FastAPI(title="Yoshi's World API")


# ---------------------------------------------------------------------------
# Modelos de entrada y salida (lo que viaja en JSON)
# ---------------------------------------------------------------------------
class EstadoJSON(BaseModel):
    tablero: list[list[int]]   # 0 libre, 1 verde, 2 rojo
    verde: tuple[int, int]
    rojo: tuple[int, int]
    turno: int                 # 1 verde, 2 rojo


class NuevaPartida(BaseModel):
    semilla: Optional[int] = None


class JugadaHumano(BaseModel):
    estado: EstadoJSON
    jugada: tuple[int, int]


class JugadaMaquina(BaseModel):
    estado: EstadoJSON
    nivel: Literal["principiante", "amateur", "experto"] = "principiante"
    poda: bool = True


# ---------------------------------------------------------------------------
# Conversión entre el JSON y la clase Estado del juego
# ---------------------------------------------------------------------------
def desde_json(datos: EstadoJSON):
    return Estado(
        tablero=[fila[:] for fila in datos.tablero],
        verde=tuple(datos.verde),
        rojo=tuple(datos.rojo),
        turno=datos.turno,
    )


def a_json(estado):
    return {
        "tablero": estado.tablero,
        "verde": list(estado.verde),
        "rojo": list(estado.rojo),
        "turno": estado.turno,
    }


def respuesta_partida(estado, pase=None):
    """Todo lo que la interfaz necesita para dibujar el turno actual."""
    terminado = es_terminal(estado)
    return {
        "estado": a_json(estado),
        "casillas_verde": contar_casillas(estado, VERDE),
        "casillas_rojo": contar_casillas(estado, ROJO),
        "movimientos": [] if terminado else [list(c) for c in movimientos(estado, estado.turno)],
        "terminado": terminado,
        "ganador": ganador(estado) if terminado else None,
        "pase": pase,  # "verde" o "rojo" si ese jugador se quedó sin saltos y perdió el turno
        "heuristica": detalle(estado),
    }


def resolver_turno(estado):
    """
    Después de una jugada el turno pasa al rival. Si el rival no tiene saltos
    (y la partida no ha terminado) el turno vuelve al jugador que acaba de mover.
    """
    if es_terminal(estado):
        return respuesta_partida(estado)

    if not movimientos(estado, estado.turno):
        quien_pasa = "verde" if estado.turno == VERDE else "rojo"
        return respuesta_partida(pasar_turno(estado), pase=quien_pasa)

    return respuesta_partida(estado)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/salud")
def salud():
    return {"ok": True}


@app.post("/api/partida/nueva")
def nueva_partida(datos: NuevaPartida):
    estado = estado_inicial(datos.semilla)
    return resolver_turno(estado)


@app.post("/api/partida/jugada-humano")
def jugada_humano(datos: JugadaHumano):
    estado = desde_json(datos.estado)
    jugada = tuple(datos.jugada)

    if estado.turno != ROJO:
        raise HTTPException(400, "No es el turno del jugador rojo.")
    if jugada not in movimientos(estado, ROJO):
        raise HTTPException(400, "Esa casilla no es un salto de caballo libre.")

    nuevo = aplicar_movimiento(estado, jugada)
    return resolver_turno(nuevo)


@app.post("/api/partida/jugada-maquina")
def jugada_maquina(datos: JugadaMaquina):
    estado = desde_json(datos.estado)

    if estado.turno != VERDE:
        raise HTTPException(400, "No es el turno de la máquina.")
    if not movimientos(estado, VERDE):
        raise HTTPException(400, "La máquina no tiene saltos disponibles.")

    profundidad = PROFUNDIDAD_POR_NIVEL[datos.nivel]
    decision = decidir(estado, profundidad, usar_poda=datos.poda)

    nuevo = aplicar_movimiento(estado, decision["jugada"])
    return {
        "partida": resolver_turno(nuevo),
        "decision": {
            **decision,
            "nivel": datos.nivel,
            "jugada": list(decision["jugada"]),
            "candidatos": [
                {"jugada": list(c["jugada"]), "valor": c["valor"], "exacto": c["exacto"]}
                for c in decision["candidatos"]
            ],
        },
    }
