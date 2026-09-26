---
summary: How offload traffic is encrypted and authenticated, and how to run workers and relays safely.
---
All traffic between Storia servers, workers and relays is **encrypted and authenticated** with the shared
`secret`. The secret itself is never sent over the network.

## How it works

When a connection opens, each side sends a protocol version and a fresh 32-byte random nonce. Both sides then
derive keys:

```text
psk = PBKDF2-HMAC-SHA256(secret, "storia-offload-psk", 200,000 iterations)
prk = HMAC-SHA256(psk, initiatorNonce || responderNonce)
key(initiator → responder) = HMAC-SHA256(prk, "i2r")
key(responder → initiator) = HMAC-SHA256(prk, "r2i")
```

Every message after that is sealed with **AES-256-GCM**, using a 96-bit IV built from a per-direction message
counter. As a result:

- Nobody without the secret can **read** the traffic.
- Messages cannot be **forged**, **modified**, **replayed** or **reordered**: any of these fails authentication
  and the connection is closed.
- A peer with a **different secret** fails on its very first message and is refused.
- Each connection has **its own keys**, because the nonces are fresh.
- Data is optionally compressed (deflate) *before* encryption.

Peers with a different protocol version are refused with a message asking you to update both sides to the same
Storia release.

## Choosing a secret

- At least 8 characters are required; use **20 or more random characters**.
- Generate one with:

    ```bash
    openssl rand -base64 24
    ```

- Use the same secret on the server, every worker and the relay.
- Treat it like a password: keep `storia.yml` and `relay.properties` readable only by the service user.

!!! warning "If the secret leaks"
    Keys are derived from the secret and the (public) nonces, so someone who recorded the traffic *and* later
    learns the secret could decrypt that recording. Change the secret everywhere if you think it has leaked.
    What they could read is terrain data only: no player data, chat or credentials ever go over this link.

## What a worker can and cannot do

The main server treats worker answers as untrusted input:

- Every answer is **validated** (section layout, block data, heightmap sizes) before it is applied. A malformed answer is
  discarded and the chunk is generated locally.
- A worker only ever receives chunk coordinates, the dimension and nearby structure outlines. It never sees
  players, inventories, chat or the world files.
- A worker cannot send commands or change anything on the main server.

A worker holding the correct secret *could* still return valid-looking but different terrain. Only run workers on
machines you control. `-Dstoria.verifyOffload=true` lets you audit a worker by regenerating every chunk locally.

## Network recommendations

- Keep port **25590** off the public internet where you can: use a LAN, a VPN (WireGuard, Tailscale) or firewall
  rules that only allow your own machines.

    ```bash
    # ufw: only allow the main server to reach the worker
    sudo ufw allow from 192.168.0.10 to any port 25590 proto tcp
    ```

- With a [[relay]], only the relay needs an open port. Workers connect out.
- Workers started with `-Dstoria.worker=true` open **no** Minecraft, query or RCON port.
