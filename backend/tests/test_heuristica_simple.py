"""
Experimento: ¿qué tan fácil es ganarle a la máquina con cada heurística y en cada nivel?

Se juegan partidas completas entre la máquina (verde) y tres jugadores rojos automáticos
que imitan a personas con distinta habilidad. Se comparan dos funciones de evaluación:

    simple:     f1 = (casillas verdes - casillas rojas) / 64
    combinada:  h  = w1*f1 + w2*f2   (la que usa el juego)

Parte 1: las dos heurísticas en principiante (profundidad 2).
Parte 2: la heurística combinada en principiante, amateur y experto (2, 4 y 6).

Cómo ejecutarlo (desde la carpeta backend):

    Ver las tablas de resultados:
        python tests/test_heuristica_simple.py

    Comprobarlo como prueba automática:
        python -m pytest tests/test_heuristica_simple.py -v
"""

import os
import random
import sys
from functools import lru_cache

import pytest

# Al ejecutarlo como script, Python no ve la carpeta backend; pytest sí (pytest.ini)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from juego import (  # noqa: E402
    VERDE, ROJO, estado_inicial, movimientos, aplicar_movimiento,
    pasar_turno, es_terminal, contar_casillas,
)
from heuristica import f1, h  # noqa: E402
from minimax import decidir, minimax, nuevas_estadisticas, PROFUNDIDAD_POR_NIVEL  # noqa: E402

PARTIDAS = 40          # cada partida empieza en una posición aleatoria distinta
SEMILLA_BASE = 1000    # semillas fijas: los resultados son siempre los mismos
PRINCIPIANTE = PROFUNDIDAD_POR_NIVEL["principiante"]

HEURISTICAS = {
    "simple (solo f1)": f1,
    "combinada (h)": h,
}


# ---------------------------------------------------------------------------
# Jugadores rojos (el "humano")
# ---------------------------------------------------------------------------
def rojo_aleatorio(estado, azar):
    """Salta a cualquier casilla legal: una persona que no piensa la jugada."""
    return azar.choice(movimientos(estado, ROJO))


def rojo_intuitivo(estado, azar):
    """
    Mira una sola jugada: escoge el salto que lo deja con más saltos que el verde.
    Es como juega una persona que entendió que quedarse sin salidas es perder.
    """
    def ventaja(jugada):
        hijo = aplicar_movimiento(estado, jugada)
        return len(movimientos(hijo, ROJO)) - len(movimientos(hijo, VERDE))

    return max(movimientos(estado, ROJO), key=ventaja)


def rojo_estratega(estado, azar):
    """
    Piensa igual que la máquina en principiante: minimax de profundidad 2 con la
    heurística combinada. Es una persona que anticipa la respuesta del verde.
    """
    estadisticas = nuevas_estadisticas()
    return min(movimientos(estado, ROJO),
               key=lambda jugada: minimax(aplicar_movimiento(estado, jugada), 1, estadisticas))


RIVALES = {
    "aleatorio": rojo_aleatorio,
    "intuitivo": rojo_intuitivo,
    "estratega": rojo_estratega,
}


# ---------------------------------------------------------------------------
# Partidas
# ---------------------------------------------------------------------------
def jugar_partida(semilla, heuristica, rival, profundidad, usar_poda):
    """
    Juega una partida completa y devuelve (casillas verdes, casillas rojas,
    jugadas de la máquina, jugadas en las que todas sus opciones valían lo mismo).
    """
    azar = random.Random(semilla)
    estado = estado_inicial(semilla)
    jugadas_maquina = 0
    jugadas_a_ciegas = 0

    while not es_terminal(estado):
        if not movimientos(estado, estado.turno):
            estado = pasar_turno(estado)  # regla del pase
            continue

        if estado.turno == VERDE:
            decision = decidir(estado, profundidad, usar_poda=usar_poda, heuristica=heuristica)
            valores = {c["valor"] for c in decision["candidatos"]}
            jugadas_maquina += 1
            if len(decision["candidatos"]) > 1 and len(valores) == 1:
                jugadas_a_ciegas += 1
            jugada = decision["jugada"]
        else:
            jugada = rival(estado, azar)

        estado = aplicar_movimiento(estado, jugada)

    return contar_casillas(estado, VERDE), contar_casillas(estado, ROJO), jugadas_maquina, jugadas_a_ciegas


@lru_cache(maxsize=None)
def resultados(nombre_heuristica, nombre_rival, profundidad=PRINCIPIANTE, usar_poda=False):
    """
    Juega PARTIDAS partidas y resume el resultado desde el punto de vista del rojo.

    En principiante se juega sin poda a propósito: con poda, el ordenamiento por
    movilidad decide los empates y f1 estaría usando la movilidad "a escondidas".
    El valor minimax es el mismo con y sin poda; solo cambia cuál de las jugadas
    empatadas se escoge. En amateur y experto se usa poda para que sea rápido.
    """
    heuristica = HEURISTICAS[nombre_heuristica]
    rival = RIVALES[nombre_rival]
    resumen = {"gana_rojo": 0, "empates": 0, "gana_maquina": 0, "margen_rojo": 0,
               "jugadas_maquina": 0, "jugadas_a_ciegas": 0}

    for i in range(PARTIDAS):
        verdes, rojas, jugadas, a_ciegas = jugar_partida(SEMILLA_BASE + i, heuristica, rival, profundidad, usar_poda)
        resumen["margen_rojo"] += rojas - verdes
        resumen["jugadas_maquina"] += jugadas
        resumen["jugadas_a_ciegas"] += a_ciegas
        if rojas > verdes:
            resumen["gana_rojo"] += 1
        elif verdes > rojas:
            resumen["gana_maquina"] += 1
        else:
            resumen["empates"] += 1

    return resumen


def resultados_por_nivel(nombre_rival, nivel):
    profundidad = PROFUNDIDAD_POR_NIVEL[nivel]
    return resultados("combinada (h)", nombre_rival, profundidad, usar_poda=profundidad > PRINCIPIANTE)


def puntos_rojo(resumen):
    """Victoria = 1 punto, empate = 0.5."""
    return resumen["gana_rojo"] + 0.5 * resumen["empates"]


# ---------------------------------------------------------------------------
# Pruebas
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nombre_rival", list(RIVALES))
def test_es_mas_facil_ganarle_a_la_heuristica_simple(nombre_rival):
    simple = resultados("simple (solo f1)", nombre_rival)
    combinada = resultados("combinada (h)", nombre_rival)
    assert puntos_rojo(simple) > puntos_rojo(combinada)


def test_con_f1_la_maquina_decide_a_ciegas_la_mayoria_de_las_veces():
    """
    Propiedad 4 del informe: en profundidad 2 todas las hojas tienen el mismo f1
    (salvo que alguien quede encerrado), así que la máquina no distingue sus jugadas.
    """
    simple = resultados("simple (solo f1)", "intuitivo")
    combinada = resultados("combinada (h)", "intuitivo")
    assert simple["jugadas_a_ciegas"] / simple["jugadas_maquina"] > 0.5
    assert combinada["jugadas_a_ciegas"] < simple["jugadas_a_ciegas"]


@pytest.mark.parametrize("nombre_rival", list(RIVALES))
def test_la_dificultad_sube_con_el_nivel(nombre_rival):
    principiante = resultados_por_nivel(nombre_rival, "principiante")
    amateur = resultados_por_nivel(nombre_rival, "amateur")
    experto = resultados_por_nivel(nombre_rival, "experto")
    assert puntos_rojo(principiante) > puntos_rojo(amateur) >= puntos_rojo(experto)


# ---------------------------------------------------------------------------
# Tablas para el informe
# ---------------------------------------------------------------------------
def imprimir_tablas():
    print(f"\nParte 1. Máquina en profundidad {PRINCIPIANTE} (principiante), {PARTIDAS} partidas por fila\n")
    encabezado = (f"{'Rival (rojo)':<11} {'Heurística de la máquina':<25} {'Gana rojo':>9} "
                  f"{'Empates':>8} {'Gana máquina':>13} {'Margen rojo':>12} {'Jugadas a ciegas':>17}")
    print(encabezado)
    print("-" * len(encabezado))

    for nombre_rival in RIVALES:
        for nombre_heuristica in HEURISTICAS:
            r = resultados(nombre_heuristica, nombre_rival)
            a_ciegas = 100 * r["jugadas_a_ciegas"] / r["jugadas_maquina"]
            print(f"{nombre_rival:<11} {nombre_heuristica:<25} {r['gana_rojo']:>9} {r['empates']:>8} "
                  f"{r['gana_maquina']:>13} {r['margen_rojo'] / PARTIDAS:>+12.1f} {a_ciegas:>16.0f}%")
        print()

    print(f"Parte 2. Heurística combinada (h) en cada nivel, {PARTIDAS} partidas por fila\n")
    encabezado = (f"{'Rival (rojo)':<11} {'Nivel':<25} {'Gana rojo':>9} "
                  f"{'Empates':>8} {'Gana máquina':>13} {'Margen rojo':>12}")
    print(encabezado)
    print("-" * len(encabezado))

    for nombre_rival in RIVALES:
        for nivel, profundidad in PROFUNDIDAD_POR_NIVEL.items():
            r = resultados_por_nivel(nombre_rival, nivel)
            print(f"{nombre_rival:<11} {f'{nivel} ({profundidad})':<25} {r['gana_rojo']:>9} {r['empates']:>8} "
                  f"{r['gana_maquina']:>13} {r['margen_rojo'] / PARTIDAS:>+12.1f}")
        print()

    print("Margen rojo: casillas del rojo menos casillas del verde, en promedio por partida.")
    print("Jugadas a ciegas: jugadas de la máquina en las que todas sus opciones valían lo mismo.")


if __name__ == "__main__":
    imprimir_tablas()
