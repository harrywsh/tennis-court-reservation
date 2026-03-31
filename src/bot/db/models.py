from datetime import date, datetime, time, timezone

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Time, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AllowedUser(Base):
    __tablename__ = "allowed_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    display_name: Mapped[str]
    added_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (UniqueConstraint("date", "start_time", name="uq_date_start"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("allowed_users.id"))
    date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    cancelled_at: Mapped[datetime | None] = mapped_column(default=None)

    user: Mapped["AllowedUser"] = relationship(back_populates="reservations")


class SystemConfig(Base):
    __tablename__ = "system_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    reservations_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
