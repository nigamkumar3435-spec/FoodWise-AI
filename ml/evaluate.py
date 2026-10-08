"""
Model evaluation utilities.
"""
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def print_evaluation(name: str, mae: float, rmse: float, r2: float):
    print(f"  {name}:")
    print(f"    MAE  = {mae:.2f} meals")
    print(f"    RMSE = {rmse:.2f} meals")
    print(f"    R²   = {r2:.4f}")


def evaluate_model(model, X_test, y_test):
    preds = np.maximum(model.predict(X_test), 0)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    return {
        'mae': round(mae, 2),
        'rmse': round(rmse, 2),
        'r2': round(r2, 4),
        'predictions': preds.tolist(),
    }


def foodwise_efficiency_score(waste_pct: float, prediction_accuracy_pct: float,
                               donation_rate: float) -> dict:
    """
    Custom FoodWise platform efficiency score out of 100.
    
    Components:
      - Waste reduction component:  40 pts  (lower waste → higher score)
      - Prediction accuracy:        40 pts
      - Redistribution rate:        20 pts

    This is a PLATFORM SCORE, not a statistical accuracy measure.
    """
    # Waste component: 0% waste = 40 pts, 40%+ waste = 0 pts
    waste_score = max(0.0, 40.0 * (1.0 - waste_pct / 40.0))

    # Accuracy: percentage directly mapped to 40 pts
    acc_score = min(40.0, prediction_accuracy_pct * 0.40)

    # Redistribution: 0–20 pts
    redir_score = min(20.0, donation_rate * 20.0)

    total = round(waste_score + acc_score + redir_score, 1)

    if total >= 90:
        level = 'Excellent'
    elif total >= 75:
        level = 'Good'
    elif total >= 50:
        level = 'Needs Improvement'
    else:
        level = 'High Waste'

    return {
        'score': total,
        'level': level,
        'waste_score': round(waste_score, 1),
        'accuracy_score': round(acc_score, 1),
        'redistribution_score': round(redir_score, 1),
    }
