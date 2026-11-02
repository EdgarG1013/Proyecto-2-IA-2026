"""Juega partidas completas contra la API con un humano que escoge saltos al azar."""

import random

from fastapi.testclient import TestClient

from main import app

cliente = TestClient(app)


def jugar_partida(semilla, nivel, poda):
    azar = random.Random(semilla)
    partida = cliente.post("/api/partida/nueva", json={"semilla": semilla}).json()
    assert partida["estado"]["turno"] == 1  # siempre empieza la máquina (verde)
    assert partida["casillas_verde"] == 1 and partida["casillas_rojo"] == 1

    while not partida["terminado"]:
        estado = partida["estado"]
        if estado["turno"] == 1:
            r = cliente.post("/api/partida/jugada-maquina",
                             json={"estado": estado, "nivel": nivel, "poda": poda})
            assert r.status_code == 200, r.text
            partida = r.json()["partida"]
        else:
            jugada = azar.choice(partida["movimientos"])
            r = cliente.post("/api/partida/jugada-humano", json={"estado": estado, "jugada": jugada})
            assert r.status_code == 200, r.text
            partida = r.json()

    return partida


def test_partida_completa_termina_con_ganador():
    for semilla in range(5):
        final = jugar_partida(semilla, "principiante", poda=True)
        verde, rojo = final["casillas_verde"], final["casillas_rojo"]
        esperado = "verde" if verde > rojo else "rojo" if rojo > verde else "empate"
        assert final["ganador"] == esperado
        assert final["movimientos"] == []


def test_jugada_ilegal_se_rechaza():
    partida = cliente.post("/api/partida/nueva", json={"semilla": 7}).json()
    estado = partida["estado"]
    # No es el turno del rojo todavía
    r = cliente.post("/api/partida/jugada-humano", json={"estado": estado, "jugada": [0, 0]})
    assert r.status_code == 400


def test_poda_y_sin_poda_eligen_la_misma_jugada():
    partida = cliente.post("/api/partida/nueva", json={"semilla": 11}).json()
    cuerpo = {"estado": partida["estado"], "nivel": "amateur"}
    con = cliente.post("/api/partida/jugada-maquina", json={**cuerpo, "poda": True}).json()["decision"]
    sin = cliente.post("/api/partida/jugada-maquina", json={**cuerpo, "poda": False}).json()["decision"]
    assert con["jugada"] == sin["jugada"]
    assert con["valor"] == sin["valor"]
    assert con["hojas"] <= sin["hojas"]
