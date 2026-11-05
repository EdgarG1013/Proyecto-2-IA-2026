"""
Función de evaluación heurística.

Todas las funciones se calculan desde el punto de vista del VERDE (la máquina):
un valor positivo es bueno para la máquina y uno negativo es bueno para el humano.

    f1 = (casillas verdes - casillas rojas) / 64        -> el presente
    f2 = (saltos del verde - saltos del rojo) / 8        -> el corto plazo (un salto)

    h(s) = w1*f1 + w2*f2                                  (estados no terminales)
    U(s) = 1000*signo(D) + D                              (estados terminales)

Las dos componentes miran a lo sumo un salto adelante. Así la máquina solo "ve el
futuro" a través de la profundidad del árbol, y la dificultad crece con el nivel:
en principiante (profundidad 2) puede escoger un salto bueno ahora que la deja
acorralada más adelante.
"""

from juego import TOTAL_CASILLAS, VERDE, ROJO, movimientos, contar_casillas, es_terminal

# Pesos w1, w2: no negativos, suman 1 y w1 > 0.
# Proporción 4 : 3 entre casillas pintadas y movilidad (0.4/0.7 ≈ 0.571 y 0.3/0.7 ≈ 0.429).
PESOS = (0.4 / 0.7, 0.3 / 0.7)


# ---------------------------------------------------------------------------
# f1: diferencia de casillas pintadas
# ---------------------------------------------------------------------------
def diferencia_pintadas(estado):
    """D(s) = |P_V| - |P_R|"""
    return contar_casillas(estado, VERDE) - contar_casillas(estado, ROJO)


def f1(estado):
    return diferencia_pintadas(estado) / TOTAL_CASILLAS


# ---------------------------------------------------------------------------
# f2: diferencia de movilidad
# ---------------------------------------------------------------------------
def f2(estado):
    saltos_verde = len(movimientos(estado, VERDE))
    saltos_rojo = len(movimientos(estado, ROJO))
    return (saltos_verde - saltos_rojo) / 8


# ---------------------------------------------------------------------------
# Heurística combinada, utilidad terminal y evaluación
# ---------------------------------------------------------------------------
def h(estado, pesos=PESOS):
    w1, w2 = pesos
    return w1 * f1(estado) + w2 * f2(estado)


def utilidad(estado):
    """
    Valor exacto de un estado terminal: más de 1000 si gana el verde,
    menos de -1000 si gana el rojo y 0 si hay empate. Sumar D hace que la
    máquina prefiera ganar por más casillas (o perder por menos).
    """
    d = diferencia_pintadas(estado)
    if d > 0:
        signo = 1
    elif d < 0:
        signo = -1
    else:
        signo = 0
    return 1000 * signo + d


def evaluar(estado, pesos=PESOS):
    """Eval(s): utilidad si la partida terminó, heurística h si no."""
    if es_terminal(estado):
        return utilidad(estado)
    return h(estado, pesos)


def detalle(estado, pesos=PESOS):
    """Todas las piezas de la heurística, para mostrarlas en la interfaz."""
    terminal = es_terminal(estado)
    return {
        "terminal": terminal,
        "utilidad": utilidad(estado) if terminal else None,
        "pintadas_verde": contar_casillas(estado, VERDE),
        "pintadas_rojo": contar_casillas(estado, ROJO),
        "saltos_verde": len(movimientos(estado, VERDE)),
        "saltos_rojo": len(movimientos(estado, ROJO)),
        "f1": f1(estado),
        "f2": f2(estado),
        "pesos": list(pesos),
        "h": h(estado, pesos),
    }
