from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, date

from app import db
from app.models.organization import Organization
from app.models.food_history import FoodHistory, ImpactMetric
from app.models.surplus import SurplusListing, DonationRequest
from app.services.prediction_service import PredictionService
from app.services.matching_service import MatchingService
from app.services.impact_service import ImpactService

api_bp = Blueprint('api', __name__)


def _json_ok(data=None, message='OK'):
    return jsonify({'success': True, 'data': data, 'message': message})


def _json_err(message, status=400):
    return jsonify({'success': False, 'data': None, 'message': message}), status


@api_bp.route('/predict-demand', methods=['POST'])
@login_required
def predict_demand():
    org = Organization.query.filter_by(user_id=current_user.id).first()
    if not org:
        return _json_err('Organization not found.', 404)
    payload = request.get_json() or {}
    try:
        svc = PredictionService(org.id)
        result = svc.predict(
            pred_date=datetime.strptime(payload['pred_date'], '%Y-%m-%d').date(),
            meal_type=payload.get('meal_type', 'lunch'),
            number_of_people=int(payload.get('number_of_people', 100)),
            holiday=bool(payload.get('holiday', False)),
            event_type=payload.get('event_type', 'normal'),
            weather_condition=payload.get('weather_condition', 'clear'),
            temperature=float(payload.get('temperature', 25.0)),
            safety_buffer=float(payload.get('safety_buffer', 0.05)),
        )
        return _json_ok(result, 'Prediction completed successfully.')
    except Exception as e:
        return _json_err(str(e))


@api_bp.route('/dashboard-stats', methods=['GET'])
@login_required
def dashboard_stats():
    org = Organization.query.filter_by(user_id=current_user.id).first()
    if not org:
        return _json_err('Organization not found.', 404)
    impact = ImpactMetric.query.filter_by(organization_id=org.id).first()
    data = {
        'meals_saved': impact.meals_saved if impact else 0,
        'total_food_saved_kg': impact.total_food_saved_kg if impact else 0,
        'successful_donations': impact.successful_donations if impact else 0,
        'waste_reduction_percentage': impact.waste_reduction_percentage if impact else 0,
    }
    return _json_ok(data)


@api_bp.route('/food-history', methods=['POST'])
@login_required
def add_food_history():
    org = Organization.query.filter_by(user_id=current_user.id).first()
    if not org:
        return _json_err('Organization not found.', 404)
    payload = request.get_json() or {}
    try:
        entry_date = datetime.strptime(payload['date'], '%Y-%m-%d').date()
        prepared = float(payload['food_prepared'])
        consumed = float(payload['food_consumed'])
        surplus = max(prepared - consumed, 0.0)
        record = FoodHistory(
            organization_id=org.id,
            date=entry_date,
            day_of_week=entry_date.weekday(),
            meal_type=payload.get('meal_type', 'lunch'),
            number_of_people=int(payload.get('number_of_people', 0)),
            food_prepared=prepared,
            food_consumed=consumed,
            surplus_food=surplus,
            event_type=payload.get('event_type', 'normal'),
            holiday=bool(payload.get('holiday', False)),
            weather_condition=payload.get('weather_condition', 'clear'),
            temperature=float(payload.get('temperature', 25.0)),
        )
        db.session.add(record)
        db.session.commit()
        ImpactService.update_for_org(org.id)
        return _json_ok(record.to_dict(), 'Record added.')
    except Exception as e:
        return _json_err(str(e))


@api_bp.route('/food-history', methods=['GET'])
@login_required
def get_food_history():
    org = Organization.query.filter_by(user_id=current_user.id).first()
    if not org:
        return _json_err('Organization not found.', 404)
    records = FoodHistory.query.filter_by(organization_id=org.id).order_by(
        FoodHistory.date.desc()).limit(100).all()
    return _json_ok([r.to_dict() for r in records])


@api_bp.route('/surplus', methods=['POST'])
@login_required
def create_surplus():
    org = Organization.query.filter_by(user_id=current_user.id).first()
    if not org:
        return _json_err('Organization not found.', 404)
    payload = request.get_json() or {}
    if not payload.get('food_safety_confirmed'):
        return _json_err('Food safety must be confirmed.')
    try:
        listing = SurplusListing(
            provider_id=org.id,
            food_name=payload['food_name'],
            food_category=payload.get('food_category', 'other'),
            quantity=float(payload['quantity']),
            unit=payload.get('unit', 'meals'),
            food_safety_confirmed=True,
            status='available',
        )
        db.session.add(listing)
        db.session.commit()
        return _json_ok(listing.to_dict(), 'Surplus listing created.')
    except Exception as e:
        return _json_err(str(e))


@api_bp.route('/surplus', methods=['GET'])
@login_required
def get_surplus():
    listings = SurplusListing.query.filter_by(status='available').all()
    return _json_ok([l.to_dict() for l in listings])


@api_bp.route('/matches/<int:listing_id>', methods=['GET'])
@login_required
def get_matches(listing_id):
    listing = SurplusListing.query.get_or_404(listing_id)
    matches = MatchingService.find_matches(listing)
    return _json_ok(matches)


@api_bp.route('/donation-request', methods=['POST'])
@login_required
def create_donation_request():
    org = Organization.query.filter_by(user_id=current_user.id).first()
    if not org:
        return _json_err('Organization not found.', 404)
    payload = request.get_json() or {}
    listing = SurplusListing.query.get(payload.get('surplus_listing_id'))
    if not listing or listing.status != 'available':
        return _json_err('Listing not available.')
    req = DonationRequest(
        surplus_listing_id=listing.id,
        ngo_id=org.id,
        request_status='pending',
    )
    listing.status = 'requested'
    db.session.add(req)
    db.session.commit()
    return _json_ok(req.to_dict(), 'Request submitted.')


@api_bp.route('/donation-request/<int:req_id>', methods=['PATCH'])
@login_required
def update_donation_request(req_id):
    req = DonationRequest.query.get_or_404(req_id)
    payload = request.get_json() or {}
    new_status = payload.get('status')
    allowed = ('approved', 'rejected', 'completed')
    if new_status not in allowed:
        return _json_err(f'Status must be one of: {allowed}')
    req.request_status = new_status
    if new_status == 'approved':
        req.approved_time = datetime.utcnow()
        req.surplus_listing.status = 'assigned'
    elif new_status == 'completed':
        req.collected_time = datetime.utcnow()
        req.surplus_listing.status = 'collected'
    db.session.commit()
    return _json_ok(req.to_dict(), 'Status updated.')


@api_bp.route('/impact', methods=['GET'])
@login_required
def get_impact():
    org = Organization.query.filter_by(user_id=current_user.id).first()
    if not org:
        return _json_err('Organization not found.', 404)
    impact = ImpactMetric.query.filter_by(organization_id=org.id).first()
    if not impact:
        return _json_ok({})
    return _json_ok({
        'total_food_saved_kg': impact.total_food_saved_kg,
        'meals_saved': impact.meals_saved,
        'money_saved': impact.money_saved,
        'successful_donations': impact.successful_donations,
        'waste_reduction_percentage': impact.waste_reduction_percentage,
    })


@api_bp.route('/assistant', methods=['POST'])
@login_required
def assistant():
    from app.services.ai_assistant import AIAssistant
    org = Organization.query.filter_by(user_id=current_user.id).first()
    if not org:
        return _json_err('Organization not found.', 404)
    payload = request.get_json() or {}
    question = payload.get('question', '').strip()
    if not question:
        return _json_err('Question is required.')
    ai = AIAssistant(org.id)
    answer = ai.answer(question)
    return _json_ok({'answer': answer})
