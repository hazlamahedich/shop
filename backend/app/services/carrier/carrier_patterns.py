"""Carrier tracking number patterns and URL templates (Story 6.2).

This module contains patterns for 290+ international carriers organized by region.
Patterns are used to detect carriers from tracking numbers when carrier name is unavailable.

Reference: https://github.com/jkeen/tracking_number_data
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class CarrierRegion(str, Enum):
    """Geographic regions for carrier categorization."""

    UNITED_STATES = "us"
    UNITED_KINGDOM = "uk"
    PHILIPPINES = "ph"
    SOUTHEAST_ASIA = "sea"
    EUROPE = "eu"
    MIDDLE_EAST = "me"
    AFRICA = "af"
    LATIN_AMERICA = "latam"
    OCEANIA = "oce"
    SOUTH_ASIA = "sa"
    EAST_ASIA = "ea"
    CHINA = "cn"
    GLOBAL = "global"


@dataclass
class CarrierPattern:
    """Carrier tracking pattern with URL template.

    Attributes:
        name: Human-readable carrier name
        pattern: Regex pattern to match tracking numbers
        url_template: URL template with {tracking_number} placeholder
        region: Geographic region
        priority: Matching priority (higher = check first)
    """

    name: str
    pattern: str
    url_template: str
    region: CarrierRegion
    priority: int = 50


CARRIER_PATTERNS: list[CarrierPattern] = [
    # ============================================================================
    # UNITED STATES (27 carriers)
    # ============================================================================
    CarrierPattern(
        name="UPS",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=100,
    ),
    CarrierPattern(
        name="FedEx",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=90,
    ),
    CarrierPattern(
        name="FedEx SmartPost",
        pattern=r"^(92\d{18}|94\d{18})$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=95,
    ),
    CarrierPattern(
        name="USPS",
        pattern=r"^(94\d{20}|93\d{20}|92\d{20}|94\d{18}|93\d{18}|92\d{18}|[A-Z]{2}\d{9}[A-Z]{2}|\d{22})$",
        url_template="https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=80,
    ),
    CarrierPattern(
        name="DHL Express (US)",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/us-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=85,
    ),
    CarrierPattern(
        name="OnTrac",
        pattern=r"^D\d{8}$",
        url_template="https://www.ontrac.com/tracking/detail/{tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=70,
    ),
    CarrierPattern(
        name="LaserShip",
        pattern=r"^1LS\d+$",
        url_template="https://www.lasership.com/track/{tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=70,
    ),
    CarrierPattern(
        name="Amazon Logistics",
        pattern=r"^TBA\d+$",
        url_template="https://track.amazon.com/tracking/{tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=75,
    ),
    CarrierPattern(
        name="Amazon Logistics (TBC)",
        pattern=r"^TBC\d+$",
        url_template="https://track.amazon.com/tracking/{tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=75,
    ),
    CarrierPattern(
        name="UPS Mail Innovations",
        pattern=r"^(927489\d{16}|927489\d{12})$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=72,
    ),
    CarrierPattern(
        name="UPS SurePost",
        pattern=r"^(927489\d{16}|927489\d{12})$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=72,
    ),
    CarrierPattern(
        name="FedEx Ground",
        pattern=r"^\d{14}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=88,
    ),
    CarrierPattern(
        name="FedEx Express",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=88,
    ),
    CarrierPattern(
        name="DHL eCommerce",
        pattern=r"^(GM\d{16}|95\d{18})$",
        url_template="https://www.dhl.com/us-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=82,
    ),
    CarrierPattern(
        name="USPS Priority Mail",
        pattern=r"^94\d{20}$",
        url_template="https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=78,
    ),
    CarrierPattern(
        name="USPS First Class",
        pattern=r"^94\d{20}$",
        url_template="https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=78,
    ),
    CarrierPattern(
        name="USPS Express Mail",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=78,
    ),
    CarrierPattern(
        name="USPS Certified Mail",
        pattern=r"^(70\d{15}|71\d{15})$",
        url_template="https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=78,
    ),
    CarrierPattern(
        name="USPS Registered Mail",
        pattern=r"^(RA\d{9}[A-Z]{2}|RB\d{9}[A-Z]{2})$",
        url_template="https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=78,
    ),
    CarrierPattern(
        name="USPS Priority Mail Express International",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=78,
    ),
    CarrierPattern(
        name="USPS Priority Mail International",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=78,
    ),
    CarrierPattern(
        name="USPS Global Express Guaranteed",
        pattern=r"^\d{10}$",
        url_template="https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=78,
    ),
    CarrierPattern(
        name="USPS First Class Package International",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=78,
    ),
    CarrierPattern(
        name="Purolator",
        pattern=r"^\d{12}$",
        url_template="https://www.purolator.com/en/shipping/tracker?pins={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=60,
    ),
    CarrierPattern(
        name="Canada Post",
        pattern=r"^\d{16}$",
        url_template="https://www.canadapost-postescanada.ca/track-reperage/en#/resultList?searchValue={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=60,
    ),
    CarrierPattern(
        name="Canada Post Xpresspost",
        pattern=r"^\d{16}$",
        url_template="https://www.canadapost-postescanada.ca/track-reperage/en#/resultList?searchValue={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=60,
    ),
    CarrierPattern(
        name="Canada Post Expedited Parcel",
        pattern=r"^\d{16}$",
        url_template="https://www.canadapost-postescanada.ca/track-reperage/en#/resultList?searchValue={tracking_number}",
        region=CarrierRegion.UNITED_STATES,
        priority=60,
    ),
    # ============================================================================
    # UNITED KINGDOM (24 carriers)
    # ============================================================================
    CarrierPattern(
        name="Royal Mail",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.royalmail.com/track-your-item#/tracking-results/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=100,
    ),
    CarrierPattern(
        name="Royal Mail Special Delivery",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.royalmail.com/track-your-item#/tracking-results/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=100,
    ),
    CarrierPattern(
        name="Royal Mail Signed For",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.royalmail.com/track-your-item#/tracking-results/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=100,
    ),
    CarrierPattern(
        name="Royal Mail Tracked 24",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.royalmail.com/track-your-item#/tracking-results/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=100,
    ),
    CarrierPattern(
        name="Royal Mail Tracked 48",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.royalmail.com/track-your-item#/tracking-results/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=100,
    ),
    CarrierPattern(
        name="DPD UK",
        pattern=r"^\d{14}$",
        url_template="https://www.dpd.co.uk/tracking/tracking.do?parcelNumber={tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=95,
    ),
    CarrierPattern(
        name="DPD Local",
        pattern=r"^\d{14}$",
        url_template="https://www.dpdlocal.co.uk/tracking/tracking.do?parcelNumber={tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=95,
    ),
    CarrierPattern(
        name="Evri",
        pattern=r"^H\d{9}$",
        url_template="https://www.evri.com/track/parcel/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=90,
    ),
    CarrierPattern(
        name="Hermes",
        pattern=r"^H\d{9}$",
        url_template="https://www.evri.com/track/parcel/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=90,
    ),
    CarrierPattern(
        name="Yodel",
        pattern=r"^JD\d{16}$",
        url_template="https://www.yodel.co.uk/tracking/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=88,
    ),
    CarrierPattern(
        name="Parcelforce",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.parcelforce.com/track-trace?trackNumber={tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=85,
    ),
    CarrierPattern(
        name="DHL Express UK",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/gb-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=82,
    ),
    CarrierPattern(
        name="TNT UK",
        pattern=r"^\d{9}$",
        url_template="https://www.tnt.com/express/en_gb/site/tracking.html?search={tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=80,
    ),
    CarrierPattern(
        name="FedEx UK",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=78,
    ),
    CarrierPattern(
        name="UPS UK",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=78,
    ),
    CarrierPattern(
        name="Amazon Logistics UK",
        pattern=r"^TBA\d+$",
        url_template="https://track.amazon.com/tracking/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=75,
    ),
    CarrierPattern(
        name="DX Express",
        pattern=r"^\d{12}$",
        url_template="https://www.thedx.co.uk/delivery-tracking?consignmentNumber={tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=70,
    ),
    CarrierPattern(
        name="DX Secure",
        pattern=r"^\d{12}$",
        url_template="https://www.thedx.co.uk/delivery-tracking?consignmentNumber={tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=70,
    ),
    CarrierPattern(
        name="APC Overnight",
        pattern=r"^\d{10}$",
        url_template="https://www.apc-overnight.com/tracking/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=65,
    ),
    CarrierPattern(
        name="CitySprint",
        pattern=r"^\d{12}$",
        url_template="https://www.citysprint.co.uk/track/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=65,
    ),
    CarrierPattern(
        name="UK Mail",
        pattern=r"^\d{14}$",
        url_template="https://www.ukmail.com/track/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=65,
    ),
    CarrierPattern(
        name="Tuffnells",
        pattern=r"^\d{10}$",
        url_template="https://www.tuffnells.co.uk/track/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=65,
    ),
    CarrierPattern(
        name="Palletline",
        pattern=r"^\d{10}$",
        url_template="https://www.palletline.co.uk/track/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=60,
    ),
    CarrierPattern(
        name="Palletforce",
        pattern=r"^\d{10}$",
        url_template="https://www.palletforce.com/track/{tracking_number}",
        region=CarrierRegion.UNITED_KINGDOM,
        priority=60,
    ),
    # ============================================================================
    # PHILIPPINES (15 carriers)
    # ============================================================================
    CarrierPattern(
        name="LBC Express",
        pattern=r"^\d{12,15}$",
        url_template="https://www.lbcexpress.com/track/{tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=100,
    ),
    CarrierPattern(
        name="J&T Express Philippines",
        pattern=r"^JT\d{13}$",
        url_template="https://www.jtexpress.ph/tracking?billcode={tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=95,
    ),
    CarrierPattern(
        name="Ninja Van Philippines",
        pattern=r"^NV\d{10}$",
        url_template="https://www.ninjavans.ph/en-ph/tracking?id={tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=90,
    ),
    CarrierPattern(
        name="2GO Express",
        pattern=r"^\d{12}$",
        url_template="https://track.2go.com.ph/?trackno={tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=88,
    ),
    CarrierPattern(
        name="XDE Express",
        pattern=r"^XDE\d+$",
        url_template="https://www.xde.com.ph/track/{tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=85,
    ),
    CarrierPattern(
        name="Flash Express Philippines",
        pattern=r"^TH\d{13}$",
        url_template="https://www.flashexpress.com.ph/tracking?se={tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=82,
    ),
    CarrierPattern(
        name="JRS Express",
        pattern=r"^\d{10}$",
        url_template="https://www.jrs-express.com/track/{tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=80,
    ),
    CarrierPattern(
        name="Air21",
        pattern=r"^\d{12}$",
        url_template="https://www.air21.com.ph/track/{tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=75,
    ),
    CarrierPattern(
        name="Entrego",
        pattern=r"^\d{12}$",
        url_template="https://www.entrego.com.ph/track/{tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=75,
    ),
    CarrierPattern(
        name="Black Arrow Express",
        pattern=r"^BAE\d+$",
        url_template="https://www.blackarrowexpress.com/track/{tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=72,
    ),
    CarrierPattern(
        name="Move It Express",
        pattern=r"^MIE\d+$",
        url_template="https://www.moveitexpress.com/track/{tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=70,
    ),
    CarrierPattern(
        name="Lalamove Delivery",
        pattern=r"^\d{10}$",
        url_template="https://www.lalamove.com/track/{tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=68,
    ),
    CarrierPattern(
        name="GrabExpress",
        pattern=r"^GE\d+$",
        url_template="https://www.grab.com/ph/express/track/{tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=68,
    ),
    CarrierPattern(
        name="Ninjavan PH",
        pattern=r"^NV\d{10}$",
        url_template="https://www.ninjavans.ph/en-ph/tracking?id={tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=85,
    ),
    CarrierPattern(
        name="Philippine Postal Corporation",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.phlpost.gov.ph/track/{tracking_number}",
        region=CarrierRegion.PHILIPPINES,
        priority=60,
    ),
    # ============================================================================
    # SOUTHEAST ASIA (15 carriers)
    # ============================================================================
    CarrierPattern(
        name="Kerry Express Thailand",
        pattern=r"^KE\d+$",
        url_template="https://www.kerryexpress.com/th/en/track?track={tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=95,
    ),
    CarrierPattern(
        name="Thailand Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.thaiposttrack.com/track/{tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=90,
    ),
    CarrierPattern(
        name="Flash Express Thailand",
        pattern=r"^TH\d{13}$",
        url_template="https://www.flashexpress.co.th/tracking?se={tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=88,
    ),
    CarrierPattern(
        name="J&T Express Indonesia",
        pattern=r"^JT\d{13}$",
        url_template="https://www.jet.co.id/tracking?billcode={tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="J&T Express Malaysia",
        pattern=r"^JT\d{13}$",
        url_template="https://www.jtexpress.my/tracking?billcode={tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="J&T Express Vietnam",
        pattern=r"^JT\d{13}$",
        url_template="https://jtexpress.vn/tracking?billcode={tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="Ninja Van Indonesia",
        pattern=r"^NV\d{10}$",
        url_template="https://www.ninjavan.co/id-id/tracking?id={tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=82,
    ),
    CarrierPattern(
        name="Ninja Van Malaysia",
        pattern=r"^NV\d{10}$",
        url_template="https://www.ninjavan.co/my-en/tracking?id={tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=82,
    ),
    CarrierPattern(
        name="Ninja Van Thailand",
        pattern=r"^NV\d{10}$",
        url_template="https://www.ninjavan.co/th-th/tracking?id={tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=82,
    ),
    CarrierPattern(
        name="Ninja Van Vietnam",
        pattern=r"^NV\d{10}$",
        url_template="https://www.ninjavan.co/vi-vn/tracking?id={tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=82,
    ),
    CarrierPattern(
        name="JNE Express Indonesia",
        pattern=r"^\d{12}$",
        url_template="https://www.jne.co.id/tracking?billcode={tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=80,
    ),
    CarrierPattern(
        name="SiCepat Indonesia",
        pattern=r"^SP\d+$",
        url_template="https://www.sicepat.com/tracking?billcode={tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=78,
    ),
    CarrierPattern(
        name="AnterAja Indonesia",
        pattern=r"^AA\d+$",
        url_template="https://www.anteraja.id/tracking?billcode={tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=75,
    ),
    CarrierPattern(
        name="ID Express Indonesia",
        pattern=r"^ID\d+$",
        url_template="https://www.idexpress.co.id/tracking?billcode={tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=75,
    ),
    CarrierPattern(
        name="Pos Indonesia",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.posindonesia.co.id/tracking?billcode={tracking_number}",
        region=CarrierRegion.SOUTHEAST_ASIA,
        priority=70,
    ),
    # ============================================================================
    # EUROPE (45 carriers)
    # ============================================================================
    CarrierPattern(
        name="DHL Express Germany",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=100,
    ),
    CarrierPattern(
        name="DHL Paket Germany",
        pattern=r"^\d{12,20}$",
        url_template="https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=98,
    ),
    CarrierPattern(
        name="Deutsche Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.deutschepost.de/de/sendungsverfolgung.html?piececode={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=95,
    ),
    CarrierPattern(
        name="GLS Germany",
        pattern=r"^\d{12}$",
        url_template="https://gls-group.eu/DE/de/paketverfolgung?match={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=90,
    ),
    CarrierPattern(
        name="Hermes Germany",
        pattern=r"^\d{14}$",
        url_template="https://www.myhermes.de/paketverfolgung?trackingNumber={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=88,
    ),
    CarrierPattern(
        name="DPD Germany",
        pattern=r"^\d{14}$",
        url_template="https://www.dpd.com/de/tracking?parcelNumber={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=85,
    ),
    CarrierPattern(
        name="UPS Germany",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=82,
    ),
    CarrierPattern(
        name="FedEx Germany",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=80,
    ),
    CarrierPattern(
        name="PostNL",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.postnl.nl/tracktrace/?B={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=95,
    ),
    CarrierPattern(
        name="DHL Express Netherlands",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/nl-nl/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=90,
    ),
    CarrierPattern(
        name="DPD Netherlands",
        pattern=r"^\d{14}$",
        url_template="https://www.dpd.com/nl/tracking?parcelNumber={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=85,
    ),
    CarrierPattern(
        name="GLS Netherlands",
        pattern=r"^\d{12}$",
        url_template="https://gls-group.eu/NL/nl/paketverfolgung?match={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=82,
    ),
    CarrierPattern(
        name="La Poste France",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.laposte.fr/outils/suivre-vos-envois?code={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=95,
    ),
    CarrierPattern(
        name="Chronopost France",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.chronopost.fr/tracking-no-coursier?listeNumerosLT={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=90,
    ),
    CarrierPattern(
        name="Colissimo France",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.colissimo.fr/tracking-0/track?parcelNumber={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=88,
    ),
    CarrierPattern(
        name="DHL Express France",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/fr-fr/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=85,
    ),
    CarrierPattern(
        name="DPD France",
        pattern=r"^\d{14}$",
        url_template="https://www.dpd.com/fr/tracking?parcelNumber={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=82,
    ),
    CarrierPattern(
        name="GLS France",
        pattern=r"^\d{12}$",
        url_template="https://gls-group.eu/FR/fr/suivi-colis?match={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=80,
    ),
    CarrierPattern(
        name="Poste Italiane",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.poste.it/cerca/index.html?tracking={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=90,
    ),
    CarrierPattern(
        name="SDA Express Courier Italy",
        pattern=r"^\d{12}$",
        url_template="https://www.sda.it/wps/portal/Servizi_online/tracking-sda?locale=it&tracingNumber={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=85,
    ),
    CarrierPattern(
        name="BRT Bartolini Italy",
        pattern=r"^\d{12}$",
        url_template="https://vas.brt.it/vas/sped_det_show.hsm?NumeroSpedizione={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=82,
    ),
    CarrierPattern(
        name="GLS Italy",
        pattern=r"^\d{12}$",
        url_template="https://gls-group.eu/IT/it/ricerca-pacco?match={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=80,
    ),
    CarrierPattern(
        name="Correos Spain",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.correos.es/es/es/herramientas/localizador/envios?numero={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=90,
    ),
    CarrierPattern(
        name="SEUR Spain",
        pattern=r"^\d{10}$",
        url_template="https://www.seur.com/livetracking/?trackingNumber={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=85,
    ),
    CarrierPattern(
        name="MRW Spain",
        pattern=r"^\d{10}$",
        url_template="https://www.mrw.es/envios/seguimiento?codigo={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=82,
    ),
    CarrierPattern(
        name="DHL Express Spain",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/es-es/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=80,
    ),
    CarrierPattern(
        name="CTT Portugal",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.ctt.pt/feapl_2/app/open/tools/track?objetos={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=90,
    ),
    CarrierPattern(
        name="DHL Express Portugal",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/pt-pt/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=85,
    ),
    CarrierPattern(
        name="PostNord Sweden",
        pattern=r"^\d{12}$",
        url_template="https://www.postnord.se/verktyg/spara-brev-paket?shipmentId={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=90,
    ),
    CarrierPattern(
        name="DHL Express Sweden",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/sv-se/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=85,
    ),
    CarrierPattern(
        name="Posti Finland",
        pattern=r"^\d{12}$",
        url_template="https://www.posti.fi/fi/seuranta?code={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=90,
    ),
    CarrierPattern(
        name="DHL Express Finland",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/fi-fi/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=85,
    ),
    CarrierPattern(
        name="Posten Norway",
        pattern=r"^\d{12}$",
        url_template="https://www.posten.no/sporing?q={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=90,
    ),
    CarrierPattern(
        name="DHL Express Norway",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/no-no/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=85,
    ),
    CarrierPattern(
        name="Bring Norway",
        pattern=r"^\d{12}$",
        url_template="https://tracking.bring.com/tracking.html?q={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=85,
    ),
    CarrierPattern(
        name="PostNord Denmark",
        pattern=r"^\d{12}$",
        url_template="https://www.postnord.dk/verktoej/sporing?shipmentId={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=90,
    ),
    CarrierPattern(
        name="DHL Express Denmark",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/da-dk/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=85,
    ),
    CarrierPattern(
        name="DAO Denmark",
        pattern=r"^\d{10}$",
        url_template="https://www.dao.as/tracking?package={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=80,
    ),
    CarrierPattern(
        name="GLS Denmark",
        pattern=r"^\d{12}$",
        url_template="https://gls-group.eu/DK/da/pakketransport?match={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=80,
    ),
    CarrierPattern(
        name="Österreichische Post Austria",
        pattern=r"^\d{12}$",
        url_template="https://www.post.at/sv/sendungsverfolgung?id={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=90,
    ),
    CarrierPattern(
        name="DHL Express Austria",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/at-de/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=85,
    ),
    CarrierPattern(
        name="Post.ch Switzerland",
        pattern=r"^\d{12}$",
        url_template="https://www.post.ch/de/verfolgen?code={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=90,
    ),
    CarrierPattern(
        name="DHL Express Switzerland",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/de-de/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=85,
    ),
    CarrierPattern(
        name="Swiss Post",
        pattern=r"^\d{12}$",
        url_template="https://www.post.ch/de/verfolgen?code={tracking_number}",
        region=CarrierRegion.EUROPE,
        priority=88,
    ),
    # ============================================================================
    # MIDDLE EAST (15 carriers)
    # ============================================================================
    CarrierPattern(
        name="Aramex",
        pattern=r"^\d{10}$",
        url_template="https://www.aramex.com/us-en/track/results?ShipmentNumber={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=100,
    ),
    CarrierPattern(
        name="SMSA Express",
        pattern=r"^\d{12}$",
        url_template="https://www.smsaexpress.com/tracking?track={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=95,
    ),
    CarrierPattern(
        name="Emirates Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.emiratespost.ae/track?trackingNumber={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=90,
    ),
    CarrierPattern(
        name="DHL Express UAE",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/ae-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=85,
    ),
    CarrierPattern(
        name="FedEx UAE",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=82,
    ),
    CarrierPattern(
        name="UPS UAE",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=80,
    ),
    CarrierPattern(
        name="Saudi Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.sp.com.sa/tracking?track={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=90,
    ),
    CarrierPattern(
        name="Naqel Express",
        pattern=r"^\d{12}$",
        url_template="https://www.naqel.com.sa/tracking?track={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=85,
    ),
    CarrierPattern(
        name="Qatar Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.qpost.com.qa/track?trackingNumber={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=85,
    ),
    CarrierPattern(
        name="DHL Express Saudi Arabia",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/sa-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=80,
    ),
    CarrierPattern(
        name="Israel Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.israelpost.co.il/itemtrace.nsf/mainsearch?openform&code={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=85,
    ),
    CarrierPattern(
        name="Turkish Post (PTT)",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.ptt.gov.tr/tr/track?trackingNumber={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=85,
    ),
    CarrierPattern(
        name="Aras Kargo Turkey",
        pattern=r"^\d{10}$",
        url_template="https://www.araskargo.com.tr/tr/track?trackingNumber={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=80,
    ),
    CarrierPattern(
        name="Yurtici Kargo Turkey",
        pattern=r"^\d{10}$",
        url_template="https://www.yurticikargo.com/tr/track?trackingNumber={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=80,
    ),
    CarrierPattern(
        name="MNG Kargo Turkey",
        pattern=r"^\d{10}$",
        url_template="https://www.mngkargo.com.tr/tr/track?trackingNumber={tracking_number}",
        region=CarrierRegion.MIDDLE_EAST,
        priority=78,
    ),
    # ============================================================================
    # AFRICA (20 carriers)
    # ============================================================================
    CarrierPattern(
        name="DHL Express South Africa",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/za-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=90,
    ),
    CarrierPattern(
        name="FedEx South Africa",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=85,
    ),
    CarrierPattern(
        name="UPS South Africa",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=82,
    ),
    CarrierPattern(
        name="South African Post Office",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.postoffice.co.za/track?trackingNumber={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=80,
    ),
    CarrierPattern(
        name="RAM Hand-to-Hand Couriers South Africa",
        pattern=r"^\d{10}$",
        url_template="https://www.ram.co.za/track?trackingNumber={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=78,
    ),
    CarrierPattern(
        name="Dawn Wing South Africa",
        pattern=r"^\d{10}$",
        url_template="https://www.dawnwing.co.za/track?trackingNumber={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=75,
    ),
    CarrierPattern(
        name="Fastway South Africa",
        pattern=r"^\d{10}$",
        url_template="https://www.fastway.co.za/track?trackingNumber={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=72,
    ),
    CarrierPattern(
        name="Courier IT South Africa",
        pattern=r"^\d{10}$",
        url_template="https://www.courierit.co.za/track?trackingNumber={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=70,
    ),
    CarrierPattern(
        name="Nigeria Postal Service",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.nipost.gov.ng/track?trackingNumber={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=75,
    ),
    CarrierPattern(
        name="DHL Express Nigeria",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/ng-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=80,
    ),
    CarrierPattern(
        name="FedEx Nigeria",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=78,
    ),
    CarrierPattern(
        name="UPS Nigeria",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=75,
    ),
    CarrierPattern(
        name="Ghana Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.ghanapost.com.gh/track?trackingNumber={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=75,
    ),
    CarrierPattern(
        name="DHL Express Kenya",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/ke-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=80,
    ),
    CarrierPattern(
        name="G4S Kenya",
        pattern=r"^\d{10}$",
        url_template="https://www.g4s.co.ke/track?trackingNumber={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=75,
    ),
    CarrierPattern(
        name="Egypt Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.egyptpost.org/track?trackingNumber={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=75,
    ),
    CarrierPattern(
        name="DHL Express Egypt",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/eg-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=80,
    ),
    CarrierPattern(
        name="Morocco Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.poste.ma/track?trackingNumber={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=75,
    ),
    CarrierPattern(
        name="DHL Express Morocco",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/ma-fr/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=80,
    ),
    CarrierPattern(
        name="Tunisia Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.poste.tn/track?trackingNumber={tracking_number}",
        region=CarrierRegion.AFRICA,
        priority=75,
    ),
    # ============================================================================
    # LATIN AMERICA (35 carriers)
    # ============================================================================
    CarrierPattern(
        name="Correios Brazil",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.linkcorreios.com.br/?id={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=100,
    ),
    CarrierPattern(
        name="DHL Express Brazil",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/br-pt/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=90,
    ),
    CarrierPattern(
        name="FedEx Brazil",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=85,
    ),
    CarrierPattern(
        name="UPS Brazil",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=82,
    ),
    CarrierPattern(
        name="Jadlog Brazil",
        pattern=r"^\d{10}$",
        url_template="https://www.jadlog.com.br/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=80,
    ),
    CarrierPattern(
        name="Correios de Mexico",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.correosdemexico.gob.mx/Seguimiento?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=90,
    ),
    CarrierPattern(
        name="DHL Express Mexico",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/mx-es/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=88,
    ),
    CarrierPattern(
        name="FedEx Mexico",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=85,
    ),
    CarrierPattern(
        name="UPS Mexico",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=82,
    ),
    CarrierPattern(
        name="Estafeta Mexico",
        pattern=r"^\d{10}$",
        url_template="https://www.estafeta.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=80,
    ),
    CarrierPattern(
        name="Redpack Mexico",
        pattern=r"^\d{10}$",
        url_template="https://www.redpack.com.mx/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=78,
    ),
    CarrierPattern(
        name="Correo Argentino",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.correoargentino.com.ar/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=90,
    ),
    CarrierPattern(
        name="DHL Express Argentina",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/ar-es/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=88,
    ),
    CarrierPattern(
        name="OCA Argentina",
        pattern=r"^\d{12}$",
        url_template="https://www.oca.com.ar/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=85,
    ),
    CarrierPattern(
        name="Andreani Argentina",
        pattern=r"^\d{12}$",
        url_template="https://www.andreani.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=82,
    ),
    CarrierPattern(
        name="Correos Chile",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.correoschile.cl/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=90,
    ),
    CarrierPattern(
        name="DHL Express Chile",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/cl-es/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=88,
    ),
    CarrierPattern(
        name="Chilexpress",
        pattern=r"^\d{12}$",
        url_template="https://www.chilexpress.cl/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=85,
    ),
    CarrierPattern(
        name="Blue Express Chile",
        pattern=r"^\d{10}$",
        url_template="https://www.blueexpress.cl/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=80,
    ),
    CarrierPattern(
        name="Servientrega Colombia",
        pattern=r"^\d{10}$",
        url_template="https://www.servientrega.com.co/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=85,
    ),
    CarrierPattern(
        name="DHL Express Colombia",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/co-es/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=88,
    ),
    CarrierPattern(
        name="TCC Colombia",
        pattern=r"^\d{10}$",
        url_template="https://www.tcc.com.co/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=82,
    ),
    CarrierPattern(
        name="Interrapidisimo Colombia",
        pattern=r"^\d{10}$",
        url_template="https://www.interrapidisimo.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=80,
    ),
    CarrierPattern(
        name="Correos del Ecuador",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.correosdelecuador.gob.ec/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=85,
    ),
    CarrierPattern(
        name="DHL Express Ecuador",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/ec-es/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=88,
    ),
    CarrierPattern(
        name="Servientrega Ecuador",
        pattern=r"^\d{10}$",
        url_template="https://www.servientrega.com.ec/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=82,
    ),
    CarrierPattern(
        name="Correos de Peru",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.serpost.com.pe/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=85,
    ),
    CarrierPattern(
        name="DHL Express Peru",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/pe-es/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=88,
    ),
    CarrierPattern(
        name="Olva Courier Peru",
        pattern=r"^\d{10}$",
        url_template="https://www.olvacourier.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=82,
    ),
    CarrierPattern(
        name="Correos Uruguay",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.correo.com.uy/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=85,
    ),
    CarrierPattern(
        name="DHL Express Uruguay",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/uy-es/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=88,
    ),
    CarrierPattern(
        name="UES Uruguay",
        pattern=r"^\d{10}$",
        url_template="https://www.ues.com.uy/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=80,
    ),
    CarrierPattern(
        name="Correos de Costa Rica",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.correos.go.cr/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=85,
    ),
    CarrierPattern(
        name="DHL Express Costa Rica",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/cr-es/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=88,
    ),
    CarrierPattern(
        name="Correos de Guatemala",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.correos.gob.gt/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.LATIN_AMERICA,
        priority=85,
    ),
    # ============================================================================
    # OCEANIA (16 carriers)
    # ============================================================================
    CarrierPattern(
        name="Australia Post",
        pattern=r"^\d{12}$",
        url_template="https://auspost.com.au/mypost/track/#/search/{tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=100,
    ),
    CarrierPattern(
        name="DHL Express Australia",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/au-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=95,
    ),
    CarrierPattern(
        name="FedEx Australia",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=90,
    ),
    CarrierPattern(
        name="UPS Australia",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=88,
    ),
    CarrierPattern(
        name="TNT Australia",
        pattern=r"^\d{9}$",
        url_template="https://www.tnt.com/express/en_au/site/tracking.html?search={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=85,
    ),
    CarrierPattern(
        name="StarTrack Australia",
        pattern=r"^\d{12}$",
        url_template="https://startrack.com.au/track?trackingNumber={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=82,
    ),
    CarrierPattern(
        name="Aramex Australia",
        pattern=r"^\d{10}$",
        url_template="https://www.aramex.com.au/track?trackingNumber={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=80,
    ),
    CarrierPattern(
        name="Sendle Australia",
        pattern=r"^[A-Z0-9]{6}$",
        url_template="https://www.sendle.com/track?trackingNumber={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=78,
    ),
    CarrierPattern(
        name="New Zealand Post",
        pattern=r"^\d{12}$",
        url_template="https://www.nzpost.co.nz/tools/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=95,
    ),
    CarrierPattern(
        name="DHL Express New Zealand",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/nz-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=90,
    ),
    CarrierPattern(
        name="FedEx New Zealand",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=88,
    ),
    CarrierPattern(
        name="UPS New Zealand",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=85,
    ),
    CarrierPattern(
        name="CourierPost New Zealand",
        pattern=r"^\d{12}$",
        url_template="https://www.courierpost.co.nz/track?trackingNumber={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=85,
    ),
    CarrierPattern(
        name="Fastway New Zealand",
        pattern=r"^\d{10}$",
        url_template="https://www.fastway.co.nz/track?trackingNumber={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=80,
    ),
    CarrierPattern(
        name="Post Fiji",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.postfiji.com/track?trackingNumber={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=75,
    ),
    CarrierPattern(
        name="DHL Express Fiji",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/fj-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.OCEANIA,
        priority=80,
    ),
    # ============================================================================
    # SOUTH ASIA (24 carriers)
    # ============================================================================
    CarrierPattern(
        name="India Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.indiapost.gov.in/vas/Pages/IndiaPostHome.aspx?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=100,
    ),
    CarrierPattern(
        name="DHL Express India",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/in-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=95,
    ),
    CarrierPattern(
        name="FedEx India",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=90,
    ),
    CarrierPattern(
        name="UPS India",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=88,
    ),
    CarrierPattern(
        name="BlueDart India",
        pattern=r"^\d{10}$",
        url_template="https://www.bluedart.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="Delhivery India",
        pattern=r"^\d{12}$",
        url_template="https://www.delhivery.com/track?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="Ecom Express India",
        pattern=r"^\d{10}$",
        url_template="https://www.ecomexpress.in/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=82,
    ),
    CarrierPattern(
        name="Ekart Logistics India",
        pattern=r"^\d{12}$",
        url_template="https://www.ekartlogistics.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=80,
    ),
    CarrierPattern(
        name="DTDC India",
        pattern=r"^\d{10}$",
        url_template="https://www.dtdc.in/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=78,
    ),
    CarrierPattern(
        name="First Flight Couriers India",
        pattern=r"^\d{10}$",
        url_template="https://www.firstflight.net/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=75,
    ),
    CarrierPattern(
        name="Pakistan Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.pakpost.gov.pk/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="DHL Express Pakistan",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/pk-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=88,
    ),
    CarrierPattern(
        name="FedEx Pakistan",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="Leopard Couriers Pakistan",
        pattern=r"^\d{10}$",
        url_template="https://www.leopardscouriers.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=80,
    ),
    CarrierPattern(
        name="TCS Pakistan",
        pattern=r"^\d{10}$",
        url_template="https://www.tcs.com.pk/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=80,
    ),
    CarrierPattern(
        name="Sri Lanka Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.slpost.gov.lk/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="DHL Express Sri Lanka",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/lk-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=88,
    ),
    CarrierPattern(
        name="FedEx Sri Lanka",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="Bangladesh Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.bangladeshpost.gov.bd/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="DHL Express Bangladesh",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/bd-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=88,
    ),
    CarrierPattern(
        name="Sundarban Courier Bangladesh",
        pattern=r"^\d{10}$",
        url_template="https://www.sundarbancourier.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=80,
    ),
    CarrierPattern(
        name="RedX Bangladesh",
        pattern=r"^\d{10}$",
        url_template="https://www.redx.com.bd/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=78,
    ),
    CarrierPattern(
        name="Nepal Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.nepalpost.gov.np/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="DHL Express Nepal",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/np-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.SOUTH_ASIA,
        priority=88,
    ),
    # ============================================================================
    # EAST ASIA (22 carriers)
    # ============================================================================
    CarrierPattern(
        name="Japan Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.post.japanpost.jp/int/ems/tracking/index_en.html?trackingNumber={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=100,
    ),
    CarrierPattern(
        name="DHL Express Japan",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/jp-ja/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=95,
    ),
    CarrierPattern(
        name="FedEx Japan",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=90,
    ),
    CarrierPattern(
        name="UPS Japan",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=88,
    ),
    CarrierPattern(
        name="Sagawa Express Japan",
        pattern=r"^\d{10}$",
        url_template="https://www.sagawa-exp.co.jp/english/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="Yamato Transport Japan",
        pattern=r"^\d{12}$",
        url_template="https://www.kuronekoyamato.co.jp/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="Korea Post South Korea",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.epost.go.kr/trace.RetrieveRegNoPrintCondView.comm?displayHeader=N&trackingNumber={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=95,
    ),
    CarrierPattern(
        name="DHL Express South Korea",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/kr-ko/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=92,
    ),
    CarrierPattern(
        name="FedEx South Korea",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=90,
    ),
    CarrierPattern(
        name="UPS South Korea",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=88,
    ),
    CarrierPattern(
        name="CJ Logistics South Korea",
        pattern=r"^\d{12}$",
        url_template="https://www.cjlogistics.com/en/tool/track?trackingNumber={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="Logen Korea",
        pattern=r"^\d{10}$",
        url_template="https://www.ilogen.com/web/personal/track?trackingNumber={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=82,
    ),
    CarrierPattern(
        name="Taiwan Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.post.gov.tw/post/internet/Postal/index.jsp?trackingNumber={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=95,
    ),
    CarrierPattern(
        name="DHL Express Taiwan",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/tw-zh/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=92,
    ),
    CarrierPattern(
        name="FedEx Taiwan",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=90,
    ),
    CarrierPattern(
        name="UPS Taiwan",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=88,
    ),
    CarrierPattern(
        name="Chunghwa Post Taiwan",
        pattern=r"^\d{12}$",
        url_template="https://www.post.gov.tw/post/internet/Postal/index.jsp?trackingNumber={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=85,
    ),
    CarrierPattern(
        name="Hong Kong Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.hongkongpost.hk/en/tracking/index.html?trackingNumber={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=95,
    ),
    CarrierPattern(
        name="DHL Express Hong Kong",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/hk-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=92,
    ),
    CarrierPattern(
        name="FedEx Hong Kong",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=90,
    ),
    CarrierPattern(
        name="UPS Hong Kong",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=88,
    ),
    CarrierPattern(
        name="SF Express Hong Kong",
        pattern=r"^SF\d+$",
        url_template="https://www.sf-express.com/hk/en/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.EAST_ASIA,
        priority=85,
    ),
    # ============================================================================
    # CHINA (18 carriers)
    # ============================================================================
    CarrierPattern(
        name="China Post",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.chinapost.com.cn/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=100,
    ),
    CarrierPattern(
        name="EMS China",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.ems.com.cn/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=95,
    ),
    CarrierPattern(
        name="DHL Express China",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/cn-zh/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=92,
    ),
    CarrierPattern(
        name="FedEx China",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=90,
    ),
    CarrierPattern(
        name="UPS China",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=88,
    ),
    CarrierPattern(
        name="SF Express",
        pattern=r"^SF\d+$",
        url_template="https://www.sf-express.com/cn/en/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=85,
    ),
    CarrierPattern(
        name="ZTO Express",
        pattern=r"^\d{12}$",
        url_template="https://www.zto.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=82,
    ),
    CarrierPattern(
        name="YTO Express",
        pattern=r"^[A-Z]{2}\d{10}$",
        url_template="https://www.yto.net.cn/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=80,
    ),
    CarrierPattern(
        name="STO Express",
        pattern=r"^\d{12}$",
        url_template="https://www.sto.cn/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=80,
    ),
    CarrierPattern(
        name="Yunda Express",
        pattern=r"^\d{13}$",
        url_template="https://www.yundaex.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=78,
    ),
    CarrierPattern(
        name="Best Express",
        pattern=r"^\d{12}$",
        url_template="https://www.best-inc.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=75,
    ),
    CarrierPattern(
        name="JD Logistics",
        pattern=r"^JD\d+$",
        url_template="https://www.jdl.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=78,
    ),
    CarrierPattern(
        name="Cainiao",
        pattern=r"^[A-Z]{2}\d{14}$",
        url_template="https://www.cainiao.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=75,
    ),
    CarrierPattern(
        name="J&T Express China",
        pattern=r"^JT\d{13}$",
        url_template="https://www.jtexpress.cn/tracking?billcode={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=75,
    ),
    CarrierPattern(
        name="DPEX China",
        pattern=r"^\d{10}$",
        url_template="https://www.dpex.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=72,
    ),
    CarrierPattern(
        name="4PX Express",
        pattern=r"^\d{12}$",
        url_template="https://www.4px.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=70,
    ),
    CarrierPattern(
        name="Yanwen Express",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.yw56.com.cn/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=70,
    ),
    CarrierPattern(
        name="Flyt Express",
        pattern=r"^\d{12}$",
        url_template="https://www.flyt.cn/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.CHINA,
        priority=68,
    ),
    # ============================================================================
    # GLOBAL (15 carriers)
    # ============================================================================
    CarrierPattern(
        name="DHL Express Global",
        pattern=r"^\d{10}$",
        url_template="https://www.dhl.com/en/express/tracking.html?AWB={tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=100,
    ),
    CarrierPattern(
        name="FedEx Global",
        pattern=r"^\d{12}$",
        url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=95,
    ),
    CarrierPattern(
        name="UPS Global",
        pattern=r"^1Z[A-Z0-9]{16}$",
        url_template="https://www.ups.com/track?tracknum={tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=95,
    ),
    CarrierPattern(
        name="TNT Global",
        pattern=r"^\d{9}$",
        url_template="https://www.tnt.com/express/en_us/site/tracking.html?search={tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=90,
    ),
    CarrierPattern(
        name="DPD Global",
        pattern=r"^\d{14}$",
        url_template="https://www.dpd.com/tracking?parcelNumber={tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=85,
    ),
    CarrierPattern(
        name="GLS Global",
        pattern=r"^\d{12}$",
        url_template="https://gls-group.eu/EN/en/parcel-tracking?match={tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=85,
    ),
    CarrierPattern(
        name="Hermes Global",
        pattern=r"^\d{14}$",
        url_template="https://www.myhermes.com/tracking?trackingNumber={tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=80,
    ),
    CarrierPattern(
        name="PostNL Global",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.postnl.nl/en/track-and-trace/?B={tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=80,
    ),
    CarrierPattern(
        name="Aramex Global",
        pattern=r"^\d{10}$",
        url_template="https://www.aramex.com/track-results?ShipmentNumber={tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=78,
    ),
    CarrierPattern(
        name="ParcelForce Global",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.parcelforce.com/track-trace?trackNumber={tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=78,
    ),
    CarrierPattern(
        name="Purolator Global",
        pattern=r"^\d{12}$",
        url_template="https://www.purolator.com/en/shipping/tracker?pins={tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=75,
    ),
    CarrierPattern(
        name="Canada Post Global",
        pattern=r"^\d{16}$",
        url_template="https://www.canadapost-postescanada.ca/track-en/#resultList?searchValue={tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=75,
    ),
    CarrierPattern(
        name="Australia Post Global",
        pattern=r"^\d{12}$",
        url_template="https://auspost.com.au/mypost/track/#/search/{tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=75,
    ),
    CarrierPattern(
        name="Japan Post Global",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.post.japanpost.jp/int/ems/tracking/index_en.html?trackingNumber={tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=75,
    ),
    CarrierPattern(
        name="India Post Global",
        pattern=r"^[A-Z]{2}\d{9}[A-Z]{2}$",
        url_template="https://www.indiapost.gov.in/vas/Pages/IndiaPostHome.aspx?trackingNumber={tracking_number}",
        region=CarrierRegion.GLOBAL,
        priority=75,
    ),
]


_SORTED_PATTERNS_CACHE: list[CarrierPattern] | None = None


def get_sorted_patterns() -> list[CarrierPattern]:
    """Get carrier patterns sorted by priority (highest first).

    Uses module-level caching to avoid re-sorting on every call.

    Returns:
        List of CarrierPattern objects sorted by priority descending.
    """
    global _SORTED_PATTERNS_CACHE
    if _SORTED_PATTERNS_CACHE is None:
        _SORTED_PATTERNS_CACHE = sorted(CARRIER_PATTERNS, key=lambda p: p.priority, reverse=True)
    return _SORTED_PATTERNS_CACHE


def detect_carrier_by_pattern(tracking_number: str) -> CarrierPattern | None:
    """Detect carrier from tracking number using pattern matching.

    Args:
        tracking_number: The tracking number to detect carrier for.

    Returns:
        CarrierPattern if matched, None otherwise.
    """
    if not tracking_number:
        return None

    tracking_number_upper = tracking_number.upper()

    for pattern in get_sorted_patterns():
        try:
            if re.match(pattern.pattern, tracking_number_upper):
                return pattern
        except re.error:
            continue

    return None


def get_tracking_url(
    carrier_name: str | None,
    tracking_number: str,
) -> str | None:
    """Generate tracking URL from carrier name and tracking number.

    Args:
        carrier_name: Carrier name (e.g., "UPS", "FedEx").
        tracking_number: The tracking number.

    Returns:
        Tracking URL if carrier found, None otherwise.
    """
    if not tracking_number:
        return None

    if carrier_name:
        for pattern in CARRIER_PATTERNS:
            if carrier_name.lower() in pattern.name.lower():
                return pattern.url_template.format(tracking_number=tracking_number)

    detected = detect_carrier_by_pattern(tracking_number)
    if detected:
        return detected.url_template.format(tracking_number=tracking_number)

    return None
