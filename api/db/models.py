"""Modèles SQLAlchemy correspondant au schéma PostgreSQL de DataFlow360."""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
    Text,
    Boolean,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Classe de base des modèles SQLAlchemy."""


class Client(Base):
    """Client mobile money."""

    __tablename__ = "api_clients"

    client_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    age: Mapped[int] = mapped_column(Integer)
    sexe: Mapped[str] = mapped_column(String(20))
    region: Mapped[str] = mapped_column(String(100))
    account_type: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(), nullable=True
    )
    data_origin: Mapped[str] = mapped_column(
        String(24), server_default="unknown"
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="client"
    )
    credit_applications: Mapped[list["CreditApplication"]] = relationship(
        back_populates="client"
    )


class Transaction(Base):
    """Transaction mobile money."""

    __tablename__ = "api_transactions"

    transaction_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    client_id: Mapped[str] = mapped_column(
        ForeignKey("api_clients.client_id"), index=True
    )
    amount: Mapped[float] = mapped_column(Float)
    type: Mapped[str] = mapped_column(String(30))
    channel: Mapped[str] = mapped_column(String(30))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(), index=True
    )
    data_origin: Mapped[str] = mapped_column(
        String(24), server_default="unknown"
    )

    client: Mapped["Client"] = relationship(back_populates="transactions")
    fraud_alert: Mapped["FraudAlert | None"] = relationship(
        back_populates="transaction", uselist=False
    )


class FraudAlert(Base):
    """Alerte générée par le système de détection de fraude."""

    __tablename__ = "api_fraud_alerts"

    alert_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    transaction_id: Mapped[str] = mapped_column(
        ForeignKey("api_transactions.transaction_id"),
        unique=True,
        index=True,
    )

    risk_score: Mapped[float] = mapped_column(Float)

    risk_level: Mapped[str] = mapped_column(String(20))

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    reviewed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    data_origin: Mapped[str] = mapped_column(
        String(24),
        server_default="unknown",
    )

    transaction: Mapped["Transaction"] = relationship(
        back_populates="fraud_alert"
    )


class CreditApplication(Base):
    """Demande de crédit."""

    __tablename__ = "api_credit_applications"

    application_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    client_id: Mapped[str] = mapped_column(
        ForeignKey("api_clients.client_id"), index=True
    )
    requested_amount: Mapped[float] = mapped_column(Float)
    duration: Mapped[int] = mapped_column(Integer)
    income: Mapped[float] = mapped_column(Float)
    expenses: Mapped[float] = mapped_column(Float)
    data_origin: Mapped[str] = mapped_column(
        String(24), server_default="unknown"
    )

    client: Mapped["Client"] = relationship(
        back_populates="credit_applications"
    )
    credit_scores: Mapped[list["CreditScore"]] = relationship(
        back_populates="application"
    )

class CreditScore(Base):
    """Score de risque associé à une demande de crédit."""

    __tablename__ = "api_credit_scores"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    application_id: Mapped[str] = mapped_column(
        ForeignKey("api_credit_applications.application_id"),
        index=True,
    )
    risk_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), server_default=func.now()
    )
    data_origin: Mapped[str] = mapped_column(
        String(24), server_default="unknown"
    )

    application: Mapped["CreditApplication"] = relationship(
        back_populates="credit_scores"
    )
    model_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="simulation",
        server_default="simulation",
    )



class User(Base):
    """Utilisateur de l'API (analyste, admin)."""

    __tablename__ = "api_users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    full_name: Mapped[str] = mapped_column(
        String(120), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(20), server_default="analyst", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default="true", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )