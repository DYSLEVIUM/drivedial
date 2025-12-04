import logging
from typing import Dict, List, Optional, Tuple

from api.data.inventory import CAR_INVENTORY, CarSpec

logger = logging.getLogger("store")


class InventoryStore:
    _instance: Optional["InventoryStore"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._inventory = list(CAR_INVENTORY)
        return cls._instance

    @property
    def inventory(self) -> List[CarSpec]:
        return self._inventory

    def add_car(self, car: CarSpec) -> None:
        self._inventory.append(car)
        logger.info(f"Added car: {car['name']}")

    def remove_car(self, car_id: str) -> bool:
        for i, car in enumerate(self._inventory):
            if car["id"] == car_id:
                removed = self._inventory.pop(i)
                logger.info(f"Removed car: {removed['name']}")
                return True
        return False

    def update_car(self, car_id: str, updates: Dict) -> bool:
        for car in self._inventory:
            if car["id"] == car_id:
                car.update(updates)
                logger.info(f"Updated car: {car['name']}")
                return True
        return False

    def get_car(self, car_id: str) -> Optional[CarSpec]:
        for car in self._inventory:
            if car["id"] == car_id:
                return car
        return None

    def search(
        self,
        budget_min: Optional[int] = None,
        budget_max: Optional[int] = None,
        brand: Optional[str] = None,
        fuel_type: Optional[str] = None,
        transmission: Optional[str] = None,
    ) -> List[CarSpec]:
        results = self._inventory.copy()
        if budget_min is not None:
            results = [c for c in results if c["price"] >= budget_min]
        if budget_max is not None:
            results = [c for c in results if c["price"] <= budget_max]
        if brand:
            results = [c for c in results if brand.lower()
                       in c["brand"].lower()]
        if fuel_type:
            results = [c for c in results if fuel_type.lower() ==
                       c["fuel_type"].lower()]
        if transmission:
            results = [c for c in results if transmission.lower() ==
                       c["transmission"].lower()]
        return results

    def search_by_brand(self, brand: str) -> List[CarSpec]:
        return [car for car in self._inventory if brand.lower() in car["brand"].lower()]

    def get_all_brands(self) -> List[str]:
        return list(set(car["brand"] for car in self._inventory))

    def get_all_car_names(self) -> List[str]:
        return [car["name"] for car in self._inventory]

    def get_price_range(self) -> Tuple[int, int]:
        prices = [car["price"] for car in self._inventory]
        return min(prices), max(prices)

    def get_context_summary(self) -> str:
        brands = self.get_all_brands()
        car_names = self.get_all_car_names()
        min_price, max_price = self.get_price_range()

        car_list = ", ".join(car_names[:5])
        if len(car_names) > 5:
            car_list += f" and {len(car_names) - 5} more"

        return (
            f"You are selling cars from brands: {', '.join(brands)}. "
            f"Available models include: {car_list}. "
            f"Price range: ₹{min_price/100000:.1f}L to ₹{max_price/100000:.1f}L."
        )


store = InventoryStore()
