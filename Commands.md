| Situation | Command |
|-----------|---------|
| Start or restart | `docker compose up --build` |
| Stop only | `docker compose down` |
| Stop and wipe data | `docker compose down -v` |
| Full rebuild (no cache) | `docker compose build --no-cache && docker compose up` |
| Clean reset + fresh start | `docker compose down -v` then `docker compose up --build` |
