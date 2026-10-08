from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from functools import wraps

from app import db
from app.models.organization import Organization
from app.models.food_history import FoodHistory, DemandPrediction, ImpactMetric
from app.models.surplus import SurplusListing, DonationRequest
from app.services.prediction_service import PredictionService
from app.services.impact_service import ImpactService

provider_bp = Blueprint('provider', __name__)


def provider_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_provider():
            flash('Access denied.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return login_required(decorated)


def get_org():
    return Organization.query.filter_by(user_id=current_user.id).first()


# ─── Dashboard ────────────────────────────────────────────────────────────────

@provider_bp.route('/dashboard')
@provider_required
def dashboard():
    org = get_org()
    if not org:
        flash('Please complete your organization profile.', 'warning')
        return redirect(url_for('provider.profile'))

    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Today's prediction
    today_pred = DemandPrediction.query.filter_by(
        organization_id=org.id,
        prediction_date=today
    ).order_by(DemandPrediction.created_at.desc()).first()

    # Last 7 days history
    history_7 = FoodHistory.query.filter(
        FoodHistory.organization_id == org.id,
        FoodHistory.date >= week_ago
    ).order_by(FoodHistory.date.asc()).all()

    # Last 30 days for charts
    history_30 = FoodHistory.query.filter(
        FoodHistory.organization_id == org.id,
        FoodHistory.date >= month_ago
    ).order_by(FoodHistory.date.asc()).all()

    # Today's actual (if recorded)
    today_history = [h for h in history_7 if h.date == today]

    # KPIs
    total_prepared_month = sum(h.food_prepared or 0 for h in history_30)
    total_consumed_month = sum(h.food_consumed or 0 for h in history_30)
    total_surplus_month = sum(h.surplus_food or 0 for h in history_30)
    waste_pct = round((total_surplus_month / total_prepared_month * 100), 1) if total_prepared_month else 0

    # Impact
    impact = ImpactMetric.query.filter_by(organization_id=org.id).first()

    # Chart data
    chart_dates = [h.date.strftime('%d %b') for h in history_30]
    chart_prepared = [h.food_prepared or 0 for h in history_30]
    chart_consumed = [h.food_consumed or 0 for h in history_30]
    chart_surplus = [h.surplus_food or 0 for h in history_30]

    # Recent surplus listings
    recent_listings = SurplusListing.query.filter_by(
        provider_id=org.id
    ).order_by(SurplusListing.created_at.desc()).limit(5).all()

    # Pending donation requests
    pending_requests = db.session.query(DonationRequest).join(SurplusListing).filter(
        SurplusListing.provider_id == org.id,
        DonationRequest.request_status == 'pending'
    ).count()

    return render_template('provider/dashboard.html',
                           org=org,
                           today_pred=today_pred,
                           today_history=today_history,
                           history_7=history_7,
                           total_prepared_month=total_prepared_month,
                           total_consumed_month=total_consumed_month,
                           total_surplus_month=total_surplus_month,
                           waste_pct=waste_pct,
                           impact=impact,
                           chart_dates=chart_dates,
                           chart_prepared=chart_prepared,
                           chart_consumed=chart_consumed,
                           chart_surplus=chart_surplus,
                           recent_listings=recent_listings,
                           pending_requests=pending_requests)


# ─── Predict ──────────────────────────────────────────────────────────────────

@provider_bp.route('/predict', methods=['GET', 'POST'])
@provider_required
def predict():
    org = get_org()
    result = None

    if request.method == 'POST':
        try:
            pred_date = datetime.strptime(request.form['pred_date'], '%Y-%m-%d').date()
            meal_type = request.form['meal_type']
            num_people = int(request.form['number_of_people'])
            holiday = request.form.get('holiday') == 'on'
            event_type = request.form.get('event_type', 'normal')
            weather = request.form.get('weather_condition', 'clear')
            temperature = float(request.form.get('temperature', 25.0))
            safety_buffer = float(request.form.get('safety_buffer', 5.0)) / 100.0

            svc = PredictionService(org.id)
            result = svc.predict(
                pred_date=pred_date,
                meal_type=meal_type,
                number_of_people=num_people,
                holiday=holiday,
                event_type=event_type,
                weather_condition=weather,
                temperature=temperature,
                safety_buffer=safety_buffer,
            )

            # Persist prediction
            dp = DemandPrediction(
                organization_id=org.id,
                prediction_date=pred_date,
                meal_type=meal_type,
                predicted_demand=result['predicted_demand'],
                recommended_preparation=result['recommended_preparation'],
                confidence_score=result['confidence_score'],
                model_version=result.get('model_version', 'v1'),
            )
            db.session.add(dp)
            db.session.commit()

        except Exception as e:
            flash(f'Prediction error: {str(e)}', 'danger')

    return render_template('provider/predict.html', org=org, result=result,
                           today=date.today().isoformat())


# ─── Food History ─────────────────────────────────────────────────────────────

@provider_bp.route('/history')
@provider_required
def history():
    org = get_org()
    page = request.args.get('page', 1, type=int)
    meal_filter = request.args.get('meal_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    q = FoodHistory.query.filter_by(organization_id=org.id)
    if meal_filter:
        q = q.filter_by(meal_type=meal_filter)
    if date_from:
        try:
            q = q.filter(FoodHistory.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        except ValueError:
            pass
    if date_to:
        try:
            q = q.filter(FoodHistory.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        except ValueError:
            pass

    records = q.order_by(FoodHistory.date.desc(), FoodHistory.meal_type).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('provider/history.html', org=org, records=records,
                           meal_filter=meal_filter, date_from=date_from, date_to=date_to)


@provider_bp.route('/history/add', methods=['GET', 'POST'])
@provider_required
def add_history():
    org = get_org()
    if request.method == 'POST':
        try:
            entry_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            meal_type = request.form['meal_type']
            num_people = int(request.form['number_of_people'])
            prepared = float(request.form['food_prepared'])
            consumed = float(request.form['food_consumed'])
            event_type = request.form.get('event_type', 'normal')
            holiday = request.form.get('holiday') == 'on'
            weather = request.form.get('weather_condition', 'clear')
            temperature = float(request.form.get('temperature', 25.0))

            surplus = max(prepared - consumed, 0.0)

            record = FoodHistory(
                organization_id=org.id,
                date=entry_date,
                day_of_week=entry_date.weekday(),
                meal_type=meal_type,
                number_of_people=num_people,
                food_prepared=prepared,
                food_consumed=consumed,
                surplus_food=surplus,
                event_type=event_type,
                holiday=holiday,
                weather_condition=weather,
                temperature=temperature,
            )
            db.session.add(record)
            db.session.commit()

            # Update impact metrics
            ImpactService.update_for_org(org.id)

            flash('Food history record added successfully.', 'success')
            return redirect(url_for('provider.history'))
        except (ValueError, KeyError) as e:
            flash(f'Invalid input: {str(e)}', 'danger')

    return render_template('provider/add_history.html', org=org,
                           today=date.today().isoformat())


@provider_bp.route('/history/edit/<int:record_id>', methods=['GET', 'POST'])
@provider_required
def edit_history(record_id):
    org = get_org()
    record = FoodHistory.query.get_or_404(record_id)
    if record.organization_id != org.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('provider.history'))

    if request.method == 'POST':
        try:
            record.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            record.day_of_week = record.date.weekday()
            record.meal_type = request.form['meal_type']
            record.number_of_people = int(request.form['number_of_people'])
            record.food_prepared = float(request.form['food_prepared'])
            record.food_consumed = float(request.form['food_consumed'])
            record.surplus_food = max(record.food_prepared - record.food_consumed, 0.0)
            record.event_type = request.form.get('event_type', 'normal')
            record.holiday = request.form.get('holiday') == 'on'
            record.weather_condition = request.form.get('weather_condition', 'clear')
            record.temperature = float(request.form.get('temperature', 25.0))
            db.session.commit()
            ImpactService.update_for_org(org.id)
            flash('Record updated.', 'success')
            return redirect(url_for('provider.history'))
        except (ValueError, KeyError) as e:
            flash(f'Invalid input: {str(e)}', 'danger')

    return render_template('provider/add_history.html', org=org, record=record,
                           today=date.today().isoformat())


@provider_bp.route('/history/delete/<int:record_id>', methods=['POST'])
@provider_required
def delete_history(record_id):
    org = get_org()
    record = FoodHistory.query.get_or_404(record_id)
    if record.organization_id != org.id:
        flash('Access denied.', 'danger')
    else:
        db.session.delete(record)
        db.session.commit()
        ImpactService.update_for_org(org.id)
        flash('Record deleted.', 'success')
    return redirect(url_for('provider.history'))


# ─── Surplus ──────────────────────────────────────────────────────────────────

@provider_bp.route('/surplus')
@provider_required
def surplus():
    org = get_org()
    listings = SurplusListing.query.filter_by(provider_id=org.id).order_by(
        SurplusListing.created_at.desc()).all()
    return render_template('provider/surplus.html', org=org, listings=listings)


@provider_bp.route('/surplus/create', methods=['GET', 'POST'])
@provider_required
def create_surplus():
    org = get_org()
    if request.method == 'POST':
        if not request.form.get('food_safety_confirmed'):
            flash('You must confirm food safety before creating a listing.', 'danger')
            return render_template('provider/create_surplus.html', org=org)

        try:
            pickup_str = request.form.get('pickup_deadline', '')
            expiry_str = request.form.get('expiry_time', '')
            prep_str = request.form.get('preparation_time', '')

            listing = SurplusListing(
                provider_id=org.id,
                food_name=request.form['food_name'].strip(),
                food_category=request.form.get('food_category', 'other'),
                quantity=float(request.form['quantity']),
                unit=request.form.get('unit', 'meals'),
                preparation_time=datetime.strptime(prep_str, '%Y-%m-%dT%H:%M') if prep_str else None,
                expiry_time=datetime.strptime(expiry_str, '%Y-%m-%dT%H:%M') if expiry_str else None,
                pickup_deadline=datetime.strptime(pickup_str, '%Y-%m-%dT%H:%M') if pickup_str else None,
                latitude=float(request.form.get('latitude') or org.latitude or 0),
                longitude=float(request.form.get('longitude') or org.longitude or 0),
                notes=request.form.get('notes', '').strip(),
                food_safety_confirmed=True,
                status='available',
            )
            db.session.add(listing)
            db.session.commit()
            flash('Surplus listing created successfully.', 'success')
            return redirect(url_for('provider.matches', listing_id=listing.id))
        except (ValueError, KeyError) as e:
            flash(f'Invalid input: {str(e)}', 'danger')

    return render_template('provider/create_surplus.html', org=org)


@provider_bp.route('/surplus/matches/<int:listing_id>')
@provider_required
def matches(listing_id):
    from app.services.matching_service import MatchingService
    org = get_org()
    listing = SurplusListing.query.get_or_404(listing_id)
    if listing.provider_id != org.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('provider.surplus'))

    matched = MatchingService.find_matches(listing)
    return render_template('provider/matches.html', org=org, listing=listing, matches=matched)


@provider_bp.route('/donations')
@provider_required
def donations():
    org = get_org()
    requests = db.session.query(DonationRequest).join(SurplusListing).filter(
        SurplusListing.provider_id == org.id
    ).order_by(DonationRequest.request_time.desc()).all()
    return render_template('provider/donations.html', org=org, requests=requests)


@provider_bp.route('/donations/approve/<int:req_id>', methods=['POST'])
@provider_required
def approve_donation(req_id):
    org = get_org()
    req = DonationRequest.query.get_or_404(req_id)
    if req.surplus_listing.provider_id != org.id:
        flash('Access denied.', 'danger')
    else:
        req.request_status = 'approved'
        req.approved_time = datetime.utcnow()
        req.surplus_listing.status = 'assigned'
        db.session.commit()
        flash('Donation request approved.', 'success')
    return redirect(url_for('provider.donations'))


@provider_bp.route('/donations/complete/<int:req_id>', methods=['POST'])
@provider_required
def complete_donation(req_id):
    org = get_org()
    req = DonationRequest.query.get_or_404(req_id)
    if req.surplus_listing.provider_id != org.id:
        flash('Access denied.', 'danger')
    else:
        req.request_status = 'completed'
        req.collected_time = datetime.utcnow()
        req.surplus_listing.status = 'collected'
        ImpactService.record_donation(org.id, req.surplus_listing.quantity)
        db.session.commit()
        flash('Donation marked as completed.', 'success')
    return redirect(url_for('provider.donations'))


# ─── Analytics ────────────────────────────────────────────────────────────────

@provider_bp.route('/analytics')
@provider_required
def analytics():
    org = get_org()
    period = request.args.get('period', '30')
    try:
        days = int(period)
    except ValueError:
        days = 30

    since = date.today() - timedelta(days=days)
    history = FoodHistory.query.filter(
        FoodHistory.organization_id == org.id,
        FoodHistory.date >= since
    ).order_by(FoodHistory.date.asc()).all()

    total_prepared = sum(h.food_prepared or 0 for h in history)
    total_consumed = sum(h.food_consumed or 0 for h in history)
    total_surplus = sum(h.surplus_food or 0 for h in history)
    waste_pct = round(total_surplus / total_prepared * 100, 1) if total_prepared else 0
    avg_waste_pct = round(
        sum(h.waste_percentage for h in history) / len(history), 1
    ) if history else 0

    # Per-meal breakdown
    meal_data = {}
    for h in history:
        if h.meal_type not in meal_data:
            meal_data[h.meal_type] = {'prepared': 0, 'consumed': 0, 'surplus': 0, 'count': 0}
        meal_data[h.meal_type]['prepared'] += h.food_prepared or 0
        meal_data[h.meal_type]['consumed'] += h.food_consumed or 0
        meal_data[h.meal_type]['surplus'] += h.surplus_food or 0
        meal_data[h.meal_type]['count'] += 1

    # Predictions accuracy
    preds = DemandPrediction.query.filter(
        DemandPrediction.organization_id == org.id,
        DemandPrediction.prediction_date >= since
    ).all()

    impact = ImpactMetric.query.filter_by(organization_id=org.id).first()

    chart_dates = [h.date.strftime('%d %b') for h in history]
    chart_prepared = [h.food_prepared or 0 for h in history]
    chart_consumed = [h.food_consumed or 0 for h in history]
    chart_surplus = [h.surplus_food or 0 for h in history]

    return render_template('provider/analytics.html',
                           org=org,
                           period=period,
                           history=history,
                           total_prepared=total_prepared,
                           total_consumed=total_consumed,
                           total_surplus=total_surplus,
                           waste_pct=waste_pct,
                           avg_waste_pct=avg_waste_pct,
                           meal_data=meal_data,
                           preds=preds,
                           impact=impact,
                           chart_dates=chart_dates,
                           chart_prepared=chart_prepared,
                           chart_consumed=chart_consumed,
                           chart_surplus=chart_surplus)


# ─── AI Assistant ─────────────────────────────────────────────────────────────

@provider_bp.route('/assistant')
@provider_required
def assistant():
    org = get_org()
    return render_template('provider/assistant.html', org=org)


@provider_bp.route('/assistant/chat', methods=['POST'])
@provider_required
def assistant_chat():
    from app.services.ai_assistant import AIAssistant
    org = get_org()
    question = request.json.get('question', '').strip()
    if not question:
        return jsonify({'error': 'Empty question'}), 400
    assistant = AIAssistant(org.id)
    answer = assistant.answer(question)
    return jsonify({'answer': answer})


# ─── Profile ──────────────────────────────────────────────────────────────────

@provider_bp.route('/profile', methods=['GET', 'POST'])
@provider_required
def profile():
    org = get_org()
    if request.method == 'POST':
        if org is None:
            org = Organization(user_id=current_user.id)
            db.session.add(org)
        org.organization_name = request.form.get('organization_name', '').strip()
        org.organization_type = request.form.get('organization_type', '').strip()
        org.address = request.form.get('address', '').strip()
        org.city = request.form.get('city', '').strip()
        try:
            org.latitude = float(request.form.get('latitude') or 0)
            org.longitude = float(request.form.get('longitude') or 0)
        except ValueError:
            pass
        org.contact_number = request.form.get('contact_number', '').strip()
        current_user.full_name = request.form.get('full_name', current_user.full_name).strip()
        current_user.phone = request.form.get('phone', current_user.phone).strip()
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('provider.profile'))
    return render_template('provider/profile.html', org=org)
