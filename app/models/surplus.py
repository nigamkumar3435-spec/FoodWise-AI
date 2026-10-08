from datetime import datetime
from app import db


class SurplusListing(db.Model):
    __tablename__ = 'surplus_listings'

    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False, index=True)
    food_name = db.Column(db.String(200), nullable=False)
    food_category = db.Column(db.String(100))
    # Categories: rice, dal, bread, vegetables, protein, dessert, beverages, mixed, other
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), default='meals')  # meals, kg, litres
    preparation_time = db.Column(db.DateTime)
    expiry_time = db.Column(db.DateTime)
    pickup_deadline = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='available', index=True)
    # available, requested, assigned, collected, expired
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    food_safety_confirmed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    donation_requests = db.relationship('DonationRequest', backref='surplus_listing', lazy=True)

    def is_available(self):
        return self.status == 'available'

    def to_dict(self):
        return {
            'id': self.id,
            'provider_id': self.provider_id,
            'food_name': self.food_name,
            'food_category': self.food_category,
            'quantity': self.quantity,
            'unit': self.unit,
            'status': self.status,
            'pickup_deadline': self.pickup_deadline.isoformat() if self.pickup_deadline else None,
            'expiry_time': self.expiry_time.isoformat() if self.expiry_time else None,
            'latitude': self.latitude,
            'longitude': self.longitude,
        }

    def __repr__(self):
        return f'<SurplusListing {self.food_name} qty={self.quantity}>'


class DonationRequest(db.Model):
    __tablename__ = 'donation_requests'

    id = db.Column(db.Integer, primary_key=True)
    surplus_listing_id = db.Column(db.Integer, db.ForeignKey('surplus_listings.id'), nullable=False, index=True)
    ngo_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False, index=True)
    request_status = db.Column(db.String(20), default='pending', index=True)
    # pending, approved, rejected, completed
    request_time = db.Column(db.DateTime, default=datetime.utcnow)
    approved_time = db.Column(db.DateTime)
    collected_time = db.Column(db.DateTime)

    ngo = db.relationship('Organization', foreign_keys=[ngo_id], backref='donation_requests_made')

    STATUS_LABELS = {
        'pending': 'Pending Review',
        'approved': 'Approved — Pickup Scheduled',
        'rejected': 'Rejected',
        'completed': 'Completed',
    }

    def status_label(self):
        return self.STATUS_LABELS.get(self.request_status, self.request_status)

    def to_dict(self):
        return {
            'id': self.id,
            'surplus_listing_id': self.surplus_listing_id,
            'ngo_id': self.ngo_id,
            'request_status': self.request_status,
            'request_time': self.request_time.isoformat(),
            'approved_time': self.approved_time.isoformat() if self.approved_time else None,
            'collected_time': self.collected_time.isoformat() if self.collected_time else None,
        }

    def __repr__(self):
        return f'<DonationRequest listing={self.surplus_listing_id} ngo={self.ngo_id} status={self.request_status}>'
