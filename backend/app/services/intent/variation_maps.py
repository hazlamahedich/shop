"""Synonym and variation mapping layer for natural language understanding.

Story 11-3: Natural Language Variations (AC1, AC2, AC5)
Provides synonym expansion, typo correction, and mode-aware variation handling
to improve pattern-based intent classification accuracy.

Performance: All maps are pre-compiled at module load time into flat dicts
for O(N) str.replace() operations, staying within the <5ms budget.
"""

from __future__ import annotations

import re
from typing import Any

PRODUCT_SYNONYMS: dict[str, list[str]] = {
    "shoes": ["kicks", "sneakers", "footwear", "trainers", "kicks"],
    "pants": ["trousers", "jeans", "bottoms", "slacks", "chinos"],
    "shirt": ["top", "tee", "tshirt", "blouse", "polo", "button-up"],
    "jacket": ["coat", "outerwear", "hoodie", "parka", "windbreaker", "blazer"],
    "dress": ["gown", "frock", "sundress", "maxi", "mini"],
    "hat": ["cap", "beanie", "fedora", "snapback", "beret", "bonnet"],
    "bag": ["purse", "handbag", "backpack", "tote", "clutch", "satchel"],
    "watch": ["timepiece", "wristwatch", "chronograph"],
    "phone": ["smartphone", "mobile", "iphone", "android", "cell"],
    "laptop": ["notebook", "macbook", "computer", "pc"],
    "headphones": ["earbuds", "earphones", "airs", "airpods", "cans"],
    "boots": ["wellies", "wellingtons", "chelsea", "timbs", "work boots"],
    "sandals": ["flip flops", "slides", "thongs", "birkenstocks"],
    "heels": ["pumps", "stilettos", "wedges", "platforms"],
    "socks": ["sockies", "ankle socks", "crew socks"],
    "scarf": ["neck warmer", "shawl", "wrap", "muffler"],
    "gloves": ["mittens", "hand warmers"],
    "belt": ["strap", "waistband"],
    "wallet": ["billfold", "cardholder", "money clip"],
    "sunglasses": ["shades", "sunnies", "aviators", "wayfarers", "ray-bans"],
    "jewelry": ["bling", "ice", "accessories", "trinkets"],
    "ring": ["band", "signet", "solitaire"],
    "necklace": ["chain", "pendant", "choker", "locket"],
    "bracelet": ["bangle", "cuff", "wristband", "charm"],
}

ACTION_SYNONYMS: dict[str, list[str]] = {
    "show me": ["find me", "get me", "pull up", "bring up", "display"],
    "find": ["locate", "search for", "look for", "hunt for", "track down"],
    "looking for": [
        "in the market for",
        "on the hunt for",
        "after",
        "seeking",
        "shopping for",
        "browsing for",
        "scouting for",
    ],
    "need": ["want", "gotta have", "require", "could use", "must get"],
    "do you have": ["got any", "carry", "stock", "sell", "offer", "got"],
    "i want to buy": ["i'll take", "i wanna get", "let me get", "hook me up with"],
    "add to cart": [
        "throw in my cart",
        "put in my basket",
        "add to basket",
        "toss in",
        "drop in my bag",
    ],
    "buy": ["purchase", "cop", "grab", "snag", "score", "scoop", "pick up"],
    "compare": ["stack up", "match up", "weigh", "size up"],
    "cheap": [
        "affordable",
        "budget-friendly",
        "inexpensive",
        "won't break the bank",
        "economical",
        "wallet-friendly",
    ],
    "expensive": ["pricey", "high-end", "premium", "luxury", "fancy", "top-shelf", "luxe"],
}

PRICE_SYNONYMS: dict[str, list[str]] = {
    "on a budget": [
        "watching my wallet",
        "budget-conscious",
        "tight on cash",
        "cheap",
        "affordable",
    ],
    "under": ["less than", "below", "max", "no more than", "up to", "at most", "not over"],
    "over": ["more than", "above", "min", "at least", "starting from", "starting at"],
    "around": ["about", "approximately", "roughly", "in the range of", "close to"],
}

BRAND_SYNONYMS: dict[str, list[str]] = {
    "nike": ["swoosh", "nikes"],
    "adidas": ["three stripes", "adidas yeezy", "yeezys", "yeezy"],
    "jordan": ["jordans", "air jordan", "ajs", "retro jordan", "jumpman"],
    "converse": ["chucks", "converses", "all stars", "chuck taylors"],
    "new balance": ["nb", "new balances"],
    "under armour": ["ua", "underarmour"],
    "north face": ["tnf", "the north face", "northface"],
    "lululemon": ["lulu", "lululemons"],
    "tommy hilfiger": ["tommy", "hilfiger"],
    "ralph lauren": ["ralph", "polo ralph"],
    "h&m": ["h and m", "hm", "h&m"],
    "levis": ["levi", "levi's", "levis"],
}

BRAND_CANONICAL: dict[str, str] = {
    "swoosh": "nike",
    "nikes": "nike",
    "three stripes": "adidas",
    "yeezys": "adidas",
    "yeezy": "adidas",
    "jordans": "jordan",
    "air jordan": "jordan",
    "ajs": "jordan",
    "retro jordan": "jordan",
    "jumpman": "jordan",
    "chucks": "converse",
    "converses": "converse",
    "all stars": "converse",
    "chuck taylors": "converse",
    "nb": "new balance",
    "new balances": "new balance",
    "ua": "under armour",
    "underarmour": "under armour",
    "tnf": "north face",
    "the north face": "north face",
    "northface": "north face",
    "lulu": "lululemon",
    "lululemons": "lululemon",
    "tommy": "tommy hilfiger",
    "hilfiger": "tommy hilfiger",
    "ralph": "ralph lauren",
    "polo ralph": "ralph lauren",
    "h and m": "h&m",
    "hm": "h&m",
    "levi": "levis",
    "levi's": "levis",
}

ALL_BRANDS: set[str] = {
    "nike",
    "adidas",
    "puma",
    "reebok",
    "under armour",
    "new balance",
    "asics",
    "vans",
    "converse",
    "skechers",
    "gucci",
    "prada",
    "chanel",
    "versace",
    "zara",
    "h&m",
    "uniqlo",
    "levis",
    "gap",
    "tommy hilfiger",
    "ralph lauren",
    "north face",
    "patagonia",
    "columbia",
    "lululemon",
    "fila",
    "jordan",
    "yeezy",
    "balenciaga",
}

TYPO_MAP: dict[str, str] = {
    "shose": "shoes",
    "sneker": "sneaker",
    "sneekers": "sneakers",
    "snikers": "sneakers",
    "sho": "show",
    "shot": "shoes",
    "shooes": "shoes",
    "shoos": "shoes",
    "shoe": "shoes",
    "trak": "track",
    "pance": "pants",
    "pant": "pants",
    "trouses": "trousers",
    "jaket": "jacket",
    "jakcet": "jacket",
    "shurt": "shirt",
    "shiirt": "shirt",
    "t-shrit": "t-shirt",
    "tshirt": "t-shirt",
    "teeshirt": "t-shirt",
    "clothng": "clothing",
    "cloths": "clothes",
    "lothes": "clothes",
    "clotes": "clothes",
    "dres": "dress",
    "drss": "dress",
    "hatz": "hats",
    "bagz": "bags",
    "nike": "nike",
    "adida": "adidas",
    "adiddas": "adidas",
    "adiads": "adidas",
    "pumma": "puma",
    "reebok": "reebok",
    "reeboks": "reebok",
    "jordon": "jordan",
    "jordans": "jordan",
    "convers": "converse",
    "sketchers": "skechers",
    "shetchers": "skechers",
    "butget": "budget",
    "budjet": "budget",
    "budgt": "budget",
    "cheao": "cheap",
    "chep": "cheap",
    "expenisve": "expensive",
    "exspensive": "expensive",
    "exprnsive": "expensive",
    "afforadable": "affordable",
    "affrodable": "affordable",
    "affrdable": "affordable",
    "recomend": "recommend",
    "reccomend": "recommend",
    "recommed": "recommend",
    "reccommend": "recommend",
    "surch": "search",
    "serch": "search",
    "searh": "search",
    "saerch": "search",
    "finde": "find",
    "fnd": "find",
    "waant": "want",
    "wannt": "want",
    "ned": "need",
    "nead": "need",
    "kicks": "shoes",
    "trainor": "trainer",
    "sneaks": "sneakers",
    "laptob": "laptop",
    "labtop": "laptop",
    "phne": "phone",
    "phon": "phone",
    "fone": "phone",
    "hedphones": "headphones",
    "hedfones": "headphones",
    "headfones": "headphones",
    "headhpones": "headphones",
    "earbudz": "earbuds",
    "sunglasess": "sunglasses",
    "sunglases": "sunglasses",
    "sunlasses": "sunglasses",
    "wath": "watch",
    "wtach": "watch",
    "wtch": "watch",
    "ringz": "rings",
    "nekclace": "necklace",
    "necklase": "necklace",
    "necklce": "necklace",
    "braceleit": "bracelet",
    "braclet": "bracelet",
    "bracelte": "bracelet",
    "jakets": "jackets",
    "bootsz": "boots",
    "buts": "boots",
    "botos": "boots",
    "sandels": "sandals",
    "sandls": "sandals",
    "sanals": "sandals",
    "heals": "heels",
    "heals": "heels",
    "hees": "heels",
    "sox": "socks",
    "socsk": "socks",
    "gluves": "gloves",
    "glovse": "gloves",
    "blts": "belts",
    "belst": "belts",
    "walelt": "wallet",
    "walit": "wallet",
    "scarfe": "scarf",
    "scaf": "scarf",
    "wher": "where",
    "ordeer": "order",
    "ordr": "order",
    "ordre": "order",
    "orar": "order",
    "trakcing": "tracking",
    "trackign": "tracking",
    "delivry": "delivery",
    "delievery": "delivery",
    "delivary": "delivery",
    "shiping": "shipping",
    "shiping": "shipping",
    "shippment": "shipment",
    "reciept": "receipt",
    "recipt": "receipt",
    "refudn": "refund",
    "refnud": "refund",
    "paymnet": "payment",
    "paymetn": "payment",
    "payement": "payment",
    "returnig": "returning",
    "exhange": "exchange",
    "exchnage": "exchange",
    "canceling": "cancelling",
    "cancle": "cancel",
    "cancl": "cancel",
    "acount": "account",
    "accout": "account",
    "accunt": "account",
    "passwrod": "password",
    "passowrd": "password",
    "passward": "password",
    "loging": "login",
    "loggin": "login",
}

ECOMMERCE_SYNONYMS: dict[str, list[str]] = {
    "cart": ["basket", "bag", "shopping bag", "trolley"],
    "checkout": [
        "pay",
        "purchase",
        "ring me up",
        "let's do this",
        "take my money",
        "i'm ready to buy",
    ],
    "order": ["purchase", "transaction", "shipment", "delivery", "package"],
    "sale": ["discount", "deal", "promo", "promotion", "clearance", "markdown", "special offer"],
    "return": ["send back", "give back", "exchange", "refund"],
    "shipping": ["delivery", "postage", "mailing", "dispatch", "send"],
    "size": ["fit", "sizing", "measurement"],
    "color": ["colour", "shade", "tint", "hue"],
    "in stock": ["available", "on hand", "ready to ship", "in store"],
    "out of stock": ["sold out", "unavailable", "out of stock", "no longer available"],
    "review": ["feedback", "rating", "opinion", "testimonial", "stars"],
    "wishlist": ["saved", "favorites", "favourites", "saved for later"],
}

GENERAL_SYNONYMS: dict[str, list[str]] = {
    "issue": ["problem", "trouble", "difficulty", "complication", "snag", "hiccup", "glitch"],
    "help": ["assist", "support", "guidance", "aid", "hand"],
    "account": ["profile", "login", "credentials", "access", "membership"],
    "password": ["passcode", "pin", "secret", "credentials", "login"],
    "billing": ["invoice", "charge", "payment", "statement", "receipt", "due"],
    "refund": ["money back", "reimbursement", "credit", "compensation"],
    "cancel": ["stop", "end", "terminate", "discontinue", "abort", "call off"],
    "upgrade": ["update", "improve", "enhance", "boost", "level up"],
    "bug": ["error", "glitch", "fault", "defect", "crash", "issue", "problem"],
    "slow": ["laggy", "sluggish", "unresponsive", "crawling", "taking forever"],
    "angry": ["furious", "mad", "upset", "livid", "pissed", "annoyed", "frustrated"],
    "urgent": ["asap", "emergency", "critical", "right now", "immediately", "pronto"],
}

_FLAT_SYNONYM_MAP: dict[str, str] = {}
_FLAT_BRAND_MAP: dict[str, str] = {}
_FLAT_TYPO_MAP: dict[str, str] = {}
_MAX_NORMALIZE_LENGTH = 300


def _build_flat_maps() -> None:
    """Pre-compile all synonym maps into flat dicts at module load time."""
    synonym_sources = [
        PRODUCT_SYNONYMS,
        ACTION_SYNONYMS,
        PRICE_SYNONYMS,
        ECOMMERCE_SYNONYMS,
        GENERAL_SYNONYMS,
    ]
    for source in synonym_sources:
        for canonical, synonyms in source.items():
            for synonym in synonyms:
                key = synonym.lower().strip()
                if key and key not in _FLAT_SYNONYM_MAP:
                    _FLAT_SYNONYM_MAP[key] = canonical.lower().strip()

    for canonical, aliases in BRAND_SYNONYMS.items():
        for alias in aliases:
            key = alias.lower().strip()
            if key and key not in _FLAT_BRAND_MAP:
                _FLAT_BRAND_MAP[key] = canonical.lower().strip()

    for typo, correction in TYPO_MAP.items():
        key = typo.lower().strip()
        if key and key not in _FLAT_TYPO_MAP:
            _FLAT_TYPO_MAP[key] = correction.lower().strip()


_build_flat_maps()


_WORD_BOUNDARY_RE = re.compile(r"\b")


def normalize_message(message: str) -> str:
    text = message.lower().strip()

    if len(text) > _MAX_NORMALIZE_LENGTH:
        text = text[:_MAX_NORMALIZE_LENGTH]

    words = text.split()
    replaced = []
    for word in words:
        stripped = word.strip(".,!?;:'\"()")
        if stripped in _FLAT_TYPO_MAP:
            replaced.append(_FLAT_TYPO_MAP[stripped])
        elif stripped in _FLAT_SYNONYM_MAP:
            replaced.append(_FLAT_SYNONYM_MAP[stripped])
        elif stripped in _FLAT_BRAND_MAP:
            replaced.append(_FLAT_BRAND_MAP[stripped])
        else:
            replaced.append(word)

    return " ".join(replaced)


def normalize_brand(brand_str: str) -> str:
    """Normalize a brand name to its canonical form.

    Args:
        brand_str: Brand name (may be alias or colloquial)

    Returns:
        Canonical brand name, or the original if no mapping found
    """
    lower = brand_str.lower().strip()
    return BRAND_CANONICAL.get(lower, lower)


def get_product_category(synonym: str) -> str | None:
    """Look up the canonical product category for a synonym.

    Args:
        synonym: Product term (may be colloquial)

    Returns:
        Canonical category name, or None if not found
    """
    lower = synonym.lower().strip()
    for canonical, synonyms in PRODUCT_SYNONYMS.items():
        if lower == canonical or lower in [s.lower() for s in synonyms]:
            return canonical
    return None


def get_all_product_terms() -> set[str]:
    """Get all product category terms including synonyms.

    Returns:
        Set of all product category terms (canonical + synonyms)
    """
    terms = set()
    for canonical, synonyms in PRODUCT_SYNONYMS.items():
        terms.add(canonical)
        terms.update(s.lower() for s in synonyms)
    return terms
