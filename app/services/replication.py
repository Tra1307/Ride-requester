import httpx
from app.state import PEERS, NODE_ID


async def broadcast_to_peers(path: str, payload: dict):
    if not PEERS:
        return

    async with httpx.AsyncClient(timeout=2.0) as client:
        for peer in PEERS:
            url = f"{peer}{path}"
            try:
                await client.post(
                    url,
                    json=payload,
                    headers={"X-Source-Node": NODE_ID}
                )
            except Exception:
                pass


async def request_votes_from_peers(path: str, payload: dict) -> list[dict]:
    results = []

    if not PEERS:
        return results

    async with httpx.AsyncClient(timeout=2.0) as client:
        for peer in PEERS:
            url = f"{peer}{path}"
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"X-Source-Node": NODE_ID}
                )
                if response.status_code == 200:
                    results.append(response.json())
                else:
                    results.append({
                        "approve": False,
                        "node": peer,
                        "reason": f"http {response.status_code}"
                    })
            except Exception:
                results.append({
                    "approve": False,
                    "node": peer,
                    "reason": "unreachable"
                })

    return results
