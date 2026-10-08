"""
Generate a realistic synthetic dataset for FoodWise AI.
Produces ~3600 rows across 3 meal types × ~400 days.

Usage:
    python ml/generate_data.py
"""
import os
import random
import numpy as np
import pandas as pd
from datetime import date, timedelta

random.seed(42)
np.random.seed(42)

MEAL_TYPES = ['breakfast', 'lunch', 'dinner']
EVENT_TYPES = ['normal', 'normal', 'normal', 'holiday', 'festival',
               'college_event', 'weekend', 'conference']
WEATHER_CONDITIONS = ['clear', 'clear', 'cloudy', 'rainy', 'hot', 'cold']

BASE_PEOPLE = {
    'breakfast': (150, 30),
    'lunch': (350, 60),
    'dinner': (280, 50),
}

# Multipliers by event type
EVENT_MULTIPLIER = {
    'normal': 1.00,
    'holiday': 0.65,
    'festival': 1.25,
    'college_event': 1.18,
    'weekend': 0.80,
    'conference': 1.12,
}

# Weather effect on consumption
WEATHER_EFFECT = {
    'clear': 1.00,
    'cloudy': 0.98,
    'rainy': 0.90,
    'hot': 0.85,
    'cold': 1.05,
}


def generate_dataset(start_date=date(2023, 1, 1), days=400):
    records = []
    current = start_date

    for _ in range(days):
        dow = current.weekday()        # 0=Mon … 6=Sun
        is_weekend = dow >= 5
        is_monday = dow == 0
        month = current.month

        # Seasonal temperature
        season_temp = 20 + 10 * np.sin((month - 3) * np.pi / 6)
        temperature = round(float(season_temp) + random.gauss(0, 3), 1)
        # Clamp
        temperature = max(5.0, min(45.0, temperature))

        # Weather driven by temperature with noise
        if temperature > 35:
            weather = random.choice(['hot', 'clear', 'clear'])
        elif temperature < 12:
            weather = random.choice(['cold', 'cloudy', 'cloudy'])
        else:
            weather = random.choice(WEATHER_CONDITIONS)

        # Holiday / event
        holiday = (current.month == 1 and current.day == 1) or \
                  (current.month == 8 and current.day == 15) or \
                  (current.month == 10 and current.day == 2)
        if is_weekend:
            event_type = 'weekend'
        elif holiday:
            event_type = 'holiday'
        elif current.day % 20 == 0:
            event_type = 'festival'
        elif current.day % 15 == 0:
            event_type = 'conference'
        elif current.day % 7 == 0:
            event_type = 'college_event'
        else:
            event_type = 'normal'

        for meal in MEAL_TYPES:
            base_mu, base_sigma = BASE_PEOPLE[meal]

            # Weekend has lower breakfast/dinner but higher lunch for cafeteria
            if is_weekend and meal in ('breakfast', 'dinner'):
                base_mu = int(base_mu * 0.65)

            num_people = max(20, int(random.gauss(base_mu, base_sigma)))
            food_consumed_ideal = num_people * random.uniform(0.82, 0.98)
            food_consumed_ideal *= EVENT_MULTIPLIER.get(event_type, 1.0)
            food_consumed_ideal *= WEATHER_EFFECT.get(weather, 1.0)

            # Over-preparation bias (organizations typically over-prepare 8–20%)
            over_prep_factor = random.uniform(1.08, 1.22)
            food_prepared = round(food_consumed_ideal * over_prep_factor)
            food_consumed = round(
                food_consumed_ideal * random.uniform(0.90, 1.00)
            )
            food_consumed = min(food_consumed, food_prepared)
            surplus = max(food_prepared - food_consumed, 0)

            records.append({
                'date': current.isoformat(),
                'day_of_week': dow,
                'meal_type': meal,
                'number_of_people': num_people,
                'food_prepared': food_prepared,
                'food_consumed': food_consumed,
                'surplus_food': surplus,
                'event_type': event_type,
                'holiday': int(holiday),
                'weather_condition': weather,
                'temperature': temperature,
            })

        current += timedelta(days=1)

    return pd.DataFrame(records)


if __name__ == '__main__':
    os.makedirs('data/raw', exist_ok=True)
    df = generate_dataset()
    out = os.path.join('data', 'raw', 'sample_food_data.csv')
    df.to_csv(out, index=False)
    print(f"Generated {len(df)} rows → {out}")
    print(df.head())
    print(f"\nWaste % mean: {round((df['surplus_food'] / df['food_prepared']).mean() * 100, 1)}%")
