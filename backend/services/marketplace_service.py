"""Marketplace listing for contractors — all active supplier plants."""

from models import ConcreteProduct, Plant, Supplier
from services.plant_service import plant_to_dict, product_to_dict


def get_marketplace_plants():
    plants = (
        Plant.query.join(Supplier)
        .filter(Plant.is_active.is_(True), Supplier.is_active.is_(True))
        .order_by(Supplier.company_name.asc(), Plant.plant_name.asc())
        .all()
    )
    payload = []
    for plant in plants:
        products = (
            ConcreteProduct.query.filter_by(plant_id=plant.id, is_available=True)
            .order_by(ConcreteProduct.grade.asc())
            .all()
        )
        entry = plant_to_dict(plant, include_summary=True)
        entry["supplier_name"] = plant.supplier.company_name
        entry["products"] = [product_to_dict(p) for p in products]
        payload.append(entry)
    return payload
