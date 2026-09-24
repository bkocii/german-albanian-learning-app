# Manual Testing Guide

## Foundation and custom user model

Run from the project root in PowerShell:

```powershell
uv sync
uv run python manage.py makemigrations --check
uv run python manage.py migrate
uv run python manage.py check
uv run python manage.py test
```

Create an administrator using an email address:

```powershell
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Then open `http://127.0.0.1:8000/admin/`, sign in with the email address, and
confirm that Users can be added and edited without a username field.

Expected result:

- All commands complete without errors.
- `createsuperuser` asks for an email address, not a username.
- The administration user list displays email, name, staff status, and active status.

## Learner registration and verification

Start the server:

```powershell
uv run python manage.py runserver
```

1. Open `http://127.0.0.1:8000/` and select **Fillo tani**.
2. Register with a test email and password.
3. Confirm that the account cannot sign in before verification.
4. Copy the `/accounts/verify/...` link printed in the server console and open it.
5. Sign in and confirm that the dashboard opens.

## Password reset

1. Sign out and select **Keni harruar fjalëkalimin?**.
2. Submit the verified account's email.
3. Copy the reset link printed in the server console.
4. Set a new password and sign in with it.

## One active session

1. Sign in using one normal browser window.
2. Sign in to the same account from a different browser or private window.
3. Refresh the dashboard in the first browser.

Expected result: the first browser returns to login and explains that the account was opened
on another device; the second browser remains signed in.

## Account throttling

Repeated account-form submissions from one address are temporarily blocked after the configured
limit. Development defaults are 10 submissions in 300 seconds. Restarting the local server clears
the in-memory development counter.
