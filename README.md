# Vision On

A small Flask web app for sharing and curating pixel art around Warwick's
campus. Users upload pixel art, admins moderate and assign it to a physical
campus location (DCS, MSB, Piazza), and each approved piece gets a QR code
so it can be displayed physically and liked/disliked by anyone who scans it.

## How it works

**Accounts.** Users register with a username, email and password
(`werkzeug` password hashing, no plaintext storage). Registration sends a
verification link; the account can't log in until the link is clicked. There
are two account types, both stored on the same `User` model with an `admin`
flag: regular **artists**, who can upload and manage their own art, and
**admins**, who additionally get a moderation queue.

**Uploading art.** An artist uploads an image through `/imageUpload`. The
server crops it to a square around its centre and resizes it to 64x64 (the
"pixel art" look is enforced server-side, not just by convention), then
stores the resulting PNG as a binary blob directly in the database
(`Artwork.imageData`). New uploads start in `unmoderated` status and aren't
visible anywhere public yet.

**Moderation.** Admins see every `unmoderated`/`pending` piece on
`/moderate`. From there they can:
- **Approve** a piece and assign it to one of the campus locations
  (Piazza / MSB / DCS / none) — this flips its status to `approved` and
  makes it visible in that location's gallery.
- **Archive** a piece (hides it without deleting it).
- **Unarchive** a piece (sends it back to the moderation queue).

**Galleries & QR codes.** `/imagefinder` links to a gallery per campus
location (`/findAllImages/<place>`), each showing only `approved` art for
that place, ranked by likes. Every image in a gallery gets a QR code
generated on the fly (`qrcode`, encoding the artwork's id) — the idea being
a physical print of the art can carry a QR code next to it so a passer-by
can scan it, land on the piece's page, and like or dislike it.

**Likes.** Each like/dislike is recorded per-user in a `Likes` table (so a
user can only vote once per piece — the UI swaps the buttons out for "you
have already voted" after voting, see `static/js/like.js`), and the
artwork's running like count is incremented/decremented directly in
`/like` and `/dislike`. Admins can reset an artwork's like count via
`/reset`, which logs the reason to a `LikeReset` audit table and clears
the per-user vote records so people can vote again.

**Profile.** `/profile` shows a user's own uploads (with status, location,
likes, QR code) and their profile picture, which can be changed via
`/profilePic`.

**Password / email recovery.** Forgotten-password and forgotten-email
flows both work the same way: generate a signed, time-limited token
(`itsdangerous`), email a link containing it, and verify the token before
allowing the change. Tokens expire after 1 hour.

## Key features

- Email-verified registration and login (`flask-login` sessions)
- Image upload with automatic square-crop + resize to 64x64
- Admin moderation queue: approve (with location), archive, unarchive
- Per-location public galleries, sorted by likes
- Per-image QR codes for physical/real-world display
- One-vote-per-user like/dislike with an admin-auditable reset
- Profile picture upload
- Token-based email verification and password/email reset links

## Running it (as a user)

Requires Python 3.9+.

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

The app runs at http://127.0.0.1:5000. The SQLite database is dropped and
recreated from seed data (`db_schema.py: dbinit`) every time the app starts,
so nothing you do persists across restarts — this is a development
convenience (`resetdb = True` at the top of `app.py`), not a design choice
you'd want in production.

Seeded accounts:
- `AdrianBarraCornes` / `223` — admin, already verified
- `123` / `123` — regular user, already verified

### Email

Real email sending is off by default (`MAIL_SUPPRESS_SEND`), so register and
password/email-reset flows work out of the box without an SMTP server — the
confirmation link is just not actually emailed anywhere. To send real email,
set these environment variables before starting the app:

- `MAIL_SERVER`, `MAIL_PORT` (default 587), `MAIL_USE_TLS` (default true)
- `MAIL_USERNAME`, `MAIL_PASSWORD`
- `MAIL_SENDER` (default `noreply@dcs.warwick.ac.uk`)
- `SECRET_KEY` (default is a placeholder — set a real one for production)

## Key design decisions

- **Images are stored as DB blobs, not files on disk.** Simpler deployment
  (one SQLite file is the whole app's state, no separate media directory to
  back up or serve statically) at the cost of making the DB heavier and
  images always loaded through Flask/base64 rather than served directly.
- **Images are forced to 64x64 server-side.** Cropping/resizing on upload
  guarantees every piece renders identically regardless of what the artist
  submitted, rather than relying on CSS to fake a uniform grid.
- **Moderation is a status machine, not a delete.** `unmoderated` →
  `pending`/`approved`/`archived` are all just a string column on
  `Artwork`; nothing is ever deleted, so admin actions are reversible
  (`archive` → `unarchive`) and there's an audit trail.
- **Likes are a join table, not a counter you can spam.** A `Likes` row per
  (artwork, user) pair is the source of truth for "has this user voted",
  with `Artwork.likes` kept as a cached counter for fast sorting — resets
  clear both so the two can't drift.
- **Auth state changes (email confirm, password reset) use signed tokens,
  not database flags you'd have to look up by a guessable id.** A token
  embeds the email and is verified without a DB round trip, and naturally
  expires after an hour.
- **No real email required to run the app.** Email-sending is config-gated
  (env vars) rather than hardcoded, so the same codebase works for a
  throwaway local demo and a real deployment with actual SMTP credentials.
