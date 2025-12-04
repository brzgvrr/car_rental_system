from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum, auto
from typing import Optional


class CarStatus(Enum):
    AVAILABLE = auto()
    RESERVED = auto()
    RENTED = auto()
    MAINTENANCE = auto()


class RentalStatus(Enum):
    BOOKED = auto()
    ACTIVE = auto()
    COMPLETED = auto()
    CANCELLED = auto()


@dataclass
class Car:
    id: int
    brand: str
    model: str
    car_class: str
    daily_rate: float
    status: CarStatus = CarStatus.AVAILABLE

    def __str__(self) -> str:
        return (
            f"Car(id={self.id}, {self.brand} {self.model}, "
            f"class={self.car_class}, rate={self.daily_rate}, "
            f"status={self.status.name})"
        )


@dataclass
class Customer:
    id: int
    name: str
    license_number: str
    contact_info: str

    def __str__(self) -> str:
        return (
            f"Customer(id={self.id}, name={self.name}, "
            f"license={self.license_number})"
        )


@dataclass
class Rental:
    id: int
    car: Car
    customer: Customer
    start_date: date
    end_date: date
    status: RentalStatus = RentalStatus.BOOKED
    actual_end_date: Optional[date] = None

    base_fee: float = 0.0
    late_fee: float = 0.0
    fuel_penalty: float = 0.0
    damage_fee: float = 0.0
    total_amount: float = 0.0

    def calculate_fee(
        self,
        fuel_ok: bool,
        damaged: bool,
        actual_end_date: date,
    ) -> float:
        """
        Рассчитать стоимость аренды, штраф за просрочку,
        за топливо и повреждения.
        """
        self.actual_end_date = actual_end_date

        planned_days = (self.end_date - self.start_date).days
        if planned_days <= 0:
            raise ValueError("Неверный период аренды")

        self.base_fee = planned_days * self.car.daily_rate

        # Просрочка
        if actual_end_date > self.end_date:
            late_days = (actual_end_date - self.end_date).days
            # штраф: 150% тарифа за каждый просроченный день
            self.late_fee = late_days * self.car.daily_rate * 1.5
        else:
            self.late_fee = 0.0

        # Штрафы
        self.fuel_penalty = 0.0 if fuel_ok else 50.0
        self.damage_fee = 0.0 if not damaged else 200.0

        self.total_amount = (
            self.base_fee
            + self.late_fee
            + self.fuel_penalty
            + self.damage_fee
        )
        return self.total_amount

    def __str__(self) -> str:
        return (
            f"Rental(id={self.id}, car_id={self.car.id}, "
            f"customer_id={self.customer.id}, "
            f"{self.start_date}=>{self.end_date}, "
            f"status={self.status.name}, total={self.total_amount})"
        )