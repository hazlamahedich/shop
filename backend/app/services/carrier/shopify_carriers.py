"""Shopify carrier name to URL template mapping (Epic 6).

Maps Shopify's supported carrier names to URL templates for tracking.
Based on: https://shopify.dev/docs/api/admin-rest/latest/resources/fulfillment
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

SHOPIFY_CARRIER_URLS: dict[str, str] = {
    # Global Major Carriers
    "ups": "https://www.ups.com/track?tracknum={tracking_number}",
    "fedex": "https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
    "dhl express": "https://www.dhl.com/us-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
    "dhl": "https://www.dhl.com/us-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
    "usps": "https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
    "canada post": "https://www.canadapost-postescanada.ca/track-reperage/en#/resultList?searchFor={tracking_number}",
    "royal mail": "https://www.royalmail.com/track-your-item#/tracking-results/{tracking_number}",
    "australia post": "https://auspost.com.au/mypost/track/#/details/{tracking_number}",
    "tnt": "https://www.tnt.com/track/{tracking_number}",
    "aramex": "https://www.aramex.com/track/{tracking_number}",
    # US Regional
    "ontrac": "https://ontrac.com/tracking.asp?tracking_number={tracking_number}",
    "lasership": "https://lasership.com/track/{tracking_number}",
    # UK Regional
    "evri": "https://evri.com/track/{tracking_number}",
    "hermes": "https://hermesworld.com/track/{tracking_number}",
    "dpd": "https://dpd.com/tracking/{tracking_number}",
    "gls": "https://gls-group.eu/track/{tracking_number}",
    "yodel": "https://yodel.co.uk/track/{tracking_number}",
    "dpd uk": "https://dpd.co.uk/tracking/{tracking_number}",
    "dpd local": "https://dpdlocal.co.uk/tracking/{tracking_number}",
    "parcelforce": "https://parcelforce.com/track-trace/track?parcelNumber={tracking_number}",
    # PH/SEA Regional
    "ninja van": "https://www.ninjavan.co/en-ph/tracking?id={tracking_number}",
    "ninjavan": "https://www.ninjavan.co/en-ph/tracking?id={tracking_number}",
    "lbc express": "https://www.lbcexpress.com/track/{tracking_number}",
    "lbc": "https://www.lbcexpress.com/track/{tracking_number}",
    "j&t express": "https://www.jet.co/track/{tracking_number}",
    "j&t": "https://www.jet.co/track/{tracking_number}",
    "2go": "https://tracking.2go.com.ph/?trackingnumber={tracking_number}",
    "flash express": "https://www.flashexpress.com/fle/tracking?se={tracking_number}",
    # China
    "sf express": "https://www.sf-express.com/track/{tracking_number}",
    "china post": "https://www.chinapost.com.cn/track/{tracking_number}",
    "yunexpress": "https://www.yunexpress.com/track/{tracking_number}",
    # Europe
    "postnl": "https://postnl.nl/track/{tracking_number}",
    "bpost": "https://www.bpost.be/track/{tracking_number}",
    "colissimo": "https://www.colissimo.fr/track/{tracking_number}",
    "deutsche post": "https://www.deutschepost.de/track/{tracking_number}",
    "swiss post": "https://www.post.ch/track/{tracking_number}",
    "postnord": "https://postnord.com/track/{tracking_number}",
    # Japan
    "japan post": "https://www.post.japanpost.jp/int/ems/tracking/index_en.html?trackingNumber={tracking_number}",
    "sagawa": "https://www.sagawa-exp.co.jp/english/tracking/{tracking_number}",
    "yamato": "https://www.kuronekoyamato.co.jp/tracking/{tracking_number}",
    # Korea
    "korea post": "https://www.epost.go.kr/trace.RetrieveRegNoPrintCondView.comm?displayHeader=N&trackingNumber={tracking_number}",
    "cj logistics": "https://www.cjlogistics.com/en/tool/track/{tracking_number}",
    # India
    "india post": "https://www.indiapost.gov.in/vas/Pages/IndiaPostHome.aspx?trackingNumber={tracking_number}",
    "bluedart": "https://www.bluedart.com/tracking/{tracking_number}",
    "delhivery": "https://www.delhivery.com/track/{tracking_number}",
    # Brazil
    "correios": "https://www.linkcorreios.com.br/?id={tracking_number}",
    # Mexico
    "correos de méxico": "https://www.correosdemexico.gob.mx/Seguimiento?trackingNumber={tracking_number}",
    # Australia
    "sendle": "https://www.sendle.com/track/{tracking_number}",
    "startrack": "https://startrack.com.au/track?trackingNumber={tracking_number}",
}


def get_shopify_carrier_url(carrier_name: str, tracking_number: str) -> str | None:
    """Get the tracking URL for a Shopify carrier.

    Args:
        carrier_name: Carrier name from Shopify webhook.
        tracking_number: The tracking number.

    Returns:
        Tracking URL if carrier found, None otherwise.
    """
    if not carrier_name or not tracking_number:
        return None

    carrier_lower = carrier_name.lower().strip()

    # Direct match
    if carrier_lower in SHOPIFY_CARRIER_URLS:
        logger.debug(
            "Found direct match for Shopify carrier",
            carrier_name=carrier_name,
        )
        return SHOPIFY_CARRIER_URLS[carrier_lower].format(
            tracking_number=tracking_number,
        )

    # Partial match (e.g., "FedEx SmartPost" matches "fedex")
    for key, url_template in SHOPIFY_CARRIER_URLS.items():
        if key in carrier_lower or carrier_lower in key:
            logger.debug(
                "Found partial match for Shopify carrier",
                carrier_name=carrier_name,
                matched_key=key,
            )
            return url_template.format(tracking_number=tracking_number)

    # DHL variations
    if "dhl" in carrier_lower:
        if "express" in carrier_lower:
            return SHOPIFY_CARRIER_URLS["dhl express"].format(
                tracking_number=tracking_number,
            )
        return SHOPIFY_CARRIER_URLS["dhl"].format(
            tracking_number=tracking_number,
        )

    # UPS variations
    if "ups" in carrier_lower:
        return SHOPIFY_CARRIER_URLS["ups"].format(
            tracking_number=tracking_number,
        )

    # USPS variations
    if "usps" in carrier_lower:
        return SHOPIFY_CARRIER_URLS["usps"].format(
            tracking_number=tracking_number,
        )

    # FedEx variations
    if "fedex" in carrier_lower or "fed ex" in carrier_lower:
        return SHOPIFY_CARRIER_URLS["fedex"].format(
            tracking_number=tracking_number,
        )

    # LBC variations
    if "lbc" in carrier_lower:
        return SHOPIFY_CARRIER_URLS["lbc express"].format(
            tracking_number=tracking_number,
        )

    # J&T variations
    if "j&t" in carrier_lower or "jt" in carrier_lower:
        return SHOPIFY_CARRIER_URLS["j&t express"].format(
            tracking_number=tracking_number,
        )

    # Ninja Van variations
    if "ninja" in carrier_lower or "ninjavan" in carrier_lower:
        return SHOPIFY_CARRIER_URLS["ninja van"].format(
            tracking_number=tracking_number,
        )

    logger.debug(
        "No Shopify carrier URL found",
        carrier_name=carrier_name,
    )
    return None
