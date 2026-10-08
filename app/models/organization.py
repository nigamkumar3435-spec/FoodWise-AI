from datetime import datetime
from app import db


class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    organization_name = db.Column(db.String(150), nullable=False)
    organization_type = db.Column(db.String(50), nullable=False)
    # Types: restaurant, canteen, hotel, hostel, catering, ngo, food_bank
    address = db.Column(db.String(300))
    city = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    contact_number = db.Column(db.String(20))
    # For NGOs: capacity in meals/kg
    capacity = db.Column(db.Float, default=0.0)
    # For NGOs: comma-separated food categories
    accepted_food_categories = db.Column(db.String(300), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    food_histories = db.relationship('FoodHistory', backref='organization', lazy=True)
    predictions = db.relationship('DemandPrediction', backref='organization', lazy=True)
    surplus_listings = db.relationship('SurplusListing', backref='provider', lazy=True,
                                       foreign_keys='SurplusListing.provider_id')
    impact_metric = db.relationship('ImpactMetric', backref='organization', uselist=False, lazy=True)

    def accepted_categories_list(self):
        if self.accepted_food_categories:
            return [c.strip() for c in self.accepted_food_categories.split(',') if c.strip()]
        return []

    def __repr__(self):
        return f'<Organization {self.organization_name}>'
