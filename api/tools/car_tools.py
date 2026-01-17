from typing import Any, Dict

from api.data.store import store
from api.data.inventory import generate_car_url


def search_cars_handler(name: str, arguments: Dict) -> Any:
    return store.search(
        budget_min=arguments.get("budget_min"),
        budget_max=arguments.get("budget_max"),
        brand=arguments.get("brand"),
        model=arguments.get("model"),
        fuel_type=arguments.get("fuel_type"),
        transmission=arguments.get("transmission"),
        sort_by=arguments.get("sort_by", "closest_to_budget"),
        prefer_express=arguments.get("prefer_express", True),
    )


def get_car_details_handler(name: str, arguments: Dict) -> Any:
    return store.get_car(arguments.get("car_id", ""))


def check_availability_handler(name: str, arguments: Dict) -> Any:
    cars = store.search_by_brand(arguments.get("brand", ""))
    return [{"name": c["name"], "waiting_period": c["waiting_period"], "is_express_delivery": c["is_express_delivery"]} for c in cars]


def update_car_display_handler(name: str, arguments: Dict) -> Any:
    car_slug = arguments.get("car_slug", "")
    color = arguments.get("color")
    url = generate_car_url(car_slug, color)
    if url:
        return {"url": url, "car_slug": car_slug, "color": color, "status": "display_updated"}
    else:
        return {"error": "Could not update display. Car or color not found."}
