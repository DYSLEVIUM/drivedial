from typing import List, Optional, TypedDict


class CarSpec(TypedDict):
    id: str
    name: str
    brand: str
    price: int
    price_display: str
    fuel_type: str
    transmission: str
    mileage: str
    year: int
    color: List[str]
    features: List[str]
    availability: str
    location: str


CAR_INVENTORY: List[CarSpec] = [
    {
        "id": "swift-vxi",
        "name": "Maruti Swift VXi",
        "brand": "Maruti Suzuki",
        "price": 750000,
        "price_display": "₹7.5 Lakh",
        "fuel_type": "Petrol",
        "transmission": "Manual",
        "mileage": "22.56 kmpl",
        "year": 2024,
        "color": ["Pearl Arctic White", "Magma Grey", "Sizzling Red"],
        "features": ["Touchscreen Infotainment", "Dual Airbags", "ABS with EBD", "Rear Parking Sensors"],
        "availability": "Immediate",
        "location": "Mumbai",
    },
    {
        "id": "swift-zxi",
        "name": "Maruti Swift ZXi",
        "brand": "Maruti Suzuki",
        "price": 895000,
        "price_display": "₹8.95 Lakh",
        "fuel_type": "Petrol",
        "transmission": "Manual",
        "mileage": "22.56 kmpl",
        "year": 2024,
        "color": ["Luster Blue", "Pearl Arctic White", "Solid Fire Red"],
        "features": ["9-inch Touchscreen", "6 Airbags", "Cruise Control", "Auto Climate Control", "LED Headlamps"],
        "availability": "Immediate",
        "location": "Mumbai",
    },
    {
        "id": "city-v",
        "name": "Honda City V",
        "brand": "Honda",
        "price": 1200000,
        "price_display": "₹12 Lakh",
        "fuel_type": "Petrol",
        "transmission": "CVT",
        "mileage": "18.4 kmpl",
        "year": 2024,
        "color": ["Platinum White Pearl", "Radiant Red Metallic", "Golden Brown Metallic"],
        "features": ["8-inch Touchscreen", "Honda Connect", "6 Airbags", "Lane Watch Camera"],
        "availability": "2-3 days",
        "location": "Mumbai",
    },
    {
        "id": "city-zx",
        "name": "Honda City ZX",
        "brand": "Honda",
        "price": 1550000,
        "price_display": "₹15.5 Lakh",
        "fuel_type": "Petrol",
        "transmission": "CVT",
        "mileage": "18.4 kmpl",
        "year": 2024,
        "color": ["Meteoroid Grey Metallic", "Platinum White Pearl", "Lunar Silver Metallic"],
        "features": ["Sunroof", "Wireless Charging", "8-inch Touchscreen", "ADAS", "Ventilated Seats"],
        "availability": "Immediate",
        "location": "Mumbai",
    },
    {
        "id": "xuv700-mx",
        "name": "Mahindra XUV700 MX",
        "brand": "Mahindra",
        "price": 1399000,
        "price_display": "₹13.99 Lakh",
        "fuel_type": "Petrol",
        "transmission": "Manual",
        "mileage": "13 kmpl",
        "year": 2024,
        "color": ["Everest White", "Midnight Black"],
        "features": ["7-inch Touchscreen", "Dual Airbags", "AdrenoX Connect", "Multi-mode Steering"],
        "availability": "1-2 weeks",
        "location": "Pune",
    },
    {
        "id": "xuv700-ax5",
        "name": "Mahindra XUV700 AX5",
        "brand": "Mahindra",
        "price": 1699000,
        "price_display": "₹16.99 Lakh",
        "fuel_type": "Diesel",
        "transmission": "Automatic",
        "mileage": "16 kmpl",
        "year": 2024,
        "color": ["Red Rage", "Dazzling Silver", "Electric Blue"],
        "features": ["10.25-inch Touchscreen", "ADAS Level 2", "Panoramic Sunroof", "7 Airbags", "Smart Door Handles"],
        "availability": "Immediate",
        "location": "Mumbai",
    },
    {
        "id": "xuv700-ax7",
        "name": "Mahindra XUV700 AX7 L",
        "brand": "Mahindra",
        "price": 2450000,
        "price_display": "₹24.5 Lakh",
        "fuel_type": "Diesel",
        "transmission": "Automatic",
        "mileage": "16 kmpl",
        "year": 2024,
        "color": ["Napoli Black", "Everest White", "Dazzling Silver"],
        "features": ["Dual 10.25-inch Screens", "3D Sound by Sony", "ADAS Level 2", "Flush Door Handles", "360 Camera"],
        "availability": "3-4 weeks",
        "location": "Mumbai",
    },
    {
        "id": "creta-e",
        "name": "Hyundai Creta E",
        "brand": "Hyundai",
        "price": 1100000,
        "price_display": "₹11 Lakh",
        "fuel_type": "Petrol",
        "transmission": "Manual",
        "mileage": "16.8 kmpl",
        "year": 2024,
        "color": ["Phantom Black", "Atlas White", "Titan Grey"],
        "features": ["8-inch Touchscreen", "Wireless Android Auto", "6 Airbags", "Rear Parking Camera"],
        "availability": "Immediate",
        "location": "Delhi",
    },
    {
        "id": "creta-sx",
        "name": "Hyundai Creta SX(O)",
        "brand": "Hyundai",
        "price": 1750000,
        "price_display": "₹17.5 Lakh",
        "fuel_type": "Diesel",
        "transmission": "Automatic",
        "mileage": "21.4 kmpl",
        "year": 2024,
        "color": ["Abyss Black", "Robust Emerald", "Fiery Red"],
        "features": ["Panoramic Sunroof", "Bose Premium Sound", "Ventilated Seats", "ADAS", "10.25-inch Display"],
        "availability": "1 week",
        "location": "Mumbai",
    },
    {
        "id": "baleno-zeta",
        "name": "Maruti Baleno Zeta",
        "brand": "Maruti Suzuki",
        "price": 920000,
        "price_display": "₹9.2 Lakh",
        "fuel_type": "Petrol",
        "transmission": "Manual",
        "mileage": "22.35 kmpl",
        "year": 2024,
        "color": ["Nexa Blue", "Arctic White", "Splendid Silver"],
        "features": ["9-inch SmartPlay Pro+", "360 View Camera", "6 Airbags", "Head-Up Display"],
        "availability": "Immediate",
        "location": "Mumbai",
    },
]


def search_cars_by_budget(min_price: int = 0, max_price: int = 50000000) -> List[CarSpec]:
    return [car for car in CAR_INVENTORY if min_price <= car["price"] <= max_price]


def search_cars_by_brand(brand: str) -> List[CarSpec]:
    return [car for car in CAR_INVENTORY if brand.lower() in car["brand"].lower()]


def search_cars_by_name(name: str) -> List[CarSpec]:
    return [car for car in CAR_INVENTORY if name.lower() in car["name"].lower()]


def get_car_by_id(car_id: str) -> Optional[CarSpec]:
    for car in CAR_INVENTORY:
        if car["id"] == car_id:
            return car
    return None


def search_cars(
    budget_min: Optional[int] = None,
    budget_max: Optional[int] = None,
    brand: Optional[str] = None,
    fuel_type: Optional[str] = None,
    transmission: Optional[str] = None,
) -> List[CarSpec]:
    results = CAR_INVENTORY.copy()

    if budget_min is not None:
        results = [c for c in results if c["price"] >= budget_min]
    if budget_max is not None:
        results = [c for c in results if c["price"] <= budget_max]
    if brand:
        results = [c for c in results if brand.lower() in c["brand"].lower()]
    if fuel_type:
        results = [c for c in results if fuel_type.lower() ==
                   c["fuel_type"].lower()]
    if transmission:
        results = [c for c in results if transmission.lower() ==
                   c["transmission"].lower()]

    return results
