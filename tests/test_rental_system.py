import unittest
from datetime import date

from service import CarRentalService
from models import CarStatus, RentalStatus


class TestCarRentalSystem(unittest.TestCase):

    def setUp(self):
        """
        Перед каждым тестом создаём новую систему
        и очищаем данные, чтобы тесты были независимы.
        """
        self.service = CarRentalService()
        self.service.cars.clear()
        self.service.customers.clear()
        self.service.rentals.clear()

        self.service._next_car_id = 1
        self.service._next_customer_id = 1
        self.service._next_rental_id = 1

    # 1. УСПЕШНОЕ БРОНИРОВАНИЕ - СТАРТ АРЕНДЫ - ВОЗВРАТ

    def test_successful_booking_rental_return(self):
        car = self.service.add_car("Toyota", "Corolla", "economy", 40.0)
        customer = self.service.register_customer("Ivan", "AB123", "123")

        rental = self.service.reserve_car(
            customer.id, car.id,
            date(2025, 1, 10),
            date(2025, 1, 15)
        )

        self.assertEqual(rental.status, RentalStatus.BOOKED)
        self.assertEqual(car.status, CarStatus.RESERVED)

        # старт аренды
        self.service.start_rental(rental.id)

        self.assertEqual(rental.status, RentalStatus.ACTIVE)
        self.assertEqual(car.status, CarStatus.RENTED)

        # возврат вовремя
        total = self.service.return_car(rental.id, date(2025, 1, 15))

        # 5 дней × 40 = 200
        self.assertEqual(total, 5 * 40)

        self.assertEqual(rental.status, RentalStatus.COMPLETED)
        self.assertEqual(car.status, CarStatus.AVAILABLE)

    # 2. КОНФЛИКТ БРОНИРОВАНИЯ — пересекающиеся даты

    def test_booking_conflict(self):
        car = self.service.add_car("BMW", "X5", "lux", 100)
        customer = self.service.register_customer("Ivan", "AB123", "123")

        self.service.reserve_car(
            customer.id, car.id,
            date(2025, 1, 10),
            date(2025, 1, 15)
        )

        with self.assertRaises(ValueError):
            self.service.reserve_car(
                customer.id, car.id,
                date(2025, 1, 14),    # ← пересекается
                date(2025, 1, 20)
            )

    # 3. ПРОСРОЧКА — late fee = 1.5 × тариф × дни просрочки

    def test_late_return_penalty(self):
        car = self.service.add_car("Ford", "Focus", "standard", 50)
        customer = self.service.register_customer("Ivan", "AB123", "123")

        rental = self.service.reserve_car(
            customer.id, car.id,
            date(2025, 5, 1),
            date(2025, 5, 5)
        )

        self.service.start_rental(rental.id)

        # возврат на 2 дня позже
        total = self.service.return_car(rental.id, date(2025, 5, 7))

        base = 4 * 50              # плановые дни
        late = 2 * 50 * 1.5        # просрочка

        self.assertEqual(total, base + late)

    # 4. ОТМЕНА БРОНИ

    def test_cancel_booking(self):
        car = self.service.add_car("Audi", "A4", "business", 70)
        customer = self.service.register_customer("Ivan", "AB123", "123")

        rental = self.service.reserve_car(
            customer.id, car.id,
            date(2025, 2, 1),
            date(2025, 2, 3)
        )

        self.service.cancel_reservation(rental.id)

        self.assertEqual(rental.status, RentalStatus.CANCELLED)
        self.assertEqual(car.status, CarStatus.AVAILABLE)

    # 5. НЕКОРРЕКТНЫЕ ДАТЫ — end_date <= start_date

    def test_invalid_dates(self):
        car = self.service.add_car("Toyota", "Camry", "standard", 60)
        customer = self.service.register_customer("Ivan", "AB123", "123")

        with self.assertRaises(ValueError):
            self.service.reserve_car(
                customer.id, car.id,
                date(2025, 3, 10),
                date(2025, 3, 10)  # одинаковые даты → ошибка
            )

    # 6. НЕЛЬЗЯ НАЧАТЬ АРЕНДУ БЕЗ БРОНИ

    def test_start_rental_without_booking(self):
        car = self.service.add_car("Honda", "Civic", "standard", 55)
        customer = self.service.register_customer("Ivan", "AB123", "123")

        # Создаём бронь, но затем вручную меняем статус — имитация ошибки
        rental = self.service.reserve_car(
            customer.id, car.id,
            date(2025, 4, 1),
            date(2025, 4, 5)
        )

        rental.status = RentalStatus.COMPLETED

        with self.assertRaises(ValueError):
            self.service.start_rental(rental.id)


if __name__ == "__main__":
    unittest.main()
