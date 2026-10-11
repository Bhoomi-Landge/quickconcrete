"""Estimated cost breakdown for contractor quotes — server-side money math only."""

from decimal import Decimal, ROUND_HALF_UP

from models import ConcreteProduct, Plant, Supplier
from services.order_service import OrderError, get_product_for_plant_and_grade, _parse_grade, _parse_quantity, _parse_plant_id


def money_inr(value):
    """Round to 2 decimal places (INR paise) using decimal arithmetic."""
    if value is None:
        return None
    quantized = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(quantized)


def _pump_required_from_payload(data):
    if "pump_required" not in data:
        return False
    raw = data.get("pump_required")
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        return raw.strip().lower() == "true"
    return bool(raw)


def _line(code, label, amount_inr, source, status="confirmed", note=None):
    return {
        "code": code,
        "label": label,
        "amount_inr": amount_inr,
        "source": source,
        "status": status,
        "note": note,
    }


def build_quotation(product, quantity_m3, pump_required=False):
    """
    Build an estimated-cost breakdown for one plant product.
    Does not invent supplier charges; unknown items are marked explicitly.
    """
    plant = product.plant
    grade = product.grade
    price_per_m3 = money_inr(product.price_per_m3)
    qty = float(quantity_m3)
    concrete_subtotal = money_inr(qty * price_per_m3)

    lines = [
        _line(
            "CONCRETE",
            f"{grade} concrete ({qty} m³ × ₹{price_per_m3:,.0f}/m³)",
            concrete_subtotal,
            "supplier",
        )
    ]
    unknown_codes = []
    known_subtotal = concrete_subtotal

    if pump_required:
        if plant.pump_charge_inr is not None:
            pump_amt = money_inr(plant.pump_charge_inr)
            lines.append(
                _line(
                    "PUMP",
                    "Pump service (flat, supplier rate)",
                    pump_amt,
                    "supplier",
                )
            )
            known_subtotal = money_inr(known_subtotal + pump_amt)
        else:
            lines.append(
                _line(
                    "PUMP",
                    "Pump service",
                    None,
                    "supplier",
                    status="unknown",
                    note="Supplier has not published a pump charge; not included in total.",
                )
            )
            unknown_codes.append("PUMP")

    if plant.transport_charge_per_m3 is not None:
        transport_amt = money_inr(qty * plant.transport_charge_per_m3)
        lines.append(
            _line(
                "TRANSPORT",
                f"Transportation ({qty} m³ × ₹{plant.transport_charge_per_m3:,.0f}/m³)",
                transport_amt,
                "supplier",
            )
        )
        known_subtotal = money_inr(known_subtotal + transport_amt)
    else:
        lines.append(
            _line(
                "TRANSPORT",
                "Transportation / delivery to site",
                None,
                "supplier",
                status="unknown",
                note="Supplier has not published transport rates; not included in total.",
            )
        )
        unknown_codes.append("TRANSPORT")

    if plant.other_charge_inr is not None and plant.other_charge_inr > 0:
        label = (plant.other_charge_label or "Other disclosed charge").strip()
        other_amt = money_inr(plant.other_charge_inr)
        lines.append(_line("OTHER", label, other_amt, "supplier"))
        known_subtotal = money_inr(known_subtotal + other_amt)

    gst_rate = plant.gst_rate_percent
    tax_block = {
        "gst_rate_percent": gst_rate,
        "taxable_amount_inr": known_subtotal,
        "gst_amount_inr": None,
        "source": "supplier" if gst_rate is not None else "application",
        "status": "unknown",
    }
    if gst_rate is not None:
        if gst_rate < 0 or gst_rate > 28:
            raise OrderError("Plant GST rate must be between 0 and 28 percent.", 400)
        gst_amount = money_inr(known_subtotal * float(gst_rate) / 100.0)
        tax_block["gst_amount_inr"] = gst_amount
        tax_block["status"] = "confirmed"
        tax_block["source"] = "application"
        tax_block["note"] = f"GST calculated at {gst_rate}% on confirmed subtotal (supplier rate)."
        estimated_total = money_inr(known_subtotal + gst_amount)
    else:
        tax_block["note"] = "Supplier has not published GST rate; tax not included in total."
        unknown_codes.append("GST")
        estimated_total = known_subtotal

    has_unknown = len(unknown_codes) > 0

    return {
        "concrete_grade": grade,
        "quantity_m3": qty,
        "price_per_m3": price_per_m3,
        "concrete_subtotal_inr": concrete_subtotal,
        "minimum_order_m3": product.minimum_order_m3,
        "lines": lines,
        "subtotal_known_inr": known_subtotal,
        "tax": tax_block,
        "estimated_total_inr": estimated_total,
        "has_unknown_charges": has_unknown,
        "unknown_charge_codes": unknown_codes,
        "estimated_lead_time_hours": plant.estimated_lead_time_hours,
        "quotation_valid_days": plant.quotation_valid_days,
        "is_binding_quote": False,
        "disclaimer": (
            "Estimated cost for planning only — not a guaranteed final invoice. "
            "Excluded or unknown charges may apply at delivery."
        ),
        "currency": "INR",
    }


def estimate_with_quotation(contractor_id, data):
    from services.site_service import get_site_for_contractor

    site_id = data.get("site_id")
    if not site_id:
        raise OrderError("Construction site is required.")
    get_site_for_contractor(contractor_id, site_id)

    plant_id = _parse_plant_id(data.get("plant_id"))
    grade = _parse_grade(data.get("concrete_grade") or data.get("grade"))
    quantity_m3 = _parse_quantity(data.get("quantity_m3"))
    pump_required = _pump_required_from_payload(data)

    product = get_product_for_plant_and_grade(plant_id, grade)
    plant = product.plant
    supplier = plant.supplier
    quotation = build_quotation(product, quantity_m3, pump_required=pump_required)

    return {
        "concrete_grade": grade,
        "quantity_m3": quantity_m3,
        "price_per_m3": quotation["price_per_m3"],
        "total_amount": quotation["concrete_subtotal_inr"],
        "supplier_id": supplier.id,
        "supplier_name": supplier.company_name,
        "plant_id": plant.id,
        "plant_name": plant.plant_name,
        "plant_address": plant.address,
        "plant_city": plant.city,
        "plant_pincode": plant.pincode,
        "quotation": quotation,
    }


def compare_plant_offers(contractor_id, data):
    """Compare published offers for a grade/qty across marketplace plants."""
    site_id = data.get("site_id")
    if site_id:
        from services.site_service import get_site_for_contractor

        get_site_for_contractor(contractor_id, site_id)

    grade = _parse_grade(data.get("concrete_grade") or data.get("grade"))
    quantity_m3 = _parse_quantity(data.get("quantity_m3"))
    pump_required = _pump_required_from_payload(data)

    products = (
        ConcreteProduct.query.join(Plant)
        .join(Supplier)
        .filter(
            ConcreteProduct.grade == grade,
            ConcreteProduct.is_available.is_(True),
            Plant.is_active.is_(True),
            Supplier.is_active.is_(True),
        )
        .all()
    )

    offers = []
    for product in products:
        if quantity_m3 < product.minimum_order_m3:
            continue
        if quantity_m3 > product.available_quantity:
            continue
        plant = product.plant
        if not plant or not plant.supplier or not plant.supplier.is_active:
            continue
        quotation = build_quotation(product, quantity_m3, pump_required=pump_required)
        offers.append(
            {
                "plant_id": plant.id,
                "plant_name": plant.plant_name,
                "plant_city": plant.city,
                "supplier_id": plant.supplier_id,
                "supplier_name": plant.supplier.company_name,
                "product_id": product.id,
                "quotation": quotation,
            }
        )

    def sort_key(item):
        q = item["quotation"]
        return (q["has_unknown_charges"], q["estimated_total_inr"])

    offers.sort(key=sort_key)

    return {
        "concrete_grade": grade,
        "quantity_m3": quantity_m3,
        "pump_required": pump_required,
        "offers": offers,
        "disclaimer": (
            "Compare estimated totals using the same grade and quantity. "
            "Offers with unknown pump, transport or tax charges may appear cheaper until finalized."
        ),
    }
