from datetime import datetime
from app import db


class FoodHistory(db.Model):
    __tablename__ = 'food_history'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    day_of_week = db.Column(db.Integer)        # 0=Monday ... 6=Sunday
    meal_type = db.Column(db.String(20))       # breakfast, lunch, dinner
    number_of_people = db.Column(db.Integer)
    food_prepared = db.Column(db.Float)        # in meals/portions
    food_consumed = db.Column(db.Float)
    surplus_food = db.Column(db.Float, default=0.0)
    event_type = db.Column(db.String(50), default='normal')
    # normal, holiday, festival, college_event, weekend, conference
    holiday = db.Column(db.Boolean, default=False)
    weather_condition = db.Column(db.String(30), default='clear')
    # clear, rainy, cloudy, hot, cold
    temperature = db.Column(db.Float)          # Celsius
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def waste_percentage(self):
        if self.food_prepared and self.food_prepared > 0:
            return round((self.surplus_food / self.food_prepared) * 100, 1)
        return 0.0

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'day_of_week': self.day_of_week,
            'meal_type': self.meal_type,
            'number_of_people': self.number_of_people,
            'food_prepared': self.food_prepared,
            'food_consumed': self.food_consumed,
            'surplus_food': self.surplus_food,
            'event_type': self.event_type,
            'holiday': self.holiday,
            'weather_condition': self.weather_condition,
            'temperature': self.temperature,
            'waste_percentage': self.waste_percentage,
        }

    def __repr__(self):
        return f'<FoodHistory org={self.organization_id} date={self.date} meal={self.meal_type}>'


class DemandPrediction(db.Model):
    __tablename__ = 'demand_predictions'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False, index=True)
    prediction_date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(20))
    predicted_demand = db.Column(db.Float)
    recommended_preparation = db.Column(db.Float)
    confidence_score = db.Column(db.Float)     # 0.0 – 1.0
    model_version = db.Column(db.String(50), default='v1')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'prediction_date': self.prediction_date.isoformat(),
            'meal_type': self.meal_type,
            'predicted_demand': round(self.predicted_demand, 1),
            'recommended_preparation': round(self.recommended_preparation, 1),
            'confidence_score': round(self.confidence_score * 100, 1),
        }


class ImpactMetric(db.Model):
    __tablename__ = 'impact_metrics'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False, unique=True)
    total_food_saved_kg = db.Column(db.Float, default=0.0)
    meals_saved = db.Column(db.Integer, default=0)
    money_saved = db.Column(db.Float, default=0.0)
    successful_donations = db.Column(db.Integer, default=0)
    waste_reduction_percentage = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
