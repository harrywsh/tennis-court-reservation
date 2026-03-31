# Tennis Court Reservation Bot

Telegram bot for managing tennis court reservations with an allowlist-based access control system.

## Features

| Feature | Description |
|---|---|
| Interactive booking | Calendar-based date picker and time slot selection |
| Access control | Allowlist system — only approved users can book |
| Admin panel | Add/remove users, view/cancel all bookings, toggle reservations on/off |
| Conflict prevention | Unique constraint on date+time prevents double bookings |
| Self-service cancellation | Users can view and cancel their own bookings |

## Commands

**User commands:**

| Command | Description |
|---|---|
| `/start` | Welcome message and access check |
| `/help` | List available commands |
| `/book` | Reserve a time slot |
| `/mybookings` | View and cancel your upcoming bookings |

**Admin commands:**

| Command | Description |
|---|---|
| `/toggle` | Enable/disable reservations globally |
| `/allbookings` | View and cancel all bookings |
| `/adduser <id> <name>` | Add a user to the allowlist |
| `/removeuser <id>` | Remove a user from the allowlist |
| `/users` | List all allowed users |

## Tech Stack

- **Python 3.12+**
- **aiogram 3** — async Telegram bot framework
- **SQLAlchemy 2** (async) + **aiosqlite** — database
- **pydantic-settings** — configuration from `.env`

## Setup

### Prerequisites

- Docker and Docker Compose
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts to choose a name and username
3. Copy the bot token you receive — you'll need it for `BOT_TOKEN` in `.env`
4. (Optional) Send `/setcommands` to BotFather and paste the following to enable command autocomplete:
   ```
   book - Reserve a time slot
   mybookings - View your upcoming bookings
   help - List available commands
   ```
5. To find your Telegram user ID (needed for `ADMIN_ID`), message [@userinfobot](https://t.me/userinfobot) and it will reply with your ID

### Installation

```bash
git clone https://github.com/harrywsh/tennis-court-reservation.git
cd tennis-court-reservation
cp .env.example .env
# Edit .env with your values
```

### Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | Yes | — | Telegram bot token from BotFather |
| `ADMIN_ID` | Yes | — | Your Telegram user ID (seeded into allowlist on startup) |
| `DB_PATH` | No | `data/reservations.db` | SQLite database file path |
| `SLOT_DURATION_MINUTES` | No | `60` | Duration of each booking slot in minutes |
| `DAY_START_HOUR` | No | `8` | First bookable hour of the day |
| `DAY_END_HOUR` | No | `21` | Last bookable hour of the day |
| `MAX_ADVANCE_DAYS` | No | `14` | How many days ahead users can book |

### Running

```bash
# Start the bot
docker compose up -d

# View logs
docker compose logs -f bot

# Rebuild after code changes
docker compose up -d --build

# Stop
docker compose down
```

The SQLite database is persisted in a Docker volume (`bot-data`).

## Project Structure

```
src/bot/
├── __main__.py          # Entrypoint — bot setup and polling
├── config.py            # Settings via pydantic-settings
├── db/
│   ├── engine.py        # Async SQLAlchemy engine + session factory
│   ├── models.py        # AllowedUser, Reservation, SystemConfig
│   └── repository.py    # Database queries
├── filters/
│   └── auth.py          # AllowlistFilter, AdminFilter
├── handlers/
│   ├── admin.py         # Admin commands
│   ├── booking.py       # Booking flow (FSM-based)
│   ├── common.py        # /start, /help
│   └── my_bookings.py   # /mybookings + cancellation
├── keyboards/
│   ├── calendar.py      # Inline calendar keyboard
│   ├── common.py        # Confirm/cancel keyboards
│   └── time_slots.py    # Time slot picker
├── middlewares/
│   └── db.py            # Injects AsyncSession into handlers
├── services/
│   └── booking.py       # Availability logic
└── states/
    └── booking.py       # FSM states for booking flow
```
