# API Scripts

## init_db.py

Script for database initialization. Checks if tables exist and creates them on first startup if they don't exist.
Also applies Alembic migrations to ensure the database schema is up to date.

### Automatic Execution

The script is automatically executed on `docker-compose up` startup through the `db-init` service. It runs once before the API service starts.

### Manual Execution

```bash
# Manually
python -m scripts.init_db

# Through Docker
docker compose exec api python -m scripts.init_db
```

### Logic

1. Checks database connection (with retries)
2. Applies Alembic migrations to bring schema up to date
3. Checks if tables exist in the database
4. If tables are missing - creates them based on SQLAlchemy models
5. If tables already exist - skips creation

### Exit Codes

- `0` - Success
- `1` - Error (database connection failed or table creation failed)

