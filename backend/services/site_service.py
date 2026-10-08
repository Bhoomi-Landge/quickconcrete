from models import Site, db


class SiteError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _clean_payload(data):
    return {
        "site_name": (data.get("site_name") or "").strip(),
        "address": (data.get("address") or "").strip(),
        "city": (data.get("city") or "").strip(),
        "pincode": (data.get("pincode") or "").strip(),
    }


def validate_site_fields(payload):
    site_name = payload["site_name"]
    address = payload["address"]
    city = payload["city"]
    pincode = payload["pincode"]

    if not site_name:
        raise SiteError("Site name is required.")
    if len(site_name) > 200:
        raise SiteError("Site name is too long.")
    if not address:
        raise SiteError("Address is required.")
    if not city:
        raise SiteError("City is required.")
    if not pincode or not pincode.isdigit() or len(pincode) != 6:
        raise SiteError("Pincode must be a 6-digit number.")

    return payload


def list_sites_for_contractor(contractor_id):
    return (
        Site.query.filter_by(contractor_id=contractor_id)
        .order_by(Site.created_at.desc())
        .all()
    )


def get_site_for_contractor(contractor_id, site_id):
    site = Site.query.filter_by(id=site_id, contractor_id=contractor_id).first()
    if not site:
        raise SiteError("Site not found.", 404)
    return site


def create_site(contractor_id, data):
    payload = validate_site_fields(_clean_payload(data))
    site = Site(contractor_id=contractor_id, **payload)
    db.session.add(site)
    db.session.commit()
    return site


def update_site(contractor_id, site_id, data):
    site = get_site_for_contractor(contractor_id, site_id)
    payload = validate_site_fields(_clean_payload(data))
    site.site_name = payload["site_name"]
    site.address = payload["address"]
    site.city = payload["city"]
    site.pincode = payload["pincode"]
    db.session.commit()
    return site


def delete_site(contractor_id, site_id):
    site = get_site_for_contractor(contractor_id, site_id)
    if site.orders:
        raise SiteError(
            "This site has orders and cannot be deleted.",
            409,
        )
    db.session.delete(site)
    db.session.commit()
