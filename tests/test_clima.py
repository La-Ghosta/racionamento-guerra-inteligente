"""Testes do modulo de consulta de clima via OpenWeather API."""

from unittest.mock import MagicMock

import pytest
import requests

from racionador.clima import obter_clima


@pytest.fixture
def cliente_http_valido():
    mock_resposta = MagicMock()
    mock_resposta.json.return_value = {
        "name": "Brasilia",
        "main": {"temp": 28.5, "humidity": 60},
        "weather": [{"description": "céu limpo"}],
    }
    mock_cliente = MagicMock()
    mock_cliente.get.return_value = mock_resposta
    return mock_cliente


def test_obter_clima_resposta_valida(monkeypatch, cliente_http_valido):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key")
    resultado = obter_clima("Brasilia", http_client=cliente_http_valido)
    assert resultado == {
        "cidade": "Brasilia",
        "temperatura_c": 28.5,
        "descricao": "céu limpo",
        "umidade": 60,
    }


def test_obter_clima_sem_api_key(monkeypatch):
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
    resultado = obter_clima("Brasilia")
    assert resultado is None


def test_obter_clima_connection_error(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key")
    mock_cliente = MagicMock()
    mock_cliente.get.side_effect = requests.exceptions.ConnectionError()
    resultado = obter_clima("Brasilia", http_client=mock_cliente)
    assert resultado is None


def test_obter_clima_timeout(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key")
    mock_cliente = MagicMock()
    mock_cliente.get.side_effect = requests.exceptions.Timeout()
    resultado = obter_clima("Brasilia", http_client=mock_cliente)
    assert resultado is None


def test_obter_clima_http_401(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key")
    mock_resposta = MagicMock()
    mock_resposta.raise_for_status.side_effect = requests.exceptions.HTTPError(
        response=MagicMock(status_code=401)
    )
    mock_cliente = MagicMock()
    mock_cliente.get.return_value = mock_resposta
    resultado = obter_clima("Brasilia", http_client=mock_cliente)
    assert resultado is None


def test_obter_clima_http_404(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key")
    mock_resposta = MagicMock()
    mock_resposta.raise_for_status.side_effect = requests.exceptions.HTTPError(
        response=MagicMock(status_code=404)
    )
    mock_cliente = MagicMock()
    mock_cliente.get.return_value = mock_resposta
    resultado = obter_clima("CidadeInexistente", http_client=mock_cliente)
    assert resultado is None


def test_obter_clima_json_invalido(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key")
    mock_resposta = MagicMock()
    mock_resposta.json.side_effect = requests.exceptions.JSONDecodeError("Decode error", "", 0)
    mock_cliente = MagicMock()
    mock_cliente.get.return_value = mock_resposta
    resultado = obter_clima("Brasilia", http_client=mock_cliente)
    assert resultado is None


def test_obter_clima_chave_faltante(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key")
    mock_resposta = MagicMock()
    mock_resposta.json.return_value = {
        "name": "Brasilia",
        "weather": [{"description": "céu limpo"}],
    }
    mock_cliente = MagicMock()
    mock_cliente.get.return_value = mock_resposta
    resultado = obter_clima("Brasilia", http_client=mock_cliente)
    assert resultado is None
