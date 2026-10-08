# Package init — import all models so SQLAlchemy discovers them
from app.models.user import User
from app.models.organization import Organization
from app.models.food_history import FoodHistory, DemandPrediction, ImpactMetric
from app.models.surplus import SurplusListing, DonationRequest

__all__ = [
    'User', 'Organization',
    'FoodHistory', 'DemandPrediction', 'ImpactMetric',
    'SurplusListing', 'DonationRequest',
]
