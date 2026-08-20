# Large local mock dataset

LoveLink includes `seed_mock_users` for generating a large deterministic development dataset without committing generated rows to Git.

The command is intentionally restricted to Django `DEBUG=true` environments.

## Seed one million users

Run reference-data seeding first, then generate users and profiles:

```powershell
cd backend
uv run --env-file ../.env.host python manage.py seed_reference_data
uv run --env-file ../.env.host python manage.py seed_mock_users --count 1000000 --batch-size 5000
```

The command defaults to 1,000,000 users, so `--count 1000000` may be omitted. It writes in batches and is deterministic/idempotent: rerunning the same index range does not create duplicate users or profiles.

Generated accounts use emails such as `mock.000000001@lovelink.local` and the shared local-only password `MockPassword123!`.

## Richer profile data

Add three interests and one external placeholder portrait per profile:

```powershell
uv run --env-file ../.env.host python manage.py seed_mock_users `
  --count 1000000 `
  --batch-size 5000 `
  --with-interests `
  --with-photos
```

`--with-interests` adds roughly three million join-table rows for one million users. `--with-photos` adds one million `ProfilePhoto` rows, so these options require substantially more disk space and seed time.

Profiles include deterministic Vietnamese-style names, age, gender, location, hometown, height, occupation, education, income, relationship status/goal, habits, biography, visibility, verification state, phone-verification state and recent activity.

## Smaller or parallel ranges

For a quick local UI dataset:

```powershell
uv run --env-file ../.env.host python manage.py seed_mock_users --count 10000
```

`--start-index` makes it possible to seed non-overlapping ranges:

```powershell
uv run --env-file ../.env.host python manage.py seed_mock_users --start-index 1 --count 500000
uv run --env-file ../.env.host python manage.py seed_mock_users --start-index 500001 --count 500000
```

## Remove generated accounts

```powershell
uv run --env-file ../.env.host python manage.py seed_mock_users --clear
```

Deleting mock users cascades to their generated profile, photo and interest relations. This command never targets normal accounts; it only deletes users whose email starts with `mock.`.
