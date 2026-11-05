# PostgreSQL schema backup

## Backup commands (PowerShell)

Set the database password for the current terminal only:

```powershell
$env:PGPASSWORD="smartgrocery"
```

Schema-only backup:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" `
  -h localhost -p 5432 -U smartgrocery -d smartgrocery `
  --schema-only --no-owner --no-privileges `
  -f "docs/schema-backup.sql"
```

Full custom-format backup:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" `
  -h localhost -p 5432 -U smartgrocery -d smartgrocery `
  --format=custom --file="smartgrocery.backup"
```

Verify the backup tools:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" --version
& "C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" --list smartgrocery.backup
```

Never commit passwords or `.env` files. Store generated backup artifacts outside
Git or in the team's approved secure artifact storage.
