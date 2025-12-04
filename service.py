from datetime import date
from typing import List, Optional

from models import Car, CarStatus, Customer, Rental, RentalStatus
from json_db import load_database, save_database


class CarRentalService:
    def __init__(self) -> None:
        db = load_database()

        # загрузка автомобилей
        self.cars: List[Car] = [
            Car(
                id=car["id"],
                brand=car["brand"],
                model=car["model"],
                car_class=car["car_class"],
                daily_rate=car["daily_rate"],
                status=CarStatus[car["status"]],
            )
            for car in db["cars"]
        ]

        # загрузка клиентов
        self.customers: List[Customer] = [
            Customer(
                id=c["id"],
                name=c["name"],
                license_number=c["license_number"],
                contact_info=c["contact_info"],
            )
            for c in db["customers"]
        ]

        # загрузка аренд
        self.rentals: List[Rental] = []
        for r in db["rentals"]:
            rental = Rental(
                id=r["id"],
                car=self._load_car_ref(r["car_id"]),
                customer=self._load_customer_ref(r["customer_id"]),
                start_date=date.fromisoformat(r["start_date"]),
                end_date=date.fromisoformat(r["end_date"]),
                status=RentalStatus[r["status"]],
                actual_end_date=(
                    date.fromisoformat(r["actual_end_date"])
                    if r["actual_end_date"]
                    else None
                ),
                base_fee=r["base_fee"],
                late_fee=r["late_fee"],
                fuel_penalty=r["fuel_penalty"],
                damage_fee=r["damage_fee"],
                total_amount=r["total_amount"],
            )
            self.rentals.append(rental)

        # генераторы ID
        self._next_car_id = max((c.id for c in self.cars), default=0) + 1
        self._next_customer_id = max((c.id for c in self.customers), default=0) + 1
        self._next_rental_id = max((r.id for r in self.rentals), default=0) + 1

    # JSON хэлперы

    def _load_car_ref(self, car_id: int) -> Car:
        return next(c for c in self.cars if c.id == car_id)

    def _load_customer_ref(self, customer_id: int) -> Customer:
        return next(c for c in self.customers if c.id == customer_id)

    def _save(self) -> None:
        db = {
            "cars": [
                {
                    "id": c.id,
                    "brand": c.brand,
                    "model": c.model,
                    "car_class": c.car_class,
                    "daily_rate": c.daily_rate,
                    "status": c.status.name,
                }
                for c in self.cars
            ],
            "customers": [
                {
                    "id": c.id,
                    "name": c.name,
                    "license_number": c.license_number,
                    "contact_info": c.contact_info,
                }
                for c in self.customers
            ],
            "rentals": [
                {
                    "id": r.id,
                    "car_id": r.car.id,
                    "customer_id": r.customer.id,
                    "start_date": r.start_date.isoformat(),
                    "end_date": r.end_date.isoformat(),
                    "actual_end_date": (
                        r.actual_end_date.isoformat()
                        if r.actual_end_date
                        else None
                    ),
                    "status": r.status.name,
                    "base_fee": r.base_fee,
                    "late_fee": r.late_fee,
                    "fuel_penalty": r.fuel_penalty,
                    "damage_fee": r.damage_fee,
                    "total_amount": r.total_amount,
                }
                for r in self.rentals
            ],
        }
        save_database(db)

    # Бизнес-логика

    # автомобили
    def add_car(self, brand: str, model: str, car_class: str, daily_rate: float) -> Car:
        car = Car(
            id=self._next_car_id,
            brand=brand,
            model=model,
            car_class=car_class,
            daily_rate=daily_rate,
        )
        self._next_car_id += 1
        self.cars.append(car)
        self._save()
        return car

    def remove_car(self, car_id: int) -> None:
        car = self._load_car_ref(car_id)
        for rental in self.rentals:
            if rental.car.id == car_id and rental.status in {
                RentalStatus.BOOKED,
                RentalStatus.ACTIVE,
            }:
                raise ValueError("Нельзя удалить автомобиль: есть активные аренды")

        self.cars.remove(car)
        self._save()

    # клиенты
    def register_customer(self, name: str, license_number: str, contact_info: str) -> Customer:
        customer = Customer(
            id=self._next_customer_id,
            name=name,
            license_number=license_number,
            contact_info=contact_info,
        )
        self._next_customer_id += 1
        self.customers.append(customer)
        self._save()
        return customer

    # поиск машин
    @staticmethod
    def _dates_overlap(start1: date, end1: date, start2: date, end2: date) -> bool:
        return start1 < end2 and start2 < end1  # интервал пересекается

    def _is_car_available(self, car: Car, start_date: date, end_date: date) -> bool:
        if end_date <= start_date:
            raise ValueError("Дата окончания должна быть позже даты начала")

        for rental in self.rentals:
            if rental.car.id != car.id:
                continue
            if rental.status in {RentalStatus.BOOKED, RentalStatus.ACTIVE}:
                if self._dates_overlap(start_date, end_date, rental.start_date, rental.end_date):
                    return False

        return car.status in {CarStatus.AVAILABLE, CarStatus.RESERVED}

    def find_available_cars(
        self,
        start_date: date,
        end_date: date,
        car_class: Optional[str] = None,
        max_rate: Optional[float] = None,
    ) -> List[Car]:
        result = []
        for car in self.cars:
            if car_class and car.car_class != car_class:
                continue
            if max_rate is not None and car.daily_rate > max_rate:
                continue
            if self._is_car_available(car, start_date, end_date):
                result.append(car)
        return result

    # бронирование
    def reserve_car(self, customer_id: int, car_id: int, start_date: date, end_date: date) -> Rental:
        customer = self._load_customer_ref(customer_id)
        car = self._load_car_ref(car_id)

        if not self._is_car_available(car, start_date, end_date):
            raise ValueError("Автомобиль недоступен на выбранные даты")

        rental = Rental(
            id=self._next_rental_id,
            car=car,
            customer=customer,
            start_date=start_date,
            end_date=end_date,
            status=RentalStatus.BOOKED,
        )
        self._next_rental_id += 1

        self.rentals.append(rental)
        car.status = CarStatus.RESERVED
        self._save()
        return rental

    # старт аренды
    def start_rental(self, rental_id: int) -> None:
        rental = self._load_rental(rental_id)
        if rental.status != RentalStatus.BOOKED:
            raise ValueError("Аренду можно начать только со статуса BOOKED")

        rental.status = RentalStatus.ACTIVE
        rental.car.status = CarStatus.RENTED
        self._save()

    def _load_rental(self, rental_id: int) -> Rental:
        return next(r for r in self.rentals if r.id == rental_id)

    # возврат
    def return_car(self, rental_id: int, actual_end_date: date, fuel_ok: bool = True, damaged: bool = False) -> float:
        rental = self._load_rental(rental_id)

        if rental.status != RentalStatus.ACTIVE:
            raise ValueError("Вернуть можно только активную аренду")

        total = rental.calculate_fee(
            fuel_ok=fuel_ok,
            damaged=damaged,
            actual_end_date=actual_end_date,
        )

        rental.status = RentalStatus.COMPLETED
        rental.car.status = CarStatus.AVAILABLE
        self._save()
        return total

    # отмена
    def cancel_reservation(self, rental_id: int) -> None:
        rental = self._load_rental(rental_id)

        if rental.status != RentalStatus.BOOKED:
            raise ValueError("Отменить можно только бронь в статусе BOOKED")

        rental.status = RentalStatus.CANCELLED
        rental.car.status = CarStatus.AVAILABLE
        self._save()

    # списки
    def get_active_rentals(self) -> List[Rental]:
        return [
            r for r in self.rentals
            if r.status in {RentalStatus.BOOKED, RentalStatus.ACTIVE}
        ]

    def get_rental_history(self, customer_id: int) -> List[Rental]:
        return [
            r for r in self.rentals
            if r.customer.id == customer_id
            and r.status in {RentalStatus.COMPLETED, RentalStatus.CANCELLED}
        ]
