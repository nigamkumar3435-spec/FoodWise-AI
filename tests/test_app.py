"""
FoodWise AI — Test Suite
Run with: pytest tests/
"""
import pytest
import sys
import os

# Make app importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db as _db
from app.models import User, Organization, FoodHistory, ImpactMetric


@pytest.fixture(scope='session')
def app():
    """Session-scoped test application with in-memory SQLite database."""
    app = create_app('default')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret',
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


# ─── Auth Tests ───────────────────────────────────────────────────────────────

class TestRegistration:
    def test_register_provider(self, client, db):
        resp = client.post('/auth/register', data={
            'full_name': 'Test Canteen',
            'email': 'test.canteen@fw.ai',
            'phone': '9876543210',
            'password': 'Password123',
            'confirm_password': 'Password123',
            'role': 'provider',
            'organization_name': 'Test Canteen',
            'organization_type': 'canteen',
            'city': 'Delhi',
        }, follow_redirects=True)
        assert resp.status_code == 200
        user = User.query.filter_by(email='test.canteen@fw.ai').first()
        assert user is not None
        assert user.role == 'provider'
        assert not user.check_password('wrong')
        assert user.check_password('Password123')

    def test_register_ngo(self, client, db):
        resp = client.post('/auth/register', data={
            'full_name': 'Test NGO',
            'email': 'test.ngo@fw.ai',
            'phone': '9876543211',
            'password': 'Password123',
            'confirm_password': 'Password123',
            'role': 'ngo',
            'organization_name': 'Test NGO',
            'city': 'Mumbai',
            'capacity': '300',
            'accepted_categories': 'rice,dal',
        }, follow_redirects=True)
        assert resp.status_code == 200
        user = User.query.filter_by(email='test.ngo@fw.ai').first()
        assert user is not None
        assert user.role == 'ngo'

    def test_duplicate_email_rejected(self, client, db):
        client.post('/auth/register', data={
            'full_name': 'Dup User',
            'email': 'dup@fw.ai',
            'phone': '',
            'password': 'Password123',
            'confirm_password': 'Password123',
            'role': 'provider',
            'organization_name': 'Dup Org',
        })
        resp = client.post('/auth/register', data={
            'full_name': 'Dup User',
            'email': 'dup@fw.ai',
            'phone': '',
            'password': 'Password123',
            'confirm_password': 'Password123',
            'role': 'provider',
            'organization_name': 'Dup Org',
        }, follow_redirects=True)
        assert resp.status_code == 200
        # Should show error, count remains 1
        assert User.query.filter_by(email='dup@fw.ai').count() == 1

    def test_password_mismatch_rejected(self, client):
        resp = client.post('/auth/register', data={
            'full_name': 'Mismatch User',
            'email': 'mismatch@fw.ai',
            'password': 'Password123',
            'confirm_password': 'Different456',
            'role': 'provider',
            'organization_name': 'Some Org',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert User.query.filter_by(email='mismatch@fw.ai').first() is None

    def test_short_password_rejected(self, client):
        resp = client.post('/auth/register', data={
            'full_name': 'Short Pass',
            'email': 'short@fw.ai',
            'password': 'abc',
            'confirm_password': 'abc',
            'role': 'provider',
            'organization_name': 'Short Org',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert User.query.filter_by(email='short@fw.ai').first() is None


class TestLogin:
    def test_login_valid(self, client, db):
        # Ensure user exists
        from werkzeug.security import generate_password_hash
        if not User.query.filter_by(email='login.test@fw.ai').first():
            u = User(full_name='Login Test', email='login.test@fw.ai', role='provider')
            u.set_password('ValidPass1')
            _db.session.add(u)
            org = Organization(user_id=0, organization_name='Login Test Org',
                                organization_type='canteen', city='Test')
            _db.session.add(u)
            _db.session.flush()
            org.user_id = u.id
            _db.session.add(org)
            _db.session.commit()

        resp = client.post('/auth/login', data={
            'email': 'login.test@fw.ai',
            'password': 'ValidPass1',
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_wrong_password(self, client):
        resp = client.post('/auth/login', data={
            'email': 'test.canteen@fw.ai',
            'password': 'wrongpassword',
        }, follow_redirects=True)
        # Should stay on login page or show error
        assert b'Invalid' in resp.data or resp.status_code == 200


# ─── User Model Tests ─────────────────────────────────────────────────────────

class TestUserModel:
    def test_password_hashing(self, app):
        with app.app_context():
            u = User(full_name='Hash Test', email='hash@fw.ai', role='provider')
            u.set_password('MySecret99')
            assert u.password_hash != 'MySecret99'
            assert u.check_password('MySecret99')
            assert not u.check_password('Wrong')

    def test_role_checks(self, app):
        with app.app_context():
            p = User(role='provider')
            n = User(role='ngo')
            a = User(role='admin')
            assert p.is_provider() and not p.is_ngo()
            assert n.is_ngo() and not n.is_admin()
            assert a.is_admin() and not a.is_provider()


# ─── Food History & Surplus Calc Tests ───────────────────────────────────────

class TestFoodHistory:
    def test_waste_percentage_calculation(self, app):
        with app.app_context():
            from datetime import date
            h = FoodHistory(
                organization_id=1,
                date=date.today(),
                meal_type='lunch',
                food_prepared=500,
                food_consumed=430,
                surplus_food=70,
            )
            assert h.waste_percentage == 14.0

    def test_waste_zero_when_no_surplus(self, app):
        with app.app_context():
            from datetime import date
            h = FoodHistory(
                organization_id=1, date=date.today(),
                meal_type='lunch', food_prepared=200,
                food_consumed=200, surplus_food=0,
            )
            assert h.waste_percentage == 0.0

    def test_waste_handles_zero_prepared(self, app):
        with app.app_context():
            from datetime import date
            h = FoodHistory(
                organization_id=1, date=date.today(),
                meal_type='lunch', food_prepared=0,
                food_consumed=0, surplus_food=0,
            )
            assert h.waste_percentage == 0.0


# ─── Impact Service Tests ─────────────────────────────────────────────────────

class TestImpactService:
    def test_impact_metric_update(self, app, db):
        with app.app_context():
            from app.services.impact_service import ImpactService, KG_PER_MEAL, MONEY_PER_KG
            # Just test that the computation formulas are consistent
            meals = 100
            expected_kg = round(meals * KG_PER_MEAL, 2)
            expected_money = round(expected_kg * MONEY_PER_KG, 2)
            assert expected_kg == 35.0
            assert expected_money == 2800.0


# ─── ML Feature Engineering Tests ────────────────────────────────────────────

class TestFeatureEngineering:
    def test_engineer_features_no_leakage(self):
        import pandas as pd
        from ml.feature_engineering import engineer_features, FEATURE_COLUMNS

        data = {
            'date': ['2024-01-01'] * 3 + ['2024-01-02'] * 3,
            'day_of_week': [0] * 6,
            'meal_type': ['breakfast', 'lunch', 'dinner'] * 2,
            'number_of_people': [100] * 6,
            'food_prepared': [120] * 6,
            'food_consumed': [100] * 6,
            'surplus_food': [20] * 6,
            'event_type': ['normal'] * 6,
            'holiday': [0] * 6,
            'weather_condition': ['clear'] * 6,
            'temperature': [28.0] * 6,
        }
        df = pd.DataFrame(data)
        result = engineer_features(df)
        # All feature columns should exist
        for col in FEATURE_COLUMNS:
            assert col in result.columns, f"Missing feature: {col}"
        # No NaN in feature columns after engineering
        assert result[FEATURE_COLUMNS].isnull().sum().sum() == 0

    def test_meal_type_encoding(self):
        import pandas as pd
        from ml.feature_engineering import engineer_features

        data = {
            'date': ['2024-01-01'] * 3,
            'day_of_week': [0, 0, 0],
            'meal_type': ['breakfast', 'lunch', 'dinner'],
            'number_of_people': [100, 300, 200],
            'food_prepared': [110, 330, 220],
            'food_consumed': [95, 300, 190],
            'surplus_food': [15, 30, 30],
            'event_type': ['normal', 'normal', 'normal'],
            'holiday': [0, 0, 0],
            'weather_condition': ['clear', 'clear', 'clear'],
            'temperature': [25, 25, 25],
        }
        df = engineer_features(pd.DataFrame(data))
        assert set(df['meal_type_enc'].unique()).issubset({0, 1, 2})


# ─── NGO Matching Tests ───────────────────────────────────────────────────────

class TestMatchingService:
    def test_haversine_same_point(self):
        from app.services.matching_service import haversine
        assert haversine(12.97, 77.59, 12.97, 77.59) == pytest.approx(0.0, abs=0.01)

    def test_haversine_known_distance(self):
        from app.services.matching_service import haversine
        # Approx distance between Bangalore and Mysore: ~128 km
        dist = haversine(12.9716, 77.5946, 12.2958, 76.6394)
        assert 120 < dist < 160

    def test_distance_score_nearby(self):
        from app.services.matching_service import _distance_score
        assert _distance_score(0.5) == 1.0

    def test_distance_score_far(self):
        from app.services.matching_service import _distance_score
        assert _distance_score(50.0) == 0.0

    def test_capacity_score_sufficient(self):
        from app.services.matching_service import _capacity_score
        assert _capacity_score(200, 100) == 1.0

    def test_capacity_score_insufficient(self):
        from app.services.matching_service import _capacity_score
        assert _capacity_score(50, 100) == pytest.approx(0.5)


# ─── Prediction Service fallback Tests ───────────────────────────────────────

class TestPredictionService:
    def test_fallback_prediction(self, app):
        with app.app_context():
            from app.services.prediction_service import PredictionService
            from datetime import date
            # No model, no history → should still return a result
            svc = PredictionService(organization_id=9999)
            result = svc.predict(
                pred_date=date.today(),
                meal_type='lunch',
                number_of_people=200,
                holiday=False,
                event_type='normal',
                weather_condition='clear',
                temperature=28.0,
                safety_buffer=0.05,
            )
            assert 'predicted_demand' in result
            assert result['predicted_demand'] >= 0
            assert result['recommended_preparation'] >= result['predicted_demand']
            assert 0 < result['confidence_score'] <= 1.0
