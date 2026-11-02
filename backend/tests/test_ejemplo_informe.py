"""
Reproduce el ejemplo teórico con profundidad 2 del informe (sección 6).

En el informe las coordenadas empiezan en 1; aquí se convierten a índices desde 0.
"""

import pytest

from juego import Estado, VACIO, VERDE, ROJO, TAMANO, movimientos, aplicar_movimiento
from heuristica import f1, f2, f3, h, territorio
from minimax import decidir, minimax, nuevas_estadisticas


def casilla(fila, columna):
    """Convierte coordenadas del informe (desde 1) a índices internos (desde 0)."""
    return (fila - 1, columna - 1)


def estado_del_informe():
    tablero = [[VACIO] * TAMANO for _ in range(TAMANO)]
    for c in [casilla(4, 1), casilla(2, 2), casilla(1, 4)]:
        tablero[c[0]][c[1]] = VERDE
    for c in [casilla(4, 8), casilla(3, 6), casilla(5, 5)]:
        tablero[c[0]][c[1]] = ROJO
    return Estado(tablero, verde=casilla(1, 4), rojo=casilla(5, 5), turno=VERDE)


def test_heuristicas_en_la_raiz():
    estado = estado_del_informe()

    assert sorted(movimientos(estado, VERDE)) == sorted([casilla(2, 6), casilla(3, 5), casilla(3, 3)])
    assert len(movimientos(estado, ROJO)) == 7
    assert territorio(estado) == (20, 38)

    assert f1(estado) == 0
    assert f2(estado) == pytest.approx(-0.5)
    assert f3(estado) == pytest.approx(-18 / 64)
    assert h(estado) == pytest.approx(-0.234, abs=0.0005)


def test_valor_de_cada_rama():
    """El mínimo de cada nodo MIN coincide con la tabla 1 del informe."""
    estado = estado_del_informe()
    esperado = {
        casilla(2, 6): -0.103,
        casilla(3, 5): 0.019,
        casilla(3, 3): -0.019,
    }
    for jugada, valor in esperado.items():
        hijo = aplicar_movimiento(estado, jugada)
        assert minimax(hijo, 1, nuevas_estadisticas()) == pytest.approx(valor, abs=0.0005)


def test_una_hoja_de_la_tabla():
    """Verde a (3,5) y rojo a (6,7): T_V = 34, T_R = 22, h = 0.169."""
    estado = aplicar_movimiento(estado_del_informe(), casilla(3, 5))
    estado = aplicar_movimiento(estado, casilla(6, 7))
    assert territorio(estado) == (34, 22)
    assert h(estado) == pytest.approx(0.169, abs=0.0005)


@pytest.mark.parametrize("usar_poda", [False, True])
def test_la_maquina_juega_3_5(usar_poda):
    decision = decidir(estado_del_informe(), profundidad=2, usar_poda=usar_poda)
    assert decision["jugada"] == casilla(3, 5)
    assert decision["valor"] == pytest.approx(0.019, abs=0.0005)


def test_la_poda_evalua_menos_hojas():
    sin_poda = decidir(estado_del_informe(), profundidad=2, usar_poda=False)
    con_poda = decidir(estado_del_informe(), profundidad=2, usar_poda=True)
    assert sin_poda["hojas"] == 21
    assert con_poda["hojas"] < sin_poda["hojas"]
