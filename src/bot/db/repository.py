from datetime import date, time

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.bot.db.models import AllowedUser, Reservation, SystemConfig


# ── AllowedUser ──────────────────────────────────────────────

async def get_allowed_user(session: AsyncSession, telegram_id: int) -> AllowedUser | None:
    stmt = select(AllowedUser).where(AllowedUser.telegram_id == telegram_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def is_allowed(session: AsyncSession, telegram_id: int) -> bool:
    user = await get_allowed_user(session, telegram_id)
    return user is not None


async def ensure_user(session: AsyncSession, telegram_id: int, display_name: str) -> AllowedUser:
    user = await get_allowed_user(session, telegram_id)
    if user is None:
        user = AllowedUser(telegram_id=telegram_id, display_name=display_name)
        session.add(user)
        await session.flush()
    return user


async def remove_user(session: AsyncSession, telegram_id: int) -> bool:
    user = await get_allowed_user(session, telegram_id)
    if user is None:
        return False
    await session.delete(user)
    return True


async def list_allowed_users(session: AsyncSession) -> list[AllowedUser]:
    stmt = select(AllowedUser).order_by(AllowedUser.display_name)
    return list((await session.execute(stmt)).scalars().all())


# ── SystemConfig ─────────────────────────────────────────────

async def get_system_config(session: AsyncSession) -> SystemConfig:
    config = await session.get(SystemConfig, 1)
    assert config is not None
    return config


async def toggle_reservations(session: AsyncSession) -> bool:
    config = await get_system_config(session)
    config.reservations_enabled = not config.reservations_enabled
    return config.reservations_enabled


# ── Reservation ──────────────────────────────────────────────

async def get_booked_times(session: AsyncSession, target_date: date) -> list[time]:
    stmt = select(Reservation.start_time).where(Reservation.date == target_date)
    return list((await session.execute(stmt)).scalars().all())


async def create_reservation(
    session: AsyncSession,
    user: AllowedUser,
    target_date: date,
    start: time,
    end: time,
) -> Reservation:
    reservation = Reservation(
        user_id=user.id,
        date=target_date,
        start_time=start,
        end_time=end,
    )
    session.add(reservation)
    await session.flush()
    return reservation


async def get_user_reservations(
    session: AsyncSession, telegram_id: int
) -> list[Reservation]:
    stmt = (
        select(Reservation)
        .join(AllowedUser)
        .where(AllowedUser.telegram_id == telegram_id)
        .where(Reservation.date >= date.today())
        .order_by(Reservation.date, Reservation.start_time)
        .options(selectinload(Reservation.user))
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_all_reservations(session: AsyncSession) -> list[Reservation]:
    stmt = (
        select(Reservation)
        .where(Reservation.date >= date.today())
        .order_by(Reservation.date, Reservation.start_time)
        .options(selectinload(Reservation.user))
    )
    return list((await session.execute(stmt)).scalars().all())


async def cancel_reservation(session: AsyncSession, reservation_id: int) -> bool:
    reservation = await session.get(Reservation, reservation_id)
    if reservation is None:
        return False
    await session.delete(reservation)
    return True


async def cancel_reservation_if_owned(
    session: AsyncSession, reservation_id: int, telegram_id: int
) -> bool:
    stmt = (
        select(Reservation)
        .join(AllowedUser)
        .where(Reservation.id == reservation_id)
        .where(AllowedUser.telegram_id == telegram_id)
    )
    reservation = (await session.execute(stmt)).scalar_one_or_none()
    if reservation is None:
        return False
    await session.delete(reservation)
    return True
