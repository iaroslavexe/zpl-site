"""Общий клиент GraphQL ultisport для скриптов синхронизации."""
import json
import urllib.request

API = "https://api.ultisport.ru/graphql"


def gql(query: str, variables: dict | None = None) -> dict:
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    request = urllib.request.Request(
        API, data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)
