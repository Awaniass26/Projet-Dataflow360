"""Modèles SQLAlchemy des tables PostgreSQL de DataFlow360."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Classe de base des modèles SQLAlchemy."""


class Client(Base):
    """Client mobile money."""

    __tablename__ = "clients"

    client_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )
    age: Mapped[int] = mapped_column(Integer)
    sexe: Mapped[str] = mapped_column(String(20))
    region: Mapped[str] = mapped_column(String(100))
    account_type: Mapped[str] = mapped_column(String(50))

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="client",
    )

    credit_applications: Mapped[list["CreditApplication"]] = relationship(
        back_populates="client",
    )


class Transaction(Base):
    """Transaction mobile money."""

    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )
    client_id: Mapped[str] = mapped_column(
        ForeignKey("clients.client_id"),
        index=True,
    )
    amount: Mapped[float] = mapped_column(Float)
    type: Mapped[str] = mapped_column(String(30))
    channel: Mapped[str] = mapped_column(String(30))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )

    client: Mapped["Client"] = relationship(
        back_populates="transactions",
    )

    fraud_alert: Mapped["FraudAlert | None"] = relationship(
        back_populates="transaction",
        uselist=False,
    )


class FraudAlert(Base):
    """Alerte générée par le système de détection de fraude."""

    __tablename__ = "fraud_alerts"

    alert_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    transaction_id: Mapped[str] = mapped_column(
        ForeignKey("transactions.transaction_id"),
        unique=True,
        index=True,
    )
    risk_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    transaction: Mapped["Transaction"] = relationship(
        back_populates="fraud_alert",
    )


class CreditApplication(Base):
    """Demande de crédit."""

    __tablename__ = "credit_applications"

    application_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )
    client_id: Mapped[str] = mapped_column(
        ForeignKey("clients.client_id"),
        index=True,
    )
    requested_amount: Mapped[float] = mapped_column(Float)
    duration: Mapped[int] = mapped_column(Integer)
    income: Mapped[float] = mapped_column(Float)
    expenses: Mapped[float] = mapped_column(Float)

    client: Mapped["Client"] = relationship(
        back_populates="credit_applications",
    )

    credit_score: Mapped["CreditScore | None"] = relationship(
        back_populates="application",
        uselist=False,
    )


class CreditScore(Base):
    """Score de risque associé à une demande de crédit."""

    __tablename__ = "credit_scores"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    application_id: Mapped[str] = mapped_column(
        ForeignKey("credit_applications.application_id"),
        unique=True,
        index=True,
    )
    risk_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    application: Mapped["CreditApplication"] = relationship(
        back_populates="credit_score",
    )