Bot scaffold (minimal)

Files created:
- bot/__main__.py — module entrypoint (python -m bot)
- bot/bot.py — bot factory/runner, loads cogs from bot/cogs
- bot/cogs/moderation.py — sample cog with ping command and anti-caps logic
- .env.example — environment variables template (includes bot name/status values)

Getting started (local):
1) Copy .env.example to .env and fill DISCORD_TOKEN and other values.
2) Install dependencies (example):
   pip install -r requirements.txt
   # recommended packages: discord.py, python-dotenv
3) Run:
   python -m bot

Next suggested steps (confirm before proceeding):
- Add requirements.txt / pyproject.toml and pin dependencies
- Add more cogs and DB integration
- Add CI + Dockerfile + docker-compose for local dev
- Add logging/Sentry/config validation

If you want, proceed to implement any specific cog or add the dashboard skeleton next. Remember to confirm before the next step.

Database notes:
- By default the scaffold will use SQLite for local development (DATABASE_URL defaults to sqlite+aiosqlite:///./data.db).
- Install aiosqlite (pip install aiosqlite) or use full Postgres in production (DATABASE_URL=postgresql+asyncpg://...).
- The DB service uses SQLAlchemy Async and creates a guild_config table on startup. Use persistent Postgres for production.
