"""
Feature engineering for the FoodWise AI demand prediction model.
All transformations must avoid data leakage (no future information).
"""
import pandas as pd
import numpy as np

MEAL_TYPE_MAP = {'breakfast': 0, 'lunch': 1, 'dinner': 2}
EVENT_TYPE_MAP = {
    'normal': 0, 'holiday': 1, 'festival': 2,
    'college_event': 3, 'weekend': 4, 'conference': 5,
}
WEATHER_MAP = {'clear': 0, 'cloudy': 1, 'rainy': 2, 'hot': 3, 'cold': 4}


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input  : raw DataFrame with columns from sample_food_data.csv
    Output : feature DataFrame ready for model training/inference
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values(['date', 'meal_type'], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # --- Encode categoricals ---
    df['meal_type_enc'] = df['meal_type'].map(MEAL_TYPE_MAP).fillna(1).astype(int)
    df['event_type_enc'] = df['event_type'].map(EVENT_TYPE_MAP).fillna(0).astype(int)
    df['weather_enc'] = df['weather_condition'].map(WEATHER_MAP).fillna(0).astype(int)

    # --- Binary flags ---
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['is_holiday'] = df['holiday'].astype(int)

    # --- Lag / rolling features (computed within each meal_type group) ---
    # Sort by date within each meal_type so shifts are chronological.
    df.sort_values(['meal_type', 'date'], inplace=True)

    df['prev_day_consumption'] = (
        df.groupby('meal_type')['food_consumed']
        .shift(1)
    )
    df['same_day_last_week_consumption'] = (
        df.groupby(['meal_type', 'day_of_week'])['food_consumed']
        .shift(1)
    )
    df['last_3_day_avg'] = (
        df.groupby('meal_type')['food_consumed']
        .transform(lambda x: x.shift(1).rolling(3, min_periods=1).mean())
    )
    df['last_7_day_avg'] = (
        df.groupby('meal_type')['food_consumed']
        .transform(lambda x: x.shift(1).rolling(7, min_periods=1).mean())
    )

    # Consumption trend: ratio of last-3-avg to last-7-avg
    df['consumption_trend'] = df['last_3_day_avg'] / (df['last_7_day_avg'] + 1e-6)

    # Fill NaN lags with forward-fill then the column mean
    lag_cols = [
        'prev_day_consumption', 'same_day_last_week_consumption',
        'last_3_day_avg', 'last_7_day_avg', 'consumption_trend'
    ]
    for col in lag_cols:
        df[col] = df[col].fillna(df.groupby('meal_type')[col].transform('mean'))
        df[col] = df[col].fillna(df['food_consumed'].mean())

    df.sort_values(['date', 'meal_type'], inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


FEATURE_COLUMNS = [
    'day_of_week',
    'meal_type_enc',
    'number_of_people',
    'is_holiday',
    'event_type_enc',
    'weather_enc',
    'temperature',
    'is_weekend',
    'prev_day_consumption',
    'last_3_day_avg',
    'last_7_day_avg',
    'same_day_last_week_consumption',
    'consumption_trend',
]

TARGET_COLUMN = 'food_consumed'
