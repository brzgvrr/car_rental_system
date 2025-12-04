from datetime import date, timedelta

from service import CarRentalService


def main() -> None:
    service = CarRentalService()

    # создаём машины
    car1 = service.add_car("Toyota", "Corolla", "economy", 40.0)
    car2 = service.add_car("BMW", "3 Series", "business", 90.0)

    # регистрируем клиентов
    customer1 = service.register_customer(
        name="Егор Брезговин",
        license_number="AB1234567",
        contact_info="+7-707-777-22-33",
    )

    # ищем доступные машины
    start = date.today()
    end = start + timedelta(days=3)

    print("Доступные авто на 3 дня:")
    for car in service.find_available_cars(start, end):
        print(" ", car)

    # бронирование
    rental = service.reserve_car(
        customer_id=customer1.id,
        car_id=car1.id,
        start_date=start,
        end_date=end,
    )
    print("\nСоздана бронь:", rental)

    # старт аренды
    service.start_rental(rental.id)
    print("Аренда начата. Статус аренды:", rental.status.name)
    print("Статус авто:", rental.car.status.name)

    # возврат без просрочки
    actual_return_date = end
    total = service.return_car(
        rental_id=rental.id,
        actual_end_date=actual_return_date,
        fuel_ok=True,
        damaged=False,
    )

    print("\nМашина возвращена.")
    print("Стоимость аренды:", total)
    print("Базовая:", rental.base_fee)
    print("Штраф за просрочку:", rental.late_fee)
    print("Штраф за топливо:", rental.fuel_penalty)
    print("Штраф за повреждения:", rental.damage_fee)
    print("Текущий статус аренды:", rental.status.name)
    print("Статус авто:", rental.car.status.name)

    # история клиента
    print("\nИстория аренд клиента:")
    for r in service.get_rental_history(customer1.id):
        print(" ", r)

    # пример конфликта по датам
    print("\nПробуем сделать конфликтную бронь:")
    r1 = service.reserve_car(
        customer_id=customer1.id,
        car_id=car2.id,
        start_date=start,
        end_date=end,
    )
    print("  Бронь r1 создана.")

    try:
        service.reserve_car(
            customer_id=customer1.id,
            car_id=car2.id,
            start_date=start + timedelta(days=1),
            end_date=end + timedelta(days=2),
        )
    except ValueError as exc:
        print("  Ожидаемая ошибка при конфликте:", exc)


if __name__ == "__main__":
    main()