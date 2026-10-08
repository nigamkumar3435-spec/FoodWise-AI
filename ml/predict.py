"""
predict.py — standalone inference script (also used for quick testing).

Usage:
    python ml/predict.py
"""
import os
import sys
import json
import joblib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODEL_PATH = os.path.join('ml', 'models', 'best_model.pkl')
META_PATH = os.path.join('ml', 'models', 'model_meta.json')

MEAL_TYPE_MAP = {'breakfast': 0, 'lunch': 1, 'dinner': 2}
EVENT_TYPE_MAP = {
    'normal': 0, 'holiday': 1, 'festival': 2,
    'college_event': 3, 'weekend': 4, 'conference': 5,
}
WEATHER_MAP = {'clear': 0, 'cloudy': 1, 'rainy': 2, 'hot': 3, 'cold': 4}


def predict_demand(
    day_of_week: int,
    meal_type: str,
    number_of_people: int,
    holiday: bool,
    event_type: str,
    weather_condition: str,
    temperature: float,
    prev_day_consumption: float,
    last_3_avg: float,
    last_7_avg: float,
    same_day_last_week: float,
) -> dict:
    if not os.path.exists(MODEL_PATH):
        return {'error': 'Model not trained. Run ml/train_model.py first.'}

    model = joblib.load(MODEL_PATH)
    is_weekend = 1 if day_of_week >= 5 else 0
    consumption_trend = last_3_avg / (last_7_avg + 1e-6)

    features = np.array([[
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
        same_day_last_week,
        consumption_trend,
    ]])

    prediction = float(model.predict(features)[0])
    prediction = max(0.0, prediction)

    meta = {}
    if os.path.exists(META_PATH):
        with open(META_PATH) as f:
            meta = json.load(f)

    return {
        'predicted_demand': round(prediction, 1),
        'model': meta.get('best_model', 'unknown'),
        'model_mae': meta.get('mae', None),
        'model_r2': meta.get('r2', None),
    }


if __name__ == '__main__':
    # Example prediction
    result = predict_demand(
        day_of_week=1,         # Tuesday
        meal_type='lunch',
        number_of_people=320,
        holiday=False,
        event_type='normal',
        weather_condition='clear',
        temperature=28.0,
        prev_day_consumption=290.0,
        last_3_avg=285.0,
        last_7_avg=280.0,
        same_day_last_week=295.0,
    )
    print("Prediction result:", result)
