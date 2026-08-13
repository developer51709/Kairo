"""
src/bot/database/migrations/__init__.py
-----------------------------------------
Kairo Database Migrations

Contains the migration runner and all numbered SQL migration files.

Migration files follow the naming convention:
    <NNN>_<description>.sql

Where NNN is a zero-padded sequential number (001, 002, ...).

The runner tracks which migrations have been applied in a special
schema_migrations table and only runs new ones.
"""
