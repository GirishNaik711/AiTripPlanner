import requests


class UpstreamError(RuntimeError):
    """An external API call failed. The message never contains the request URL."""


def get_json(url: str, params: dict = None, timeout: tuple = (3, 15)) -> dict:
    # requests puts the full URL, including api keys, into its exception text,
    # so nothing from the original exception is kept.
    try:
        response = requests.get(url, params=params, timeout=timeout)
    except requests.RequestException:
        raise UpstreamError("request to upstream API failed") from None

    if response.status_code != 200:
        raise UpstreamError(f"upstream API returned HTTP {response.status_code}")

    try:
        return response.json()
    except ValueError:
        raise UpstreamError("upstream API returned invalid JSON") from None
