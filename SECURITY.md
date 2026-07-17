# Security Policy

## Supported Versions

| Version | Supported |
|:---|:---:|
| 1.0.x | ✅ |

## Reporting a Vulnerability

**Please do not report security vulnerabilities via public GitHub Issues.**

If you discover a security vulnerability, please disclose it responsibly by emailing the maintainer directly. You can find contact information on the [GitHub profile](https://github.com/SahanaK17).

Include in your report:

- A description of the vulnerability and its potential impact
- Steps to reproduce or proof-of-concept code
- Any suggested mitigation or fix

You will receive an acknowledgment within 48 hours. We aim to patch confirmed vulnerabilities within 7 days and will coordinate disclosure timing with you.

---

## Security Design Principles

MindGuard is designed with the following security properties:

- **No sensitive input is stored.** Raw keystrokes are discarded at the OS hook level. Only statistical aggregates (timing intervals, velocities) are transmitted.
- **Authentication is stateless with revocation.** Access tokens use short-lived JWTs (30 minutes). Logout immediately blacklists the token JTI in Redis, preventing reuse.
- **Passwords are never stored in plaintext.** All passwords are hashed with bcrypt at work factor 12.
- **Secrets are managed via environment variables.** No credentials are hardcoded. See `.env.example` for the full variable manifest.
- **Input is validated at the API boundary.** All request bodies are validated against strict Pydantic schemas before processing.
- **CORS is restricted to an allowlist.** Only origins listed in `CORS_ORIGINS` are permitted.

---

## Known Limitations

- Token blacklisting requires a running Redis instance. If Redis is unavailable, the backend degrades gracefully (tokens remain valid until natural expiry). Ensure Redis is highly available in production deployments.
- WebSocket authentication is performed via query parameter (`?token=`). In production, ensure TLS (WSS) is enforced at the Nginx layer to prevent token interception.
