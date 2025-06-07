# Translator as Service

## Introduction: Project Structure

- `api_template/` — Contains all API related code:

  - `manage.py` — Entry point for the API. Contains no business logic.
  - `.env` — Global configuration file for the API. Avoid putting application/module level configs here.
  - `application/` — Main source code and test modules for the API. Prefer to keep this folder at the project root.
  - `logs/` — Contains raw log files. No configuration files here. You can move this folder, but avoid placing it inside `application/`.
  - `models/` — Store ML/DL model files here. For large models hosted on the cloud, consider using symlinks.
  - `resources/` — Store documentation, CSV/TXT/IMG files related to the application.
  - `settings/` — Global configuration files (e.g., YAML/JSON) for logger, database, models, etc.

- `application/` — Core application folder:
  - `main/` — Priority folder with all core application code:
    - `infrastructure/` — Backbone code for database and ML/DL models.
    - `routers/` — API route handlers. Should contain no business logic.
    - `services/` — Business logic and processing layer for routers.
    - `utility/` — Helper modules:
      - `config_loader` — Loads app configs from `settings/`.
      - `logger` — Logging utilities.
      - `manager` — Utilities for common data-related tasks used across services.
    - `config.py` — Main application config, inheriting from `.env`.
  - `test/` — Test cases for the application.
  - `initializer.py` — Preloads models and modules shared across the app to speed up inference.

## Running Locally

```bash
pip install -r requirements.txt
python manage.py
```

## Docker support

```bash
docker build -t translator-as-service .
docker run --env-file .env --gpus all -p 8080:8080 translator-as-service:latest
```
