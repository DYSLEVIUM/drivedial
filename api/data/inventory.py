from typing import List, Optional, TypedDict
false= False
true=True
null=None

class CarSpec(TypedDict):
    slug: str
    name: str
    model_name: str
    variant_name: str
    brand_name: str
    market_price: int
    acko_price: int
    savings: int
    fuel_type: str
    transmission: str
    seating_capacity: int
    mileage: str
    color: List[str]
    features: List[str]
    waiting_period: str
    is_express_delivery: bool


CAR_INVENTORY: List[CarSpec] = [
  {
    "slug": "honda-city-15-sports-cvt",
    "name": "Honda City 1.5 Sports CVT",
    "model_name": "City",
    "variant_name": "1.5 Sports CVT",
    "brand_name": "Honda",
    "market_price": 1674200,
    "acko_price": 1613651,
    "savings": 60549,
    "fuel_type": "Petrol",
    "transmission": "CVT",
    "seating_capacity": 5,
    "mileage": "18.4 kmpl",
    "color": [
      "meteoroid-grey-metallic",
      "platinum-white-pearl",
      "radiant-red-metallic",
      "obsidian-blue-pearl",
      "lunar-silver-metallic"
    ],
    "features": [
      "4 Airbags",
      "Rear Camera",
      "Paddle Shifters",
      "8-inch Touchscreen"
    ],
    "waiting_period": "20 days",
    "is_express_delivery": true
  },
  {
    "slug": "honda-elevate-zx-black-edition-cvt",
    "name": "Honda Elevate ZX Black Edition CVT",
    "model_name": "Elevate",
    "variant_name": "ZX Black Edition CVT",
    "brand_name": "Honda",
    "market_price": 1890705,
    "acko_price": 1705911,
    "savings": 184794,
    "fuel_type": "Petrol",
    "transmission": "CVT",
    "seating_capacity": 5,
    "mileage": "16.92 kmpl",
    "color": [
      "crystal-black-pearl"
    ],
    "features": [
      "ADAS Level 2",
      "6 Airbags",
      "10.25-inch Touchscreen",
      "Sunroof"
    ],
    "waiting_period": "20 days",
    "is_express_delivery": true
  },
  {
    "slug": "honda-amaze-vx-cvt",
    "name": "Honda Amaze VX CVT",
    "model_name": "Amaze",
    "variant_name": "VX CVT",
    "brand_name": "Honda",
    "market_price": 1033642,
    "acko_price": 931743,
    "savings": 101899,
    "fuel_type": "Petrol",
    "transmission": "CVT",
    "seating_capacity": 5,
    "mileage": "18.3 kmpl",
    "color": [
      "lunar-silver",
      "meteoroid-grey",
      "radiant-red",
      "obsidian-blue",
      "platinum-white"
    ],
    "features": [
      "Automatic Climate Control",
      "Rear Camera",
      "Paddle Shifters",
      "LED Projector Headlamps"
    ],
    "waiting_period": "20 days",
    "is_express_delivery": true
  },
  {
    "slug": "hyundai-grand-i10-nios-12-sportz-cng",
    "name": "Hyundai Grand i10 Nios Sportz CNG",
    "model_name": "Grand i10 Nios",
    "variant_name": "1.2 Sportz CNG",
    "brand_name": "Hyundai",
    "market_price": 872719,
    "acko_price": 772606,
    "savings": 100113,
    "fuel_type": "CNG",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "27 km/kg",
    "color": [
      "titan-grey",
      "typhoon-silver",
      "aqua-teal",
      "spark-green",
      "amazon-grey",
      "fiery-red",
      "atlas-white"
    ],
    "features": [
      "6 Airbags",
      "Automatic Climate Control",
      "Rear AC Vents",
      "Projector Headlamps"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "hyundai-i20-12-astao-ivt",
    "name": "Hyundai i20 Asta(O) IVT",
    "model_name": "i20",
    "variant_name": "1.2 Asta(O) IVT",
    "brand_name": "Hyundai",
    "market_price": 1204705.7,
    "acko_price": 1082479.7,
    "savings": 122226,
    "fuel_type": "Petrol",
    "transmission": "CVT",
    "seating_capacity": 5,
    "mileage": "19.65 kmpl",
    "color": [
      "amazon-grey",
      "fiery-red",
      "atlas-white",
      "titan-grey",
      "typhoon-silver",
      "starry-night",
      "fiery-red-with-abyss-black-roof",
      "atlas-white-with-abyss-black-roof"
    ],
    "features": [
      "Sunroof",
      "6 Airbags",
      "Bose Audio System",
      "Wireless Charger"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "hyundai-creta-n-line-n10-dct",
    "name": "Hyundai Creta N Line N10 DCT",
    "model_name": "Creta N Line",
    "variant_name": "N10 DCT",
    "brand_name": "Hyundai",
    "market_price": 2313072.55,
    "acko_price": 2186508.55,
    "savings": 126564,
    "fuel_type": "Petrol",
    "transmission": "DCT",
    "seating_capacity": 5,
    "mileage": "18.2 kmpl",
    "color": [
      "atlas-white-with-black-roof",
      "shadow-grey-with-black-roof",
      "thunder-blue-with-black-roof",
      "titan-grey-matte",
      "atlas-white",
      "abyss-black"
    ],
    "features": [
      "ADAS Level 2",
      "360 Camera",
      "Ventilated Seats",
      "Panoramic Sunroof"
    ],
    "waiting_period": "90 days",
    "is_express_delivery": true
  },
  {
    "slug": "hyundai-verna-15-sx-turbo-dct",
    "name": "Hyundai Verna 1.5 SX Turbo DCT",
    "model_name": "Verna",
    "variant_name": "1.5 SX Turbo DCT",
    "brand_name": "Hyundai",
    "market_price": 1828080.39,
    "acko_price": 1684064.39,
    "savings": 144016,
    "fuel_type": "Petrol",
    "transmission": "DCT",
    "seating_capacity": 5,
    "mileage": "20.6 kmpl",
    "color": [
      "starry-night",
      "tellurian-brown",
      "atlas-white",
      "abyss-black",
      "typhoon-silver",
      "fiery-red",
      "titan-grey",
      "fiery-red-with-black-roof",
      "atlas-white-with-black-roof"
    ],
    "features": [
      "6 Airbags",
      "Front Parking Sensors",
      "Sunroof",
      "Ambient Lighting"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "hyundai-exter-12-sx-cng",
    "name": "Hyundai Exter SX CNG",
    "model_name": "Exter",
    "variant_name": "1.2 SX CNG",
    "brand_name": "Hyundai",
    "market_price": 981912,
    "acko_price": 850969,
    "savings": 130943,
    "fuel_type": "CNG",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "27.1 km/kg",
    "color": [
      "titan-grey",
      "abyss-black",
      "ranger-khaki",
      "fiery-red",
      "altas-white",
      "starry-night",
      "cosmic-blue"
    ],
    "features": [
      "Sunroof",
      "6 Airbags",
      "Automatic Climate Control",
      "8-inch Touchscreen"
    ],
    "waiting_period": "20 days",
    "is_express_delivery": true
  },
  {
    "slug": "hyundai-tucson-20-signature-4wd-at-diesel",
    "name": "Hyundai Tucson Signature 4WD AT Diesel",
    "model_name": "Tucson",
    "variant_name": "2.0 Signature 4WD AT Diesel",
    "brand_name": "Hyundai",
    "market_price": 3982015.97,
    "acko_price": 3889924.97,
    "savings": 92091,
    "fuel_type": "Diesel",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "15 kmpl",
    "color": [
      "polar-white-dual-tone",
      "fiery-red-dual-tone",
      "fiery-red",
      "amazon-grey",
      "phantom-black",
      "starry-night",
      "polar-white"
    ],
    "features": [
      "ADAS Level 2",
      "AWD",
      "Heated & Cooled Seats",
      "Panoramic Sunroof"
    ],
    "waiting_period": "300 days",
    "is_express_delivery": false
  },
  {
    "slug": "kia-sonet-15-htx-at",
    "name": "Kia Sonet 1.5 HTX AT",
    "model_name": "Sonet",
    "variant_name": "1.5 HTX AT",
    "brand_name": "Kia",
    "market_price": 1420702.22,
    "acko_price": 1368840.63,
    "savings": 51861.59,
    "fuel_type": "Diesel",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "19 kmpl",
    "color": [
      "aurora-black-pearl",
      "pewter-olive",
      "imperial-blue",
      "glacier-white-pearl",
      "sparkling-silver",
      "gravity-grey"
    ],
    "features": [
      "Sunroof",
      "Ventilated Seats",
      "6 Airbags",
      "Leatherette Seats"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "kia-seltos-15-gtx-plus-dct-gdi",
    "name": "Kia Seltos 1.5 GTX Plus DCT GDi",
    "model_name": "Seltos",
    "variant_name": "1.5 GTX Plus DCT GDi",
    "brand_name": "Kia",
    "market_price": 2240266.85,
    "acko_price": 2152053.39,
    "savings": 88213.46,
    "fuel_type": "Petrol",
    "transmission": "DCT",
    "seating_capacity": 5,
    "mileage": "17.9 kmpl",
    "color": [
      "pewter-olive",
      "imperial-blue",
      "glacier-white-pearl",
      "gravity-grey",
      "sparkling-silver",
      "aurora-black-pearl",
      "glacier-white-pearl-with-aurora-black-pearl-roof"
    ],
    "features": [
      "ADAS Level 2",
      "360 Camera",
      "Panoramic Sunroof",
      "Dual Zone Climate Control"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "kia-carens-15-premiumo-7-str-diesel",
    "name": "Kia Carens 1.5 Premium(O) 7 STR Diesel",
    "model_name": "Carens",
    "variant_name": "1.5 Premium(O) 7 STR Diesel",
    "brand_name": "Kia",
    "market_price": 1506579.38,
    "acko_price": 1459793.38,
    "savings": 46786,
    "fuel_type": "Diesel",
    "transmission": "Manual",
    "seating_capacity": 7,
    "mileage": "17 kmpl",
    "color": [
      "pewter-olive",
      "clear-white",
      "gravity-grey",
      "sparkling-silver",
      "aurora-black-pearl",
      "imperial-blue"
    ],
    "features": [
      "6 Airbags",
      "Rear Camera",
      "All Row AC Vents",
      "8-inch Touchscreen"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "mahindra-thar-roxx-22-mx5-4wd-diesel",
    "name": "Mahindra Thar Roxx MX5 4WD Diesel",
    "model_name": "Thar Roxx",
    "variant_name": "2.2 MX5 4WD Diesel",
    "brand_name": "Mahindra",
    "market_price": 2295495,
    "acko_price": 2220011,
    "savings": 75484,
    "fuel_type": "Diesel",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "15 kmpl",
    "color": [
      "everest-white",
      "battleship-grey",
      "tango-red",
      "nebula-blue",
      "burnt-sienna",
      "deep-forest",
      "stealth-black"
    ],
    "features": [
      "4WD",
      "Sunroof",
      "10.25-inch Touchscreen",
      "Cruise Control"
    ],
    "waiting_period": "280 days",
    "is_express_delivery": false
  },
  {
    "slug": "mahindra-scorpio-n-20-z8l-at-petrol",
    "name": "Mahindra Scorpio-N Z8L AT Petrol",
    "model_name": "Scorpio-N",
    "variant_name": "2.0 Z8L AT Petrol",
    "brand_name": "Mahindra",
    "market_price": 2537186,
    "acko_price": 2464868,
    "savings": 72318,
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "seating_capacity": 7,
    "mileage": "12 kmpl",
    "color": [
      "royal-gold",
      "red-rage",
      "napoli-black",
      "everest-white",
      "grand-canyon",
      "deep-forest",
      "dazzling-silver"
    ],
    "features": [
      "ADAS Level 2",
      "6-Way Power Seat",
      "12 Speaker Audio",
      "Front Camera"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "mahindra-xuv700-22-ax7-luxury-pack-7-str-diesel",
    "name": "Mahindra XUV700 AX7 Luxury Pack 7 STR Diesel",
    "model_name": "XUV700",
    "variant_name": "2.2 AX7 Luxury Pack 7 STR Diesel",
    "brand_name": "Mahindra",
    "market_price": 2588201,
    "acko_price": 2524738,
    "savings": 63463,
    "fuel_type": "Diesel",
    "transmission": "Manual",
    "seating_capacity": 7,
    "mileage": "12 kmpl",
    "color": [
      "stealth-black",
      "midnight-black",
      "red-rage-with-black-roof",
      "midnight-black-with-black-roof",
      "everest-white-with-black-roof",
      "electric-blue-with-black-roof",
      "dazzling-silver-with-black-roof",
      "napoli-black",
      "everest-white",
      "dazzling-silver"
    ],
    "features": [
      "ADAS Level 2",
      "360 Camera",
      "Panoramic Sunroof",
      "Sony 3D Audio"
    ],
    "waiting_period": "1095 days",
    "is_express_delivery": true
  },
  {
    "slug": "mahindra-xev-9e-pack-two-79kwh",
    "name": "Mahindra XEV 9e Pack Two 79kWh",
    "model_name": "XEV 9e",
    "variant_name": "Pack Two 79kWh",
    "brand_name": "Mahindra",
    "market_price": 2851765,
    "acko_price": 2676271,
    "savings": 175494,
    "fuel_type": "Electric",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "663 km/charge",
    "color": [
      "ruby-velvet",
      "nebula-blue",
      "everest-white",
      "deep-forest",
      "tango-red",
      "desert-myst",
      "stealth-black"
    ],
    "features": [
      "Triple Screen Dash",
      "Panoramic Sunroof",
      "Level 2 ADAS",
      "Powered Tailgate"
    ],
    "waiting_period": "84 days",
    "is_express_delivery": false
  },
  {
    "slug": "mahindra-xuv400-el-pro-345-kwh",
    "name": "Mahindra XUV400 EL Pro 34.5 kWh",
    "model_name": "XUV400",
    "variant_name": "EL Pro 34.5 kWh",
    "brand_name": "Mahindra",
    "market_price": 1814191,
    "acko_price": 1355797,
    "savings": 458394,
    "fuel_type": "Electric",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "378 km/charge",
    "color": [
      "napoli-black-with-satin-copper-roof",
      "arctic-blue-with-satin-copper-roof",
      "nebula-blue-with-satin-copper-roof",
      "everest-white-with-satin-copper-roof",
      "galaxy-grey-with-satin-copper-roof",
      "galaxy-grey",
      "everest-white",
      "nebula-blue",
      "arctic-blue",
      "napoli-black"
    ],
    "features": [
      "Sunroof",
      "6 Airbags",
      "Connected Car Tech",
      "Rear Camera"
    ],
    "waiting_period": "30 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-swift-zxi-plus-amt",
    "name": "Maruti Suzuki Swift ZXi Plus AMT",
    "model_name": "Swift",
    "variant_name": "ZXi Plus AMT",
    "brand_name": "Maruti Suzuki",
    "market_price": 984503,
    "acko_price": 944772,
    "savings": 39731,
    "fuel_type": "Petrol",
    "transmission": "AMT",
    "seating_capacity": 5,
    "mileage": "25.75 kmpl",
    "color": [
      "pearl-arctic-white-with-midnight-black-roof",
      "luster-blue-with-midnight-black-roof",
      "sizzling-red-with-midnight-black-roof",
      "pearl-arctic-white",
      "splendid-silver",
      "magma-grey",
      "novel-orange"
    ],
    "features": [
      "9-inch Touchscreen",
      "Wireless Charger",
      "6 Airbags",
      "Cruise Control"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-brezza-zxi-at",
    "name": "Maruti Suzuki Brezza ZXi AT",
    "model_name": "Brezza",
    "variant_name": "ZXi AT",
    "brand_name": "Maruti Suzuki",
    "market_price": 1370360,
    "acko_price": 1342115,
    "savings": 28245,
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "19.8 kmpl",
    "color": [
      "pearl-midnight-black",
      "magma-gray",
      "exuberant-blue",
      "splendid-silver",
      "pearl-arctic-white",
      "splendid-silver-with-midnight-black-roof",
      "sizzling-red-with-midnight-black-roof",
      "brave-khaki-with-arctic-white-roof"
    ],
    "features": [
      "Sunroof",
      "6 Airbags",
      "Paddle Shifters",
      "SmartPlay Pro+"
    ],
    "waiting_period": "70 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-ertiga-vxi-cng",
    "name": "Maruti Suzuki Ertiga VXi CNG",
    "model_name": "Ertiga",
    "variant_name": "VXi CNG",
    "brand_name": "Maruti Suzuki",
    "market_price": 1291682,
    "acko_price": 1263954,
    "savings": 27728,
    "fuel_type": "CNG",
    "transmission": "Manual",
    "seating_capacity": 7,
    "mileage": "26.11 km/kg",
    "color": [
      "pearl-metallic-auburn-red",
      "pearl-arctic-white",
      "pearl-metallic-oxford-blue",
      "metallic-magma-gray",
      "splendid-silver",
      "dignity-brown"
    ],
    "features": [
      "Projector Headlamps",
      "Rear AC Vents",
      "Music System",
      "CNG Kit"
    ],
    "waiting_period": "56 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-grand-vitara-alpha-awd-at",
    "name": "Maruti Suzuki Grand Vitara Alpha AWD AT",
    "model_name": "Grand Vitara",
    "variant_name": "Alpha AWD AT",
    "brand_name": "Maruti Suzuki",
    "market_price": 2075686,
    "acko_price": 1936020,
    "savings": 139666,
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "19.38 kmpl",
    "color": [
      "arctic-white-with-black-roof",
      "opulent-red-with-black-roof",
      "splendid-silver-with-black-roof",
      "arctic-white",
      "splendid-silver",
      "chestnut-brown",
      "grandeur-grey",
      "nexa-bluecelestial"
    ],
    "features": [
      "AllGrip 4WD",
      "Panoramic Sunroof",
      "360 Camera",
      "Ventilated Seats"
    ],
    "waiting_period": "30 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-fronx-10-alpha-turbo-at",
    "name": "Maruti Suzuki Fronx Alpha Turbo AT",
    "model_name": "Fronx",
    "variant_name": "1.0 Alpha Turbo AT",
    "brand_name": "Maruti Suzuki",
    "market_price": 1354420,
    "acko_price": 1290343,
    "savings": 64077,
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "20.01 kmpl",
    "color": [
      "opulent-red-with-bluish-black-roof",
      "splendid-silver-with-bluish-black-roof",
      "earthen-brown-with-bluish-black-roof",
      "bluish-black",
      "opulent-red",
      "earthen-brown",
      "grandeur-grey",
      "splendid-silver",
      "artic-white",
      "nexa-bluecelestial"
    ],
    "features": [
      "HUD (Head Up Display)",
      "360 Camera",
      "6 Airbags",
      "Wireless Charger"
    ],
    "waiting_period": "45 days",
    "is_express_delivery": true
  },
  {
    "slug": "tata-nexon-12-creative-plus-s-cng",
    "name": "Tata Nexon Creative Plus S CNG",
    "model_name": "Nexon",
    "variant_name": "1.2 Creative Plus S CNG",
    "brand_name": "Tata",
    "market_price": 1301263.9,
    "acko_price": 1236422.9,
    "savings": 64841,
    "fuel_type": "CNG",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "17 km/kg",
    "color": [
      "pristine-white",
      "ocean-blue",
      "royal-blue",
      "pure-grey",
      "grassland-beige",
      "daytona-grey"
    ],
    "features": [
      "Twin Cylinder CNG",
      "360 Camera",
      "Sunroof",
      "10.25-inch Infotainment"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "tata-punch-ev-empowered-plus-lr-72",
    "name": "Tata Punch EV Empowered Plus LR 7.2",
    "model_name": "Punch EV",
    "variant_name": "Empowered Plus LR 7.2",
    "brand_name": "Tata",
    "market_price": 1500502,
    "acko_price": 1370710,
    "savings": 129792,
    "fuel_type": "Electric",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "421 km/charge",
    "color": [
      "pristine-white-with-black-roof",
      "fearless-red-with-black-roof",
      "daytona-grey-with-black-roof",
      "seaweed-with-black-roof",
      "empowered-oxide-with-black-roof"
    ],
    "features": [
      "Ventilated Seats",
      "360 Camera",
      "Voice Assisted Sunroof",
      "Fast Charging"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "tata-harrier-fearless-x-plus-dark-edition-at",
    "name": "Tata Harrier Fearless X Plus Dark Edition AT",
    "model_name": "Harrier",
    "variant_name": "Fearless X Plus Dark Edition AT",
    "brand_name": "Tata",
    "market_price": 2951853,
    "acko_price": 2805081,
    "savings": 146772,
    "fuel_type": "Diesel",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "14.6 kmpl",
    "color": [
      "carbon-black"
    ],
    "features": [
      "ADAS Level 2",
      "7 Airbags",
      "360 Camera",
      "Ventilated Seats"
    ],
    "waiting_period": "90 days",
    "is_express_delivery": false
  },
  {
    "slug": "tata-tiago-ev-xz-plus-tech-lux-lr",
    "name": "Tata Tiago EV XZ Plus Tech LUX LR",
    "model_name": "Tiago EV",
    "variant_name": "XZ Plus Tech LUX LR",
    "brand_name": "Tata",
    "market_price": 1196320,
    "acko_price": 1051805,
    "savings": 144515,
    "fuel_type": "Electric",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "315 km/charge",
    "color": [
      "chill-lime-with-black-roof",
      "teal-blue",
      "supernova-copper",
      "arizona-blue",
      "daytona-grey",
      "pristine-white"
    ],
    "features": [
      "Fast Charging",
      "Cruise Control",
      "Auto Headlamps",
      "Rain Sensing Wipers"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "toyota-fortuner-legender-28-4x4-at",
    "name": "Toyota Fortuner Legender 2.8 4x4 AT",
    "model_name": "Fortuner Legender",
    "variant_name": "2.8 4x4 AT",
    "brand_name": "Toyota",
    "market_price": 5991128,
    "acko_price": 5815387,
    "savings": 175741,
    "fuel_type": "Diesel",
    "transmission": "Automatic",
    "seating_capacity": 7,
    "mileage": "14 kmpl",
    "color": [
      "platinum-white-pearl-with-black-roof"
    ],
    "features": [
      "4x4 Drivetrain",
      "Ventilated Seats",
      "Dual Zone Climate Control",
      "Kick Sensor Tailgate"
    ],
    "waiting_period": "60 days",
    "is_express_delivery": false
  },
  {
    "slug": "toyota-urban-cruiser-hyryder-hybrid-v-cvt",
    "name": "Toyota Urban Cruiser Hyryder Hybrid V CVT",
    "model_name": "Urban Cruiser Hyryder",
    "variant_name": "Hybrid V CVT",
    "brand_name": "Toyota",
    "market_price": 2270229,
    "acko_price": 2187905,
    "savings": 82324,
    "fuel_type": "Hybrid",
    "transmission": "CVT",
    "seating_capacity": 5,
    "mileage": "27.97 kmpl",
    "color": [
      "cafe-white",
      "enticing-silver",
      "gaming-grey",
      "sportin-red",
      "midnight-black",
      "cave-black",
      "speedy-blue",
      "speedy-blue-x-midnight-black",
      "enticing-silver-x-midnight-black",
      "sportin-red-x-midnight-black",
      "cafe-white-x-midnight-black"
    ],
    "features": [
      "Strong Hybrid",
      "360 Camera",
      "Ventilated Seats",
      "Panoramic Sunroof"
    ],
    "waiting_period": "56 days",
    "is_express_delivery": true
  },
  {
    "slug": "toyota-glanza-g-cng",
    "name": "Toyota Glanza G CNG",
    "model_name": "Glanza",
    "variant_name": "G CNG",
    "brand_name": "Toyota",
    "market_price": 1022720,
    "acko_price": 945498,
    "savings": 77222,
    "fuel_type": "CNG",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "30.61 km/kg",
    "color": [
      "cafe-white",
      "sportin-red",
      "enticing-silver",
      "gaming-grey",
      "insta-blue"
    ],
    "features": [
      "6 Airbags",
      "Rear Camera",
      "LED Projector Headlamps",
      "Smart Playcast"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "honda-city-15-zx-r-ehev",
    "name": "Honda City 1.5 ZX-R eHEV",
    "model_name": "City",
    "variant_name": "1.5 ZX-R eHEV",
    "brand_name": "Honda",
    "market_price": 2263636,
    "acko_price": 2139968,
    "savings": 123668,
    "fuel_type": "Hybrid",
    "transmission": "CVT",
    "seating_capacity": 5,
    "mileage": "27.1 kmpl",
    "color": [
      "meteoroid-grey-metallic",
      "platinum-white-pearl",
      "radiant-red-metallic",
      "obsidian-blue-pearl",
      "lunar-silver-metallic"
    ],
    "features": [
      "Strong Hybrid",
      "ADAS",
      "Electric Parking Brake",
      "Lane Watch Camera"
    ],
    "waiting_period": "20 days",
    "is_express_delivery": false
  },
  {
    "slug": "honda-elevate-v-r",
    "name": "Honda Elevate V-R",
    "model_name": "Elevate",
    "variant_name": "V-R",
    "brand_name": "Honda",
    "market_price": 1412396,
    "acko_price": 1281820,
    "savings": 130576,
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "15.31 kmpl",
    "color": [
      "platinum-white-pearl",
      "obsidian-blue-pearl",
      "phoenix-orange-pearl",
      "meteoroid-gray-metallic",
      "lunar-silver-metallic",
      "radiant-red-metallic",
      "golden-brown-metallic"
    ],
    "features": [
      "Rear Camera",
      "8-inch Touchscreen",
      "Automatic Climate Control",
      "LED Projector Headlamps"
    ],
    "waiting_period": "20 days",
    "is_express_delivery": true
  },
  {
    "slug": "hyundai-aura-12-sx-cng",
    "name": "Hyundai Aura 1.2 SX CNG",
    "model_name": "Aura",
    "variant_name": "1.2 SX CNG",
    "brand_name": "Hyundai",
    "market_price": 955798,
    "acko_price": 838396,
    "savings": 117402,
    "fuel_type": "CNG",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "28 km/kg",
    "color": [
      "atlas-white",
      "starry-night",
      "aqua-teal",
      "titan-grey",
      "typhoon-silver"
    ],
    "features": [
      "Reverse Camera",
      "8-inch Touchscreen",
      "Projector Headlamps",
      "Alloy Wheels"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "hyundai-alcazar-platinum-diesel",
    "name": "Hyundai Alcazar Platinum Diesel",
    "model_name": "Alcazar",
    "variant_name": "Platinum Diesel",
    "brand_name": "Hyundai",
    "market_price": 2261438,
    "acko_price": 2131329,
    "savings": 130109,
    "fuel_type": "Diesel",
    "transmission": "Manual",
    "seating_capacity": 7,
    "mileage": "20.4 kmpl",
    "color": [
      "atlas-white-with-abyss-black",
      "titan-grey-matte",
      "robust-emerald-matte",
      "abyss-black",
      "atlas-white",
      "starry-night-turbo",
      "fiery-red",
      "robust-emerald-pearl",
      "ranger-khaki"
    ],
    "features": [
      "360 Camera",
      "Panoramic Sunroof",
      "6 Airbags",
      "Bose Audio"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": false
  },
  {
    "slug": "hyundai-creta-electric-excellence",
    "name": "Hyundai Creta Electric Excellence",
    "model_name": "Creta Electric",
    "variant_name": "Excellence",
    "brand_name": "Hyundai",
    "market_price": 2289432,
    "acko_price": 2217016,
    "savings": 72416,
    "fuel_type": "Electric",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "240 km/charge",
    "color": [
      "atlas-white-with-abyss-black-roof",
      "starry-night"
    ],
    "features": [
      "ADAS Level 2",
      "Ventilated Seats",
      "Panoramic Sunroof",
      "360 Camera"
    ],
    "waiting_period": "30 days",
    "is_express_delivery": false
  },
  {
    "slug": "kia-syros-10-htx-plus-turbo-dct",
    "name": "Kia Syros 1.0 HTX Plus Turbo DCT",
    "model_name": "Syros",
    "variant_name": "1.0 HTX Plus Turbo DCT",
    "brand_name": "Kia",
    "market_price": 1671069.1,
    "acko_price": 1547501.3,
    "savings": 123567.8,
    "fuel_type": "Petrol",
    "transmission": "DCT",
    "seating_capacity": 5,
    "mileage": "17 kmpl",
    "color": [
      "aurora-black-pearl",
      "glacier-white-pearl",
      "pewter-olive",
      "imperial-blue",
      "gravity-grey",
      "sparkling-silver",
      "frost-blue"
    ],
    "features": [
      "Panoramic Sunroof",
      "Ventilated Seats",
      "Leatherette Seats",
      "10.25-inch Screen"
    ],
    "waiting_period": "1095 days",
    "is_express_delivery": true
  },
  {
    "slug": "mahindra-be-6-pack-two",
    "name": "Mahindra BE 6 Pack Two",
    "model_name": "BE 6",
    "variant_name": "Pack Two",
    "brand_name": "Mahindra",
    "market_price": 2376387,
    "acko_price": 2187805,
    "savings": 188582,
    "fuel_type": "Electric",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "360 km/charge",
    "color": [
      "desert-myst",
      "stealth-black",
      "everest-white",
      "tango-red",
      "everest-white-satin",
      "deep-forest",
      "desert-myst-satin",
      "firestorm-orange"
    ],
    "features": [
      "ADAS Level 2",
      "Panoramic Sunroof",
      "Dual Zone Climate Control",
      "Connected Car Tech"
    ],
    "waiting_period": "84 days",
    "is_express_delivery": false
  },
  {
    "slug": "maruti-suzuki-alto-k10-vxi-o-amt",
    "name": "Maruti Suzuki Alto K10 VXi (O) AMT",
    "model_name": "Alto K10",
    "variant_name": "VXi (O) AMT",
    "brand_name": "Maruti Suzuki",
    "market_price": 543341,
    "acko_price": 510004,
    "savings": 33337,
    "fuel_type": "Petrol",
    "transmission": "AMT",
    "seating_capacity": 5,
    "mileage": "24.9 kmpl",
    "color": [
      "pearl-midnight-black",
      "metallic-sizzling-red",
      "metallic-granite-grey",
      "premium-earth-gold",
      "metallic-silky-silver",
      "metallic-speedy-blue",
      "solid-white"
    ],
    "features": [
      "SmartPlay Dock",
      "Dual Airbags",
      "Rear Parking Sensors",
      "Keyless Entry"
    ],
    "waiting_period": "45 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-celerio-zxi-plus-amt",
    "name": "Maruti Suzuki Celerio ZXi Plus AMT",
    "model_name": "Celerio",
    "variant_name": "ZXi Plus AMT",
    "brand_name": "Maruti Suzuki",
    "market_price": 751659,
    "acko_price": 716807,
    "savings": 34852,
    "fuel_type": "Petrol",
    "transmission": "AMT",
    "seating_capacity": 5,
    "mileage": "26 kmpl",
    "color": [
      "pearl-midnight-black",
      "speedy-blue",
      "glistening-grey",
      "arctic-white",
      "silky-silver",
      "solid-fire-red",
      "caffeine-brown"
    ],
    "features": [
      "Engine Start/Stop Button",
      "Smartplay Studio",
      "Hill Hold Assist",
      "15-inch Alloys"
    ],
    "waiting_period": "21 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-wagon-r-12-zxi-amt",
    "name": "Maruti Suzuki Wagon R 1.2 ZXi AMT",
    "model_name": "Wagon R",
    "variant_name": "1.2 ZXi AMT",
    "brand_name": "Maruti Suzuki",
    "market_price": 723536,
    "acko_price": 682157,
    "savings": 41379,
    "fuel_type": "Petrol",
    "transmission": "AMT",
    "seating_capacity": 5,
    "mileage": "24.43 kmpl",
    "color": [
      "pearl-midnight-black",
      "solid-white",
      "poolside-blue",
      "magma-grey",
      "silky-silver",
      "nutmeg-brown",
      "prime-gallant-red"
    ],
    "features": [
      "7-inch Touchscreen",
      "Steering Mounted Controls",
      "Dual Airbags",
      "Electrically Adjustable ORVMs"
    ],
    "waiting_period": "56 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-jimny-alpha-at",
    "name": "Maruti Suzuki Jimny Alpha AT",
    "model_name": "Jimny",
    "variant_name": "Alpha AT",
    "brand_name": "Maruti Suzuki",
    "market_price": 1635855,
    "acko_price": 1494563,
    "savings": 141292,
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "seating_capacity": 4,
    "mileage": "16.39 kmpl",
    "color": [
      "nexa-blue",
      "pearl-arctic-white",
      "granite-grey",
      "bluish-black",
      "kinetic-yellow-with-bluish-black-roof",
      "sizzling-red-with-bluish-black-roof"
    ],
    "features": [
      "4x4 AllGrip",
      "Headlamp Washer",
      "Cruise Control",
      "9-inch SmartPlay Pro+"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-eeco-5-str-ac-cng",
    "name": "Maruti Suzuki Eeco 5 STR AC CNG",
    "model_name": "Eeco",
    "variant_name": "5 STR AC CNG",
    "brand_name": "Maruti Suzuki",
    "market_price": 737432,
    "acko_price": 686871,
    "savings": 50561,
    "fuel_type": "CNG",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "26.78 km/kg",
    "color": [
      "pearl-midnight-black",
      "metallic-glistening-grey",
      "solid-white",
      "brisk-blue",
      "metallic-silky-silver"
    ],
    "features": [
      "Air Conditioning",
      "Dual Airbags",
      "ABS with EBD",
      "Reverse Parking Sensors"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-ignis-12-alpha-amt",
    "name": "Maruti Suzuki Ignis 1.2 Alpha AMT",
    "model_name": "Ignis",
    "variant_name": "1.2 Alpha AMT",
    "brand_name": "Maruti Suzuki",
    "market_price": 844763,
    "acko_price": 804882,
    "savings": 39881,
    "fuel_type": "Petrol",
    "transmission": "AMT",
    "seating_capacity": 5,
    "mileage": "20.89 kmpl",
    "color": [
      "nexa-blue-with-black-roof",
      "nexa-blue-with-silver-roof",
      "lucent-orange-with-black-roof",
      "pearl-arctic-white",
      "glistening-grey",
      "turquoise-blue",
      "silky-silver",
      "lucent-orange",
      "nexa-blue"
    ],
    "features": [
      "LED Projector Headlamps",
      "SmartPlay Studio",
      "Automatic Climate Control",
      "Rear Camera"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-s-presso-10-vxi-plus",
    "name": "Maruti Suzuki S-Presso 1.0 VXi Plus",
    "model_name": "S-Presso",
    "variant_name": "1.0 VXi Plus",
    "brand_name": "Maruti Suzuki",
    "market_price": 528215,
    "acko_price": 494278,
    "savings": 33937,
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "24.76 kmpl",
    "color": [
      "pearl-midnight-black",
      "solid-white",
      "metallic-silky-silver",
      "solid-fire-red",
      "metallic-granite-grey",
      "pearl-starry-blue",
      "solid-sizzle-orange"
    ],
    "features": [
      "SmartPlay Studio",
      "Steering Mounted Controls",
      "Dual Airbags",
      "Digital Speedometer"
    ],
    "waiting_period": "21 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-baleno-12-zeta-cng",
    "name": "Maruti Suzuki Baleno 1.2 Zeta CNG",
    "model_name": "Baleno",
    "variant_name": "1.2 Zeta CNG",
    "brand_name": "Maruti Suzuki",
    "market_price": 964073,
    "acko_price": 923540,
    "savings": 40533,
    "fuel_type": "CNG",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "30.61 km/kg",
    "color": [
      "pearl-midnight-black",
      "pearl-arctic-white",
      "splendid-silver",
      "opulent-red",
      "grandeur-grey",
      "luxe-beige",
      "celestial-blue"
    ],
    "features": [
      "6 Airbags",
      "Rear AC Vents",
      "LED Projector Headlamps",
      "Alloy Wheels"
    ],
    "waiting_period": "45 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-xl6-alpha-plus-at",
    "name": "Maruti Suzuki XL6 Alpha Plus AT",
    "model_name": "XL6",
    "variant_name": "Alpha Plus AT",
    "brand_name": "Maruti Suzuki",
    "market_price": 1640830,
    "acko_price": 1597805,
    "savings": 43025,
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "seating_capacity": 6,
    "mileage": "20.27 kmpl",
    "color": [
      "splendid-silver-with-black-roof",
      "brave-khaki-with-black-roof",
      "opulent-red-with-black-roof",
      "pearl-midnight-black",
      "arctic-white",
      "splendid-silver",
      "grandeur-grey",
      "brave-khaki",
      "opulent-red",
      "nexa-blue"
    ],
    "features": [
      "Ventilated Seats",
      "360 Camera",
      "TPMS",
      "Paddle Shifters"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-invicto-alpha-plus-7-str",
    "name": "Maruti Suzuki Invicto Alpha Plus 7 STR",
    "model_name": "Invicto",
    "variant_name": "Alpha Plus 7 STR",
    "brand_name": "Maruti Suzuki",
    "market_price": 3287394,
    "acko_price": 3121995,
    "savings": 165399,
    "fuel_type": "Hybrid",
    "transmission": "CVT",
    "seating_capacity": 7,
    "mileage": "23.24 kmpl",
    "color": [
      "mystic-white",
      "majestic-silver",
      "stellar-bronze",
      "nexa-blue-celestial"
    ],
    "features": [
      "Strong Hybrid",
      "Powered Tailgate",
      "Memory Seats",
      "Panoramic Sunroof"
    ],
    "waiting_period": "90 days",
    "is_express_delivery": false
  },
  {
    "slug": "toyota-rumion-s-cng",
    "name": "Toyota Rumion S CNG",
    "model_name": "Rumion",
    "variant_name": "S CNG",
    "brand_name": "Toyota",
    "market_price": 1323702,
    "acko_price": 1274215,
    "savings": 49487,
    "fuel_type": "CNG",
    "transmission": "Manual",
    "seating_capacity": 7,
    "mileage": "26.11 km/kg",
    "color": [
      "enticing-silver",
      "cafe-white",
      "iconic-grey",
      "rustic-brown",
      "spunky-blue"
    ],
    "features": [
      "Projector Headlamps",
      "Audio System",
      "Steering Mounted Controls",
      "Automatic Climate Control"
    ],
    "waiting_period": "70 days",
    "is_express_delivery": true
  },
  {
    "slug": "toyota-innova-crysta-zx-7-str",
    "name": "Toyota Innova Crysta ZX 7 STR",
    "model_name": "Innova Crysta",
    "variant_name": "ZX 7 STR",
    "brand_name": "Toyota",
    "market_price": 3018315,
    "acko_price": 2961917,
    "savings": 56398,
    "fuel_type": "Diesel",
    "transmission": "Manual",
    "seating_capacity": 7,
    "mileage": "12 kmpl",
    "color": [
      "avant-garde-bronze-metalic",
      "super-white",
      "attitude-black-mica",
      "platinum-white-pearl",
      "silver-metalic"
    ],
    "features": [
      "7 Airbags",
      "Power Driver Seat",
      "Leather Seats",
      "Cruise Control"
    ],
    "waiting_period": "84 days",
    "is_express_delivery": true
  },
  {
    "slug": "toyota-urban-cruiser-taisor-10-v-at",
    "name": "Toyota Urban Cruiser Taisor 1.0 V AT",
    "model_name": "Urban Cruiser Taisor",
    "variant_name": "1.0 V AT",
    "brand_name": "Toyota",
    "market_price": 1385744,
    "acko_price": 1336336,
    "savings": 49408,
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "20.01 kmpl",
    "color": [
      "sportin-red-with-midnight-black-roof",
      "enticing-silver-with-midnight-black-roof",
      "cafe-white-with-midnight-black-roof",
      "gaming-grey",
      "enticing-silver",
      "cafe-white",
      "lucent-orange",
      "enticing-silver-x-midnight-black"
    ],
    "features": [
      "360 Camera",
      "HUD",
      "Paddle Shifters",
      "6 Airbags"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "toyota-camry-sprint-edition",
    "name": "Toyota Camry Sprint Edition",
    "model_name": "Camry",
    "variant_name": "Sprint Edition",
    "brand_name": "Toyota",
    "market_price": 5479016,
    "acko_price": 5362544,
    "savings": 116472,
    "fuel_type": "Petrol",
    "transmission": "CVT",
    "seating_capacity": 5,
    "mileage": "25 kmpl",
    "color": [
      "precious-metal",
      "emotional-red",
      "dark-blue",
      "platinum-white",
      "cement-gray"
    ],
    "features": [
      "9 Airbags",
      "Ventilated Seats",
      "Heads Up Display",
      "3 Zone Climate Control"
    ],
    "waiting_period": "90 days",
    "is_express_delivery": false
  },
  {
    "slug": "tata-curvv-ev-accomplished-plus-s-55",
    "name": "Tata Curvv EV Accomplished Plus S 55",
    "model_name": "Curvv EV",
    "variant_name": "Accomplished Plus S 55",
    "brand_name": "Tata",
    "market_price": 2103315,
    "acko_price": 1910540,
    "savings": 192775,
    "fuel_type": "Electric",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "474 km/charge",
    "color": [
      "pristine-white-with-black-roof",
      "pure-grey-with-black-roof",
      "virtual-sunrise-with-black-roof",
      "flame-red-with-black-roof"
    ],
    "features": [
      "Panoramic Sunroof",
      "360 Camera",
      "Ventilated Seats",
      "V2L Technology"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "tata-curvv-12-accomplished-s-dca-gdi",
    "name": "Tata Curvv 1.2 Accomplished S DCA GDi",
    "model_name": "Curvv",
    "variant_name": "1.2 Accomplished S DCA GDi",
    "brand_name": "Tata",
    "market_price": 1966064,
    "acko_price": 1863730,
    "savings": 102334,
    "fuel_type": "Petrol",
    "transmission": "DCT",
    "seating_capacity": 5,
    "mileage": "17 kmpl",
    "color": [
      "nitro-crimson-with-black-roof",
      "gold-essence-with-black-roof",
      "opera-blue-with-black-roof",
      "flame-red-with-black-roof",
      "pure-grey-with-black-roof",
      "pristine-white-with-black-roof"
    ],
    "features": [
      "ADAS Level 2",
      "Panoramic Sunroof",
      "Powered Tailgate",
      "JBL Audio System"
    ],
    "waiting_period": "90 days",
    "is_express_delivery": false
  },
  {
    "slug": "tata-harrier-pure-x",
    "name": "Tata Harrier Pure X",
    "model_name": "Harrier",
    "variant_name": "Pure X",
    "brand_name": "Tata",
    "market_price": 2016198,
    "acko_price": 1918722,
    "savings": 97476,
    "fuel_type": "Diesel",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "16.8 kmpl",
    "color": [
      "pristine-white",
      "daytona-grey",
      "fearless-red",
      "pure-grey"
    ],
    "features": [
      "10.25-inch Infotainment",
      "Reverse Camera",
      "6 Airbags",
      "LED Projector Headlamps"
    ],
    "waiting_period": "90 days",
    "is_express_delivery": false
  },
  {
    "slug": "tata-safari-adventure-x-plus",
    "name": "Tata Safari Adventure X Plus",
    "model_name": "Safari",
    "variant_name": "Adventure X Plus",
    "brand_name": "Tata",
    "market_price": 2238304,
    "acko_price": 2132673,
    "savings": 105631,
    "fuel_type": "Diesel",
    "transmission": "Manual",
    "seating_capacity": 7,
    "mileage": "16.3 kmpl",
    "color": [
      "supernova-copper",
      "cosmic-gold",
      "pure-grey",
      "frost-white",
      "royal-blue",
      "daytona-grey"
    ],
    "features": [
      "Panoramic Sunroof",
      "360 Camera",
      "Voice Assisted Sunroof",
      "Mood Lighting"
    ],
    "waiting_period": "90 days",
    "is_express_delivery": true
  },
  {
    "slug": "tata-punch-adventure-cng",
    "name": "Tata Punch Adventure CNG",
    "model_name": "Punch",
    "variant_name": "Adventure S CNG",
    "brand_name": "Tata",
    "market_price": 895853,
    "acko_price": 820343,
    "savings": 75510,
    "fuel_type": "CNG",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "26.99 km/kg",
    "color": [
      "calypso-red",
      "tropical-mist",
      "daytona-grey",
      "orcus-white"
    ],
    "features": [
      "Twin Cylinder CNG",
      "Sunroof",
      "7-inch Touchscreen",
      "Push Button Start"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "tata-nexon-ev-empowered-plus-45",
    "name": "Tata Nexon EV Empowered Plus 45",
    "model_name": "Nexon EV",
    "variant_name": "Empowered Plus 45",
    "brand_name": "Tata",
    "market_price": 1793080,
    "acko_price": 1694019,
    "savings": 99061,
    "fuel_type": "Electric",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "489 km/charge",
    "color": [
      "empowered-oxide-with-black-roof",
      "intensi-teal-with-black-roof",
      "flame-red-with-black-roof",
      "daytona-grey-with-black-roof"
    ],
    "features": [
      "V2L & V2V Charging",
      "360 Camera",
      "Ventilated Seats",
      "Cinematic 12.3-inch Screen"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "tata-tiago-xt",
    "name": "Tata Tiago XT",
    "model_name": "Tiago",
    "variant_name": "XT",
    "brand_name": "Tata",
    "market_price": 644858,
    "acko_price": 600232,
    "savings": 44626,
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "19.01 kmpl",
    "color": [
      "ocean-blue",
      "supernova-copper",
      "arizona-blue",
      "daytona-grey",
      "pristine-white"
    ],
    "features": [
      " Harman Infotainment",
      "Steering Mounted Controls",
      "Rear Parking Sensors",
      "Digital Instrument Cluster"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-altroz-12-xz-plus-s-diesel",
    "name": "Tata Altroz 1.5 Creative S Diesel",
    "model_name": "Altroz",
    "variant_name": "1.5 Creative S Diesel",
    "brand_name": "Tata",
    "market_price": 1063431,
    "acko_price": 1007383,
    "savings": 56048,
    "fuel_type": "Diesel",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "23.64 kmpl",
    "color": [
      "pure-grey",
      "ember-glow",
      "royal-blue",
      "pristine-white",
      "dune-glow"
    ],
    "features": [
      "Sunroof",
      "Cruise Control",
      "Rear AC Vents",
      "Connected Car Tech"
    ],
    "waiting_period": "60 days",
    "is_express_delivery": false
  },
  {
    "slug": "tata-tigor-xza-plus-cng",
    "name": "Tata Tigor XZA Plus CNG",
    "model_name": "Tigor",
    "variant_name": "XZA Plus CNG",
    "brand_name": "Tata",
    "market_price": 982830,
    "acko_price": 924743,
    "savings": 58087,
    "fuel_type": "CNG",
    "transmission": "AMT",
    "seating_capacity": 5,
    "mileage": "26.49 km/kg",
    "color": [
      "meteor-bronze",
      "arizona-blue",
      "supernova-copper",
      "daytona-grey",
      "pristine-white"
    ],
    "features": [
      "Automatic CNG",
      "Rain Sensing Wipers",
      "Automatic Headlamps",
      "7-inch Touchscreen"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "honda-city-15-vx-r-cvt",
    "name": "Honda City 1.5 VX-R CVT",
    "model_name": "City",
    "variant_name": "1.5 VX-R CVT",
    "brand_name": "Honda",
    "market_price": 1739875,
    "acko_price": 1581318,
    "savings": 158557,
    "fuel_type": "Petrol",
    "transmission": "CVT",
    "seating_capacity": 5,
    "mileage": "18.4 kmpl",
    "color": [
      "meteoroid-grey-metallic",
      "platinum-white-pearl",
      "radiant-red-metallic",
      "obsidian-blue-pearl",
      "lunar-silver-metallic"
    ],
    "features": [
      "Sunroof",
      "6 Airbags",
      "Lane Watch Camera",
      "Wireless Charger"
    ],
    "waiting_period": "20 days",
    "is_express_delivery": true
  },
  {
    "slug": "honda-amaze-s-cvt",
    "name": "Honda Amaze S CVT",
    "model_name": "Amaze",
    "variant_name": "V CVT",
    "brand_name": "Honda",
    "market_price": 967477,
    "acko_price": 867582,
    "savings": 99895,
    "fuel_type": "Petrol",
    "transmission": "CVT",
    "seating_capacity": 5,
    "mileage": "18.3 kmpl",
    "color": [
      "lunar-silver",
      "radiant-red",
      "meteoroid-grey",
      "platinum-white",
      "obsidian-blue",
      "crystal-black-pearl"
    ],
    "features": [
      "LED Projector Headlamps",
      "Start/Stop Button",
      "Automatic Climate Control",
      "Shark Fin Antenna"
    ],
    "waiting_period": "20 days",
    "is_express_delivery": true
  },
  {
    "slug": "hyundai-i20-n-line-n8-dct",
    "name": "Hyundai i20 N Line N8 DCT",
    "model_name": "i20 N Line",
    "variant_name": "N8 DCT",
    "brand_name": "Hyundai",
    "market_price": 1354891.84,
    "acko_price": 1224693.84,
    "savings": 130198,
    "fuel_type": "Petrol",
    "transmission": "DCT",
    "seating_capacity": 5,
    "mileage": "20 kmpl",
    "color": [
      "atlas-white-with-abyss-black",
      "thunder-blue-with-abyss-black",
      "atlas-white",
      "titan-grey",
      "thunder-blue",
      "starry-night",
      "abyss-black"
    ],
    "features": [
      "Paddle Shifters",
      "Bose Audio",
      "Disc Brakes All 4 Wheels",
      "Sunroof"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "hyundai-creta-15-sx-tech-diesel",
    "name": "Hyundai Creta 1.5 SX Tech Diesel",
    "model_name": "Creta",
    "variant_name": "1.5 SX Tech Diesel",
    "brand_name": "Hyundai",
    "market_price": 2043221.87,
    "acko_price": 1922835.87,
    "savings": 120386,
    "fuel_type": "Diesel",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "21.8 kmpl",
    "color": [
      "starry-night",
      "titan-grey-matte",
      "atlas-white-with-abyss-black-roof",
      "atlas-white",
      "titan-grey",
      "robust-emerald-pearl",
      "fiery-red",
      "ranger-khaki",
      "abyss-black"
    ],
    "features": [
      "ADAS Level 2",
      "Panoramic Sunroof",
      "Bose Premium Sound",
      "Dual Zone Climate Control"
    ],
    "waiting_period": "30 days",
    "is_express_delivery": true
  },
  {
    "slug": "kia-sonet-10-htx-imt",
    "name": "Kia Sonet 1.0 HTX iMT",
    "model_name": "Sonet",
    "variant_name": "1.0 HTX iMT",
    "brand_name": "Kia",
    "market_price": 1245036.55,
    "acko_price": 1177188.08,
    "savings": 67848.47,
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "18.2 kmpl",
    "color": [
      "aurora-black-pearl",
      "pewter-olive",
      "imperial-blue",
      "glacier-white-pearl",
      "sparkling-silver",
      "gravity-grey"
    ],
    "features": [
      "Sunroof",
      "Ventilated Seats",
      "LED Headlamps",
      "Cruise Control"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "mahindra-scorpio-n-22-z4-diesel",
    "name": "Mahindra Scorpio-N Z4 Diesel",
    "model_name": "Scorpio-N",
    "variant_name": "2.2 Z4 Diesel",
    "brand_name": "Mahindra",
    "market_price": 2002003,
    "acko_price": 1955241,
    "savings": 46762,
    "fuel_type": "Diesel",
    "transmission": "Manual",
    "seating_capacity": 7,
    "mileage": "16 kmpl",
    "color": [
      "red-rage",
      "napoli-black",
      "everest-white",
      "deep-forest",
      "dazzling-silver"
    ],
    "features": [
      "Cruise Control",
      "8-inch Touchscreen",
      "Rear AC Vents",
      "Traction Control"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "mahindra-xuv700-20-ax5-7-str",
    "name": "Mahindra XUV700 AX5 7 STR",
    "model_name": "XUV700",
    "variant_name": "2.0 AX5 7 STR",
    "brand_name": "Mahindra",
    "market_price": 2089517,
    "acko_price": 1937371,
    "savings": 152146,
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "seating_capacity": 7,
    "mileage": "15 kmpl",
    "color": [
      "stealth-black",
      "napoli-black",
      "midnight-black",
      "dazzling-silver",
      "everest-white"
    ],
    "features": [
      "Skyroof",
      "Dual HD Screens",
      "LED Headlamps",
      "Cornering Lamps"
    ],
    "waiting_period": "1095 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-brezza-lxi",
    "name": "Maruti Suzuki Brezza LXi",
    "model_name": "Brezza",
    "variant_name": "LXi",
    "brand_name": "Maruti Suzuki",
    "market_price": 924549,
    "acko_price": 901661,
    "savings": 22888,
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "20.15 kmpl",
    "color": [
      "sizzling-red",
      "magma-gray",
      "exuberant-blue",
      "splendid-silver",
      "pearl-arctic-white"
    ],
    "features": [
      "Rear AC Vents",
      "ESP",
      "Hill Hold Assist",
      "Dual Airbags"
    ],
    "waiting_period": "56 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-swift-lxi",
    "name": "Maruti Suzuki Swift LXi",
    "model_name": "Swift",
    "variant_name": "LXi",
    "brand_name": "Maruti Suzuki",
    "market_price": 637892,
    "acko_price": 603052,
    "savings": 34840,
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "24.8 kmpl",
    "color": [
      "pearl-arctic-white",
      "splendid-silver",
      "magma-grey",
      "sizzling-red"
    ],
    "features": [
      "6 Airbags",
      "Projector Headlamps",
      "LED Tail Lamps",
      "Idle Start Stop"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "tata-nexon-12-smart-cng",
    "name": "Tata Nexon Smart CNG",
    "model_name": "Nexon",
    "variant_name": "1.2 Smart CNG",
    "brand_name": "Tata",
    "market_price": 925829,
    "acko_price": 875085,
    "savings": 50744,
    "fuel_type": "CNG",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "24 km/kg",
    "color": [
      "daytona-grey",
      "pristine-white",
      "grassland-beige"
    ],
    "features": [
      "Turbo CNG",
      "6 Airbags",
      "LED Headlamps",
      "Multi-Drive Modes"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "tata-punch-pure",
    "name": "Tata Punch Pure",
    "model_name": "Punch",
    "variant_name": "Pure",
    "brand_name": "Tata",
    "market_price": 611839,
    "acko_price": 558144,
    "savings": 53695,
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "20.09 kmpl",
    "color": [
      "orcus-white",
      "daytona-grey"
    ],
    "features": [
      "Dual Airbags",
      "Front Power Windows",
      "Tilt Steering",
      "90 Degree Opening Doors"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "toyota-urban-cruiser-hyryder-neodrive-s-at",
    "name": "Toyota Urban Cruiser Hyryder Neodrive S AT",
    "model_name": "Urban Cruiser Hyryder",
    "variant_name": "Neodrive S AT",
    "brand_name": "Toyota",
    "market_price": 1571539,
    "acko_price": 1517206,
    "savings": 54333,
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "20.58 kmpl",
    "color": [
      "cafe-white",
      "enticing-silver",
      "gaming-grey",
      "sportin-red",
      "midnight-black",
      "cave-black",
      "speedy-blue"
    ],
    "features": [
      "Cruise Control",
      "Rear Camera",
      "Smart Playcast",
      "Auto AC"
    ],
    "waiting_period": "56 days",
    "is_express_delivery": true
  },
  {
    "slug": "honda-city-15-v-r-cvt",
    "name": "Honda City 1.5 V-R CVT",
    "model_name": "City",
    "variant_name": "1.5 V-R CVT",
    "brand_name": "Honda",
    "market_price": 1622067,
    "acko_price": 1470789,
    "savings": 151278,
    "fuel_type": "Petrol",
    "transmission": "CVT",
    "seating_capacity": 5,
    "mileage": "18.4 kmpl",
    "color": [
      "meteoroid-grey-metallic",
      "platinum-white-pearl",
      "radiant-red-metallic",
      "obsidian-blue-pearl",
      "lunar-silver-metallic"
    ],
    "features": [
      "ADAS Level 2",
      "4 Airbags",
      "8-inch Touchscreen",
      "Paddle Shifters"
    ],
    "waiting_period": "20 days",
    "is_express_delivery": true
  },
  {
    "slug": "hyundai-exter-12-s-amt",
    "name": "Hyundai Exter 1.2 S AMT",
    "model_name": "Exter",
    "variant_name": "1.2 S AMT",
    "brand_name": "Hyundai",
    "market_price": 885798,
    "acko_price": 772950,
    "savings": 112848,
    "fuel_type": "Petrol",
    "transmission": "AMT",
    "seating_capacity": 5,
    "mileage": "19.2 kmpl",
    "color": [
      "titan-grey",
      "abyss-black",
      "ranger-khaki",
      "cosmic-blue",
      "starry-night",
      "altas-white",
      "fiery-red"
    ],
    "features": [
      "6 Airbags",
      "8-inch Touchscreen",
      "Digital Cluster",
      "TPMS"
    ],
    "waiting_period": "20 days",
    "is_express_delivery": true
  },
  {
    "slug": "kia-carens-clavis-15-htk-diesel",
    "name": "Kia Carens 1.5 HTK Diesel",
    "model_name": "Carens",
    "variant_name": "1.5 HTK Diesel",
    "brand_name": "Kia",
    "market_price": 1760651.53,
    "acko_price": 1678325.53,
    "savings": 82326,
    "fuel_type": "Diesel",
    "transmission": "Manual",
    "seating_capacity": 7,
    "mileage": "21 kmpl",
    "color": [
      "glacier-white-pearl",
      "aurora-black-pearl",
      "pewter-olive",
      "gravity-grey",
      "imperial-blue",
      "sparkling-silver",
      "ivory-silver-gloss"
    ],
    "features": [
      "6 Airbags",
      "Rear Camera",
      "8-inch Touchscreen",
      "Alloy Wheels"
    ],
    "waiting_period": "90 days",
    "is_express_delivery": true
  },
  {
    "slug": "mahindra-thar-roxx-20-mx3-at",
    "name": "Mahindra Thar Roxx 2.0 MX3 AT",
    "model_name": "Thar Roxx",
    "variant_name": "2.0 MX3 AT",
    "brand_name": "Mahindra",
    "market_price": 1788953,
    "acko_price": 1732695,
    "savings": 56258,
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "12.4 kmpl",
    "color": [
      "everest-white",
      "tango-red",
      "stealth-black"
    ],
    "features": [
      "10.25-inch Touchscreen",
      "Cruise Control",
      "Rear Camera",
      "Wireless Charger"
    ],
    "waiting_period": "210 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-grand-vitara-delta-cng",
    "name": "Maruti Suzuki Grand Vitara Delta CNG",
    "model_name": "Grand Vitara",
    "variant_name": "Delta CNG",
    "brand_name": "Maruti Suzuki",
    "market_price": 1491235,
    "acko_price": 1439809,
    "savings": 51426,
    "fuel_type": "CNG",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "26.6 km/kg",
    "color": [
      "opulent-red",
      "midnight-black",
      "splendid-silver",
      "grandeur-grey",
      "chestnut-brown",
      "celestial-blue",
      "arctic-white"
    ],
    "features": [
      "SmartPlay Pro",
      "Cruise Control",
      "Rear Camera",
      "Push Button Start"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "tata-nexon-15-creative-plus-ps-amt",
    "name": "Tata Nexon 1.5 Creative Plus PS AMT",
    "model_name": "Nexon",
    "variant_name": "1.5 Creative Plus PS AMT",
    "brand_name": "Tata",
    "market_price": 1529005.9,
    "acko_price": 1455912.9,
    "savings": 73093,
    "fuel_type": "Diesel",
    "transmission": "AMT",
    "seating_capacity": 5,
    "mileage": "24.08 kmpl",
    "color": [
      "pristine-white-with-black-roof",
      "ocean-blue-with-white-roof",
      "royal-blue-with-black-roof",
      "pure-grey-with-black-roof",
      "grassland-beige-with-black-roof",
      "daytona-grey-with-black-roof",
      "pristine-white",
      "ocean-blue"
    ],
    "features": [
      "Panoramic Sunroof",
      "360 Camera",
      "10.25-inch Infotainment",
      "Front Parking Sensors"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": false
  },
  {
    "slug": "tata-punch-ev-adventure-lr-33",
    "name": "Tata Punch EV Adventure LR 3.3",
    "model_name": "Punch EV",
    "variant_name": "Adventure LR 3.3",
    "brand_name": "Tata",
    "market_price": 1363921,
    "acko_price": 1243834,
    "savings": 120087,
    "fuel_type": "Electric",
    "transmission": "Automatic",
    "seating_capacity": 5,
    "mileage": "421 km/charge",
    "color": [
      "pristine-white",
      "fearless-red",
      "daytona-grey",
      "seaweed"
    ],
    "features": [
      "Long Range Battery",
      "LED Headlamps",
      "Cruise Control",
      "Electronic Parking Brake"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-dzire-vxi-cng",
    "name": "Maruti Suzuki Dzire VXi CNG",
    "model_name": "Dzire",
    "variant_name": "VXi CNG",
    "brand_name": "Maruti Suzuki",
    "market_price": 904882,
    "acko_price": 877295,
    "savings": 27587,
    "fuel_type": "CNG",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "31.12 km/kg",
    "color": [
      "splendid-silver",
      "arctic-white",
      "nutmeg-brown",
      "magma-grey",
      "gallant-red",
      "alluring-blue",
      "bluish-black"
    ],
    "features": [
      "Rear AC Vents",
      "Audio System with Bluetooth",
      "Steering Mounted Controls",
      "Electrically Adjustable ORVMs"
    ],
    "waiting_period": "56 days",
    "is_express_delivery": true
  },
  {
    "slug": "toyota-rumion-v-at-neo-drive",
    "name": "Toyota Rumion V AT Neo Drive",
    "model_name": "Rumion",
    "variant_name": "V AT Neo Drive",
    "brand_name": "Toyota",
    "market_price": 1579892,
    "acko_price": 1521651,
    "savings": 58241,
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "seating_capacity": 7,
    "mileage": "20.11 kmpl",
    "color": [
      "enticing-silver",
      "cafe-white",
      "iconic-grey",
      "rustic-brown",
      "spunky-blue"
    ],
    "features": [
      "Paddle Shifters",
      "Cruise Control",
      "Rear Camera",
      "Toyota i-Connect"
    ],
    "waiting_period": "84 days",
    "is_express_delivery": true
  },
  {
    "slug": "hyundai-verna-15-sx-turbo",
    "name": "Hyundai Verna 1.5 SX Turbo",
    "model_name": "Verna",
    "variant_name": "1.5 SX Turbo",
    "brand_name": "Hyundai",
    "market_price": 1690034.33,
    "acko_price": 1549627.33,
    "savings": 140407,
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "20 kmpl",
    "color": [
      "fiery-red-with-black-roof",
      "starry-night",
      "tellurian-brown",
      "atlas-white",
      "abyss-black",
      "atlas-white-with-black-roof",
      "typhoon-silver",
      "fiery-red",
      "titan-grey"
    ],
    "features": [
      "1.5L Turbo Engine",
      "Sunroof",
      "6 Airbags",
      "Front Parking Sensors"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "tata-altroz-12-creative-cng",
    "name": "Tata Altroz 1.2 Creative CNG",
    "model_name": "Altroz",
    "variant_name": "1.2 Creative CNG",
    "brand_name": "Tata",
    "market_price": 1006923,
    "acko_price": 952808,
    "savings": 54115,
    "fuel_type": "CNG",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "26.2 km/kg",
    "color": [
      "pure-grey",
      "ember-glow",
      "royal-blue",
      "pristine-white",
      "dune-glow"
    ],
    "features": [
      "Twin Cylinder CNG",
      "Automatic Climate Control",
      "Rear Camera",
      "Projector Headlamps"
    ],
    "waiting_period": "60 days",
    "is_express_delivery": true
  },
  {
    "slug": "mahindra-xuv-3xo-12-ax5",
    "name": "Mahindra XUV 3XO 1.2 AX5",
    "model_name": "XUV 3XO",
    "variant_name": "1.2 AX5",
    "brand_name": "Mahindra",
    "market_price": 1173671,
    "acko_price": 1124644,
    "savings": 49027,
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "18.89 kmpl",
    "color": [
      "citrine-yellow",
      "deep-forest",
      "everest-white",
      "stealth-black",
      "galaxy-grey",
      "nebula-blue",
      "dune-beige",
      "tango-red"
    ],
    "features": [
      "Dual Zone Climate Control",
      "Rear Camera",
      "10.25-inch Infotainment",
      "Connected Car Tech"
    ],
    "waiting_period": "84 days",
    "is_express_delivery": true
  },
  {
    "slug": "kia-seltos-15-htk-plus-o",
    "name": "Kia Seltos 1.5 HTK Plus (O)",
    "model_name": "Seltos",
    "variant_name": "1.5 HTK Plus (O)",
    "brand_name": "Kia",
    "market_price": 1609992.91,
    "acko_price": 1498630.78,
    "savings": 111362.13,
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "17 kmpl",
    "color": [
      "aurora-black-pearl",
      "sparkling-silver",
      "gravity-grey",
      "glacier-white-pearl",
      "imperial-blue",
      "pewter-olive"
    ],
    "features": [
      "Panoramic Sunroof",
      "Automatic Climate Control",
      "Push Button Start",
      "Alloy Wheels"
    ],
    "waiting_period": "42 days",
    "is_express_delivery": true
  },
  {
    "slug": "tata-curvv-12-creative-s",
    "name": "Tata Curvv 1.2 Creative S",
    "model_name": "Curvv",
    "variant_name": "1.2 Creative S",
    "brand_name": "Tata",
    "market_price": 1450943,
    "acko_price": 1369809,
    "savings": 81134,
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "15 kmpl",
    "color": [
      "nitro-crimson",
      "opera-blue",
      "flame-red",
      "daytona-grey",
      "pristine-white"
    ],
    "features": [
      "Panoramic Sunroof",
      "360 Camera",
      "10.25-inch Touchscreen",
      "Rain Sensing Wipers"
    ],
    "waiting_period": "90 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-celerio-vxi-amt",
    "name": "Maruti Suzuki Celerio VXi AMT",
    "model_name": "Celerio",
    "variant_name": "VXi AMT",
    "brand_name": "Maruti Suzuki",
    "market_price": 613700,
    "acko_price": 579198,
    "savings": 34502,
    "fuel_type": "Petrol",
    "transmission": "AMT",
    "seating_capacity": 5,
    "mileage": "26.68 kmpl",
    "color": [
      "speedy-blue",
      "glistening-grey",
      "arctic-white",
      "silky-silver",
      "solid-fire-red",
      "caffeine-brown"
    ],
    "features": [
      "Hill Hold Assist",
      "AGS Transmission",
      "Power Windows",
      "Dual Airbags"
    ],
    "waiting_period": "21 days",
    "is_express_delivery": true
  },
  {
    "slug": "hyundai-aura-12-sx-plus-amt",
    "name": "Hyundai Aura 1.2 SX Plus AMT",
    "model_name": "Aura",
    "variant_name": "1.2 SX Plus AMT",
    "brand_name": "Hyundai",
    "market_price": 930235,
    "acko_price": 818326,
    "savings": 111909,
    "fuel_type": "Petrol",
    "transmission": "AMT",
    "seating_capacity": 5,
    "mileage": "20.1 kmpl",
    "color": [
      "atlas-white",
      "starry-night",
      "aqua-teal",
      "titan-grey",
      "typhoon-silver"
    ],
    "features": [
      "Wireless Charger",
      "Automatic Climate Control",
      "Smart Key",
      "Cruise Control"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "hyundai-i20-12-magna",
    "name": "Hyundai i20 1.2 Magna",
    "model_name": "i20",
    "variant_name": "1.2 Magna",
    "brand_name": "Hyundai",
    "market_price": 812463,
    "acko_price": 698794,
    "savings": 113669,
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "20.35 kmpl",
    "color": [
      "fiery-red",
      "amazon-grey",
      "atlas-white",
      "titan-grey",
      "typhoon-silver",
      "starry-night"
    ],
    "features": [
      "6 Airbags",
      "TPMS",
      "Day/Night IRVM",
      "Rear AC Vents"
    ],
    "waiting_period": "28 days",
    "is_express_delivery": true
  },
  {
    "slug": "maruti-suzuki-baleno-12-sigma",
    "name": "Maruti Suzuki Baleno 1.2 Sigma",
    "model_name": "Baleno",
    "variant_name": "1.2 Sigma",
    "brand_name": "Maruti Suzuki",
    "market_price": 659599,
    "acko_price": 623897,
    "savings": 35702,
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "seating_capacity": 5,
    "mileage": "22.35 kmpl",
    "color": [
      "pearl-midnight-black",
      "pearl-arctic-white",
      "splendid-silver",
      "opulent-red",
      "grandeur-grey",
      "luxe-beige",
      "celestial-blue"
    ],
    "features": [
      "Automatic Climate Control",
      "Dual Airbags",
      "Projector Headlamps",
      "Keyless Entry"
    ],
    "waiting_period": "45 days",
    "is_express_delivery": true
  }
]


def search_cars_by_budget(min_price: int = 0, max_price: int = 50000000) -> List[CarSpec]:
    return [car for car in CAR_INVENTORY if min_price <= car["acko_price"] <= max_price]


def search_cars_by_brand(brand: str) -> List[CarSpec]:
    return [car for car in CAR_INVENTORY if brand.lower() in car["brand_name"].lower()]


def search_cars_by_name(name: str) -> List[CarSpec]:
    return [car for car in CAR_INVENTORY if name.lower() in car["name"].lower()]


def get_car_by_id(car_id: str) -> Optional[CarSpec]:
    for car in CAR_INVENTORY:
        if car["slug"] == car_id:
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
        results = [c for c in results if c["acko_price"] >= budget_min]
    if budget_max is not None:
        results = [c for c in results if c["acko_price"] <= budget_max]
    if brand:
        results = [c for c in results if brand.lower() in c["brand_name"].lower()]
    if fuel_type:
        results = [c for c in results if fuel_type.lower() ==
                   c["fuel_type"].lower()]
    if transmission:
        results = [c for c in results if transmission.lower() ==
                   c["transmission"].lower()]

    return results


def generate_car_url(car_slug: str, color: Optional[str] = None) -> Optional[str]:
    """
    Generate the Acko Drive URL for a car with an optional color parameter.
    
    Args:
        car_slug: The unique slug identifier for the car (e.g., "toyota-rumion-s-cng")
        color: Optional color slug (e.g., "spunky-blue"). If not provided, uses the first available color.
    
    Returns:
        The full URL string, or None if the car is not found or color is invalid.
        Example: "https://ackodrive.com/cars/toyota-rumion-s-cng/?color=spunky-blue"
    """
    car = get_car_by_id(car_slug)
    if car is None:
        return None
    
    available_colors = car.get("color", [])
    
    if color is None:
        # Use the first available color if none specified
        if available_colors:
            color = available_colors[0]
        else:
            # Return URL without color if no colors available
            return f"https://ackodrive.com/cars/{car_slug}/"
    else:
        # Validate that the color is available for this car
        if color not in available_colors:
            return None
    
    return f"https://ackodrive.com/cars/{car_slug}/?color={color}"
