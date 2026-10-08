"""
PredictionService — loads the trained ML model and generates food demand predictions.
Falls back to a statistical baseline if no model is trained yet.
"""
import os
import math
import joblib
import numpy as np
from datetime import date, timedelta
from flask import current_app

from app import db
from app.models.food_history import FoodHistory

# Encoding maps must match train_model.py
MEAL_TYPE_MAP = {'breakfast': 0, 'lunch': 1, 'dinner': 2}
EVENT_TYPE_MAP = {
    'normal': 0, 'holiday': 1, 'festival': 2,
    'college_event': 3, 'weekend': 4, 'conference': 5,
}
WEATHER_MAP = {'clear': 0, 'cloudy': 1, 'rainy': 2, 'hot': 3, 'cold': 4}


class PredictionService:
    def __init__(self, organization_id: int):
        self.org_id = organization_id
        self._model = None
        self._model_version = 'v1'
        self._load_model()

    def _load_model(self):
        try:
            model_dir = current_app.config.get('ML_MODEL_DIR', 'ml/models')
            model_path = os.path.join(model_dir, 'best_model.pkl')
            if os.path.exists(model_path):
                self._model = joblib.load(model_path)
        except Exception:
            self._model = None

    def _get_historical_stats(self, meal_type: str, day_of_week: int):
        """Compute rolling statistics from stored history for the org."""
        records = FoodHistory.query.filter_by(
            organization_id=self.org_id,
            meal_type=meal_type,
        ).order_by(FoodHistory.date.desc()).limit(30).all()

        if not records:
            return None

        consumptions = [r.food_consumed for r in records if r.food_consumed is not None]
        same_dow = [r.food_consumed for r in records
                    if r.day_of_week == day_of_week and r.food_consumed is not None]

        avg_all = float(np.mean(consumptions)) if consumptions else None
        avg_same_dow = float(np.mean(same_dow)) if same_dow else avg_all
        last_3 = float(np.mean(consumptions[:3])) if len(consumptions) >= 3 else avg_all
        last_7 = float(np.mean(consumptions[:7])) if len(consumptions) >= 7 else avg_all
        prev_day = consumptions[0] if consumptions else None

        return {
            'avg_all': avg_all,
            'avg_same_dow': avg_same_dow,
            'last_3_avg': last_3,
            'last_7_avg': last_7,
            'prev_day': prev_day,
            'count': len(consumptions),
        }

    def _build_feature_vector(self, pred_date: date, meal_type: str,
                               number_of_people: int, holiday: bool,
                               event_type: str, weather_condition: str,
                               temperature: float, stats: dict) -> np.ndarray:
        """Build a feature vector matching the training schema."""
        day_of_week = pred_date.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0

        prev_day_consumption = stats['prev_day'] if stats else number_of_people * 0.9
        last_3_avg = stats['last_3_avg'] if stats else number_of_people * 0.9
        last_7_avg = stats['last_7_avg'] if stats else number_of_people * 0.9
        same_day_lw = stats['avg_same_dow'] if stats else number_of_people * 0.9

        # Consumption trend: ratio of last 3 days vs last 7 days
        trend = (last_3_avg / last_7_avg) if last_7_avg else 1.0

        features = [
            day_of_week,
            MEAL_TYPE_MAP.get(meal_type, 1),
            number_of_people,
            int(holiday),
            EVENT_TYPE_MAP.get(event_type, 0),
            WEATHER_MAP.get(weather_condition, 0),
            temperature,
            is_weekend,
            prev_day_consumption,
            last_3_avg,
            last_7_avg,
            same_day_lw,
            trend,
        ]
        return np.array(features).reshape(1, -1)

    def _compute_confidence(self, stats: dict, number_of_people: int) -> float:
        """
        Prediction Reliability Score (0–1).
        Based on:
          - data availability (more data → higher confidence)
          - variability of recent consumption
        NOT a statistical probability — clearly a platform score.
        """
        if not stats or not stats.get('count'):
            return 0.55  # minimal data

        count = min(stats['count'], 60)
        data_score = count / 60.0  # 0–1

        if stats['last_7_avg'] and stats['avg_all']:
            variability = abs(stats['last_7_avg'] - stats['avg_all']) / (stats['avg_all'] + 1)
            consistency_score = max(0.0, 1.0 - variability)
        else:
            consistency_score = 0.6

        score = 0.5 * data_score + 0.5 * consistency_score
        return round(min(max(score, 0.50), 0.97), 3)

    def predict(self, pred_date: date, meal_type: str, number_of_people: int,
                holiday: bool, event_type: str, weather_condition: str,
                temperature: float, safety_buffer: float = 0.05) -> dict:

        day_of_week = pred_date.weekday()
        stats = self._get_historical_stats(meal_type, day_of_week)
        confidence = self._compute_confidence(stats, number_of_people)

        if self._model is not None:
            fv = self._build_feature_vector(
                pred_date, meal_type, number_of_people, holiday,
                event_type, weather_condition, temperature, stats
            )
            try:
                predicted = float(self._model.predict(fv)[0])
                predicted = max(predicted, 0.0)
            except Exception:
                predicted = self._fallback_prediction(stats, number_of_people, event_type)
        else:
            # Statistical fallback when model not yet trained
            predicted = self._fallback_prediction(stats, number_of_people, event_type)

        recommended = math.ceil(predicted * (1 + safety_buffer))

        return {
            'predicted_demand': round(predicted, 1),
            'recommended_preparation': float(recommended),
            'confidence_score': confidence,
            'model_version': self._model_version if self._model else 'statistical_fallback',
            'safety_buffer_pct': round(safety_buffer * 100, 1),
            'meal_type': meal_type,
            'prediction_date': pred_date.isoformat(),
        }

    def _fallback_prediction(self, stats, number_of_people, event_type):
        """Rule-based fallback when ML model is not available."""
        if stats and stats.get('last_7_avg'):
            base = stats['last_7_avg']
        else:
            # Conservative estimate based on people count
            meal_ratios = {'breakfast': 0.80, 'lunch': 0.90, 'dinner': 0.85}
            base = number_of_people * 0.88

        event_multipliers = {
            'normal': 1.0, 'holiday': 0.75, 'festival': 1.20,
            'college_event': 1.15, 'weekend': 0.85, 'conference': 1.10,
        }
        return base * event_multipliers.get(event_type, 1.0)
