"""
Train and compare ML models for FoodWise AI demand prediction.
Saves the best model to ml/models/best_model.pkl.

Usage:
    python ml/train_model.py
"""
import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Add project root to path when run standalone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.feature_engineering import engineer_features, FEATURE_COLUMNS, TARGET_COLUMN
from ml.evaluate import print_evaluation


DATA_PATH = os.path.join('data', 'raw', 'sample_food_data.csv')
MODEL_DIR = os.path.join('ml', 'models')
os.makedirs(MODEL_DIR, exist_ok=True)


def load_and_prepare(csv_path: str):
    df = pd.read_csv(csv_path)
    df = engineer_features(df)
    # Drop rows with any NaN in features or target
    df = df.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN])
    return df


def time_split(df: pd.DataFrame, train_ratio: float = 0.80):
    """Chronological split — no leakage of future data into training set."""
    df = df.sort_values('date').reset_index(drop=True)
    split_idx = int(len(df) * train_ratio)
    train = df.iloc[:split_idx]
    test = df.iloc[split_idx:]
    print(f"Train: {len(train)} rows | Test: {len(test)} rows")
    print(f"Train ends: {train['date'].max()} | Test starts: {test['date'].min()}")
    return train, test


def build_models():
    return {
        'LinearRegression': Pipeline([
            ('scaler', StandardScaler()),
            ('model', LinearRegression()),
        ]),
        'RandomForest': RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
        ),
        'GradientBoosting': GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        ),
    }


def train_and_evaluate(csv_path: str = DATA_PATH):
    print("=" * 60)
    print("FoodWise AI — Model Training")
    print("=" * 60)

    df = load_and_prepare(csv_path)
    train_df, test_df = time_split(df)

    X_train = train_df[FEATURE_COLUMNS].values
    y_train = train_df[TARGET_COLUMN].values
    X_test = test_df[FEATURE_COLUMNS].values
    y_test = test_df[TARGET_COLUMN].values

    models = build_models()
    results = {}

    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        preds = np.maximum(preds, 0)  # enforce non-negative

        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        r2 = r2_score(y_test, preds)

        results[name] = {'mae': mae, 'rmse': rmse, 'r2': r2, 'model': model}
        print_evaluation(name, mae, rmse, r2)

    # Select best by R² score
    best_name = max(results, key=lambda k: results[k]['r2'])
    best = results[best_name]
    print(f"\n{'=' * 60}")
    print(f">> Best Model: {best_name}")
    print(f"   MAE:  {best['mae']:.2f} meals")
    print(f"   RMSE: {best['rmse']:.2f} meals")
    print(f"   R²:   {best['r2']:.4f}")
    print(f"{'=' * 60}")

    # Save best model
    model_path = os.path.join(MODEL_DIR, 'best_model.pkl')
    joblib.dump(best['model'], model_path)
    print(f"Model saved -> {model_path}")

    # Save metadata
    meta = {
        'best_model': best_name,
        'mae': round(best['mae'], 2),
        'rmse': round(best['rmse'], 2),
        'r2': round(best['r2'], 4),
        'features': FEATURE_COLUMNS,
        'target': TARGET_COLUMN,
        'trained_at': datetime.now().isoformat(),
        'train_rows': len(train_df),
        'test_rows': len(test_df),
    }
    meta_path = os.path.join(MODEL_DIR, 'model_meta.json')
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"Metadata saved -> {meta_path}")

    # Feature importance (tree models)
    inner_model = best['model']
    if hasattr(inner_model, 'feature_importances_'):
        importances = inner_model.feature_importances_
    elif hasattr(inner_model, 'named_steps'):
        inner = inner_model.named_steps.get('model')
        if hasattr(inner, 'coef_'):
            importances = np.abs(inner.coef_)
        else:
            importances = None
    else:
        importances = None

    if importances is not None:
        imp_df = pd.DataFrame({
            'feature': FEATURE_COLUMNS,
            'importance': importances,
        }).sort_values('importance', ascending=False)
        print("\nTop Feature Importances:")
        print(imp_df.to_string(index=False))
        imp_path = os.path.join(MODEL_DIR, 'feature_importance.csv')
        imp_df.to_csv(imp_path, index=False)

    return best_name, best['mae'], best['rmse'], best['r2']


if __name__ == '__main__':
    # Auto-generate data if not present
    if not os.path.exists(DATA_PATH):
        print(f"Dataset not found at {DATA_PATH}. Generating...")
        from ml.generate_data import generate_dataset
        os.makedirs('data/raw', exist_ok=True)
        df = generate_dataset()
        df.to_csv(DATA_PATH, index=False)
        print(f"Generated {len(df)} rows.")
    train_and_evaluate()
