---
summary: How cluster traffic is encrypted and authenticated, and how to run a relay and workers safely.
---
All traffic between Storia Workers, Storia Relay and Storia Proxy is **encrypted and authenticated** with the
shared `secret`. The secret itself is never sent over the network.

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

- Use the same secret on the relay, every worker and Storia Proxy (`[cluster]` in `storia-proxy.toml`).
- Treat it like a password: keep `storia.yml`, `relay.properties` and `storia-proxy.toml` readable only by the
  service user.

!!! warning "If the secret leaks"
    Keys are derived from the secret and the (public) nonces, so someone who recorded the traffic *and* later
    learns the secret could decrypt that recording. Anyone holding the secret can also join the cluster as a
    worker and read or change the world. Change the secret everywhere if you think it has leaked.

## What travels over the link

Chunks, entities, player data (inventories, positions), advancements, statistics, maps and the scoreboard: the
relay stores the whole world. Only run workers and the relay on machines you control.

## Network recommendations

- Keep port **25590** off the public internet: use a LAN, a VPN (WireGuard, Tailscale) or firewall rules that only
  allow your own workers and proxy.

    ```bash
    # ufw: only allow the workers and the proxy to reach the relay
    sudo ufw allow from 10.0.0.0/24 to any port 25590 proto tcp
    ```

- Only the relay listens on 25590; workers and Storia Proxy connect out to it.
- Players never reach workers directly: keep the workers' Minecraft ports private and use modern forwarding
  from Storia Proxy.
