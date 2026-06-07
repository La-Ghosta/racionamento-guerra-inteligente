import os
from typing import Any

import requests


def obter_clima(cidade: str, http_client: Any = requests) -> dict[str, str | float | int] | None:
    """Consulta o clima atual de uma cidade via OpenWeather API.

    Retorna None se a variável OPENWEATHER_API_KEY estiver ausente ou em
    qualquer falha de rede, autenticação ou decodificação.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": cidade, "appid": api_key, "units": "metric", "lang": "pt_br"}

    try:
        resposta = http_client.get(url, params=params, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        return {
            "cidade": dados["name"],
            "temperatura_c": dados["main"]["temp"],
            "descricao": dados["weather"][0]["description"],
            "umidade": dados["main"]["humidity"],
        }
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
        requests.exceptions.JSONDecodeError,
        KeyError,
        TypeError,
    ):
        return None


def geocodificar(cidade: str, http_client: Any = requests) -> tuple[float, float] | None:
    """Converte o nome de uma cidade em coordenadas (lat, lon) via Geocoding API do OpenWeather.

    Retorna None se a variável OPENWEATHER_API_KEY estiver ausente, se a
    cidade não for encontrada, ou em qualquer falha de rede, autenticação
    ou decodificação.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return None

    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {"q": cidade, "limit": 1, "appid": api_key}

    try:
        resposta = http_client.get(url, params=params, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        return (dados[0]["lat"], dados[0]["lon"])
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
        requests.exceptions.JSONDecodeError,
        KeyError,
        TypeError,
        IndexError,
    ):
        return None
