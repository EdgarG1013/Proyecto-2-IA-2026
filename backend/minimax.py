"""
Minimax con decisiones imperfectas, con y sin poda alfa-beta (informe, secciones 7 y 8).

- El VERDE (máquina) es MAX y el ROJO (humano) es MIN.
- La profundidad se cuenta en jugadas individuales: profundidad 2 = mueve el verde
  y responde el rojo.
- Regla del pase: si el jugador en turno no tiene saltos pero el rival sí, se genera
  un único hijo "pase" que consume un nivel del árbol.
- Cuando se llega a la profundidad límite, el estado se valora con la heurística h.
"""

import time

from juego import VERDE, rival, movimientos, aplicar_movimiento, pasar_turno, es_terminal
from heuristica import h, utilidad

INFINITO = float("inf")

PROFUNDIDAD_POR_NIVEL = {
    "principiante": 2,
    "amateur": 4,
    "experto": 6,
}


def nuevas_estadisticas():
    # nodos: estados visitados, hojas: estados evaluados, podas: veces que se cortó una rama
    return {"nodos": 0, "hojas": 0, "podas": 0}


def generar_hijos(estado):
    """
    Lista de (jugada, estado_hijo) del jugador en turno.
    Si no tiene saltos, el único hijo es el pase (jugada = None).
    """
    hijos = []
    for casilla in movimientos(estado, estado.turno):
        hijos.append((casilla, aplicar_movimiento(estado, casilla)))
    if not hijos:
        hijos.append((None, pasar_turno(estado)))
    return hijos


def ordenar_hijos(hijos, jugador):
    """
    Ordenamiento de movimientos para que la poda corte más (informe, sección 8.3):
    primero los hijos donde el jugador que movió queda con más saltos que su rival.
    El orden nunca cambia la decisión, solo cuántas ramas se podan.
    """
    def ventaja_de_movilidad(hijo):
        _, estado_hijo = hijo
        return len(movimientos(estado_hijo, jugador)) - len(movimientos(estado_hijo, rival(jugador)))

    return sorted(hijos, key=ventaja_de_movilidad, reverse=True)


# ---------------------------------------------------------------------------
# Minimax sin poda
# ---------------------------------------------------------------------------
def minimax(estado, profundidad, estadisticas):
    estadisticas["nodos"] += 1

    if es_terminal(estado):
        estadisticas["hojas"] += 1
        return utilidad(estado)
    if profundidad == 0:
        estadisticas["hojas"] += 1
        return h(estado)

    es_max = estado.turno == VERDE

    if es_max:
        valor = -INFINITO
        for _, hijo in generar_hijos(estado):
            valor = max(valor, minimax(hijo, profundidad - 1, estadisticas))
    else:
        valor = INFINITO
        for _, hijo in generar_hijos(estado):
            valor = min(valor, minimax(hijo, profundidad - 1, estadisticas))

    return valor


# ---------------------------------------------------------------------------
# Minimax con poda alfa-beta
# ---------------------------------------------------------------------------
def alfabeta(estado, profundidad, alfa, beta, estadisticas, ordenar=True):
    """
    alfa: mejor valor que MAX ya tiene garantizado en el camino actual.
    beta: mejor valor que MIN ya tiene garantizado en el camino actual.
    Si alfa >= beta, los hermanos restantes no pueden cambiar la decisión: se podan.
    """
    estadisticas["nodos"] += 1

    if es_terminal(estado):
        estadisticas["hojas"] += 1
        return utilidad(estado)
    if profundidad == 0:
        estadisticas["hojas"] += 1
        return h(estado)

    es_max = estado.turno == VERDE
    hijos = generar_hijos(estado)
    if ordenar:
        hijos = ordenar_hijos(hijos, estado.turno)

    if es_max:
        valor = -INFINITO
        for _, hijo in hijos:
            valor = max(valor, alfabeta(hijo, profundidad - 1, alfa, beta, estadisticas, ordenar))
            alfa = max(alfa, valor)
            if alfa >= beta:
                estadisticas["podas"] += 1
                break  # poda beta
    else:
        valor = INFINITO
        for _, hijo in hijos:
            valor = min(valor, alfabeta(hijo, profundidad - 1, alfa, beta, estadisticas, ordenar))
            beta = min(beta, valor)
            if alfa >= beta:
                estadisticas["podas"] += 1
                break  # poda alfa

    return valor


# ---------------------------------------------------------------------------
# Decisión de la máquina
# ---------------------------------------------------------------------------
def decidir(estado, profundidad, usar_poda=True, ordenar=True):
    """
    Escoge la jugada del VERDE que maximiza el valor minimax de sus hijos.

    Devuelve un diccionario con la jugada elegida, su valor, el valor de cada
    jugada candidata y las estadísticas de la búsqueda (para el informe y la interfaz).
    """
    inicio = time.perf_counter()
    estadisticas = nuevas_estadisticas()
    estadisticas["nodos"] += 1  # la raíz

    hijos = generar_hijos(estado)
    if usar_poda and ordenar:
        hijos = ordenar_hijos(hijos, estado.turno)

    mejor_jugada = None
    mejor_valor = -INFINITO
    alfa = -INFINITO
    candidatos = []

    for jugada, hijo in hijos:
        if usar_poda:
            valor = alfabeta(hijo, profundidad - 1, alfa, INFINITO, estadisticas, ordenar)
            # Con poda, si el valor no supera a alfa solo sabemos que vale "como mucho" eso.
            exacto = valor > alfa or alfa == -INFINITO
        else:
            valor = minimax(hijo, profundidad - 1, estadisticas)
            exacto = True

        candidatos.append({"jugada": jugada, "valor": valor, "exacto": exacto})

        if valor > mejor_valor:
            mejor_valor = valor
            mejor_jugada = jugada
        alfa = max(alfa, mejor_valor)

    tiempo_ms = (time.perf_counter() - inicio) * 1000

    return {
        "jugada": mejor_jugada,
        "valor": mejor_valor,
        "candidatos": candidatos,
        "profundidad": profundidad,
        "poda": usar_poda,
        "nodos": estadisticas["nodos"],
        "hojas": estadisticas["hojas"],
        "podas": estadisticas["podas"],
        "tiempo_ms": round(tiempo_ms, 1),
    }
