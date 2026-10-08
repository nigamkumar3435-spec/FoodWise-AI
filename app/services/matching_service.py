"""
MatchingService — scores NGOs against a surplus listing.

Match Score formula:
  Distance Score    × 0.30
  Capacity Score    × 0.25
  Food Compatibility × 0.25
  Pickup Feasibility × 0.20
"""
import math
from datetime import datetime

from app.models.organization import Organization
from app.models.user import User


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two coordinates."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _distance_score(distance_km: float) -> float:
    """Score decreases linearly; max 100 within 1 km, 0 beyond 30 km."""
    if distance_km <= 1.0:
        return 1.0
    if distance_km >= 30.0:
        return 0.0
    return 1.0 - (distance_km - 1.0) / 29.0


def _capacity_score(ngo_capacity: float, listing_quantity: float) -> float:
    if not ngo_capacity or not listing_quantity:
        return 0.5
    ratio = ngo_capacity / listing_quantity
    if ratio >= 1.0:
        return 1.0
    return ratio


def _compatibility_score(ngo_org: Organization, listing_category: str) -> float:
    categories = ngo_org.accepted_categories_list()
    if not categories:
        return 0.7  # NGO accepts anything
    if listing_category and listing_category.lower() in [c.lower() for c in categories]:
        return 1.0
    return 0.2


def _pickup_score(pickup_deadline) -> float:
    """More time remaining → higher score."""
    if pickup_deadline is None:
        return 0.5
    minutes_left = (pickup_deadline - datetime.utcnow()).total_seconds() / 60
    if minutes_left <= 0:
        return 0.0
    if minutes_left >= 240:   # 4+ hours
        return 1.0
    return minutes_left / 240.0


class MatchingService:
    WEIGHTS = {
        'distance': 0.30,
        'capacity': 0.25,
        'compatibility': 0.25,
        'pickup': 0.20,
    }

    @classmethod
    def find_matches(cls, listing, top_n: int = 10) -> list:
        """Return a ranked list of NGO match dicts for the given SurplusListing."""
        ngo_users = User.query.filter_by(role='ngo', is_active=True).all()
        results = []

        for user in ngo_users:
            org = user.organization
            if org is None:
                continue

            # Distance
            if (listing.latitude and listing.longitude
                    and org.latitude and org.longitude):
                dist_km = haversine(listing.latitude, listing.longitude,
                                    org.latitude, org.longitude)
            else:
                dist_km = None

            d_score = _distance_score(dist_km) if dist_km is not None else 0.5
            c_score = _capacity_score(org.capacity, listing.quantity)
            f_score = _compatibility_score(org, listing.food_category)
            p_score = _pickup_score(listing.pickup_deadline)

            match_score = (
                d_score * cls.WEIGHTS['distance']
                + c_score * cls.WEIGHTS['capacity']
                + f_score * cls.WEIGHTS['compatibility']
                + p_score * cls.WEIGHTS['pickup']
            )

            results.append({
                'ngo_id': org.id,
                'ngo_name': org.organization_name,
                'city': org.city,
                'capacity': org.capacity,
                'accepted_categories': org.accepted_categories_list(),
                'distance_km': round(dist_km, 1) if dist_km is not None else None,
                'match_score': round(match_score * 100, 1),
                'distance_score': round(d_score * 100, 1),
                'capacity_score': round(c_score * 100, 1),
                'compatibility_score': round(f_score * 100, 1),
                'pickup_score': round(p_score * 100, 1),
            })

        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:top_n]
