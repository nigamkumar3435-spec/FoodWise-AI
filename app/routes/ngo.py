from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from functools import wraps

from app import db
from app.models.organization import Organization
from app.models.surplus import SurplusListing, DonationRequest
from app.models.food_history import ImpactMetric
from app.services.impact_service import ImpactService

ngo_bp = Blueprint('ngo', __name__)


def ngo_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_ngo():
            flash('Access denied.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return login_required(decorated)


def get_org():
    return Organization.query.filter_by(user_id=current_user.id).first()


@ngo_bp.route('/dashboard')
@ngo_required
def dashboard():
    org = get_org()

    # Available food listings
    available = SurplusListing.query.filter_by(status='available').order_by(
        SurplusListing.created_at.desc()).limit(10).all()

    # Pending requests by this NGO
    pending = DonationRequest.query.filter_by(
        ngo_id=org.id, request_status='pending').count()

    # Completed donations
    completed = DonationRequest.query.filter_by(
        ngo_id=org.id, request_status='completed').all()

    total_meals = sum(r.surplus_listing.quantity for r in completed
                      if r.surplus_listing)

    return render_template('ngo/dashboard.html',
                           org=org,
                           available=available,
                           pending=pending,
                           completed=completed,
                           total_meals=total_meals)


@ngo_bp.route('/available')
@ngo_required
def available_food():
    org = get_org()
    category_filter = request.args.get('category', '')
    listings = SurplusListing.query.filter_by(status='available')
    if category_filter:
        listings = listings.filter_by(food_category=category_filter)
    listings = listings.order_by(SurplusListing.pickup_deadline.asc()).all()

    # Attach distance if coords available
    from app.services.matching_service import haversine
    for l in listings:
        if org.latitude and org.longitude and l.latitude and l.longitude:
            l.distance_km = round(haversine(org.latitude, org.longitude,
                                            l.latitude, l.longitude), 1)
        else:
            l.distance_km = None

    return render_template('ngo/available_food.html',
                           org=org,
                           listings=listings,
                           category_filter=category_filter)


@ngo_bp.route('/request/<int:listing_id>', methods=['POST'])
@ngo_required
def request_food(listing_id):
    org = get_org()
    listing = SurplusListing.query.get_or_404(listing_id)
    if listing.status != 'available':
        flash('This food listing is no longer available.', 'warning')
        return redirect(url_for('ngo.available_food'))

    # Check if already requested
    existing = DonationRequest.query.filter_by(
        surplus_listing_id=listing_id, ngo_id=org.id).first()
    if existing:
        flash('You have already requested this listing.', 'info')
        return redirect(url_for('ngo.available_food'))

    req = DonationRequest(
        surplus_listing_id=listing_id,
        ngo_id=org.id,
        request_status='pending',
    )
    listing.status = 'requested'
    db.session.add(req)
    db.session.commit()
    flash('Food request sent to the provider.', 'success')
    return redirect(url_for('ngo.requests'))


@ngo_bp.route('/requests')
@ngo_required
def requests():
    org = get_org()
    reqs = DonationRequest.query.filter_by(ngo_id=org.id).order_by(
        DonationRequest.request_time.desc()).all()
    return render_template('ngo/requests.html', org=org, requests=reqs)


@ngo_bp.route('/history')
@ngo_required
def donation_history():
    org = get_org()
    completed = DonationRequest.query.filter_by(
        ngo_id=org.id, request_status='completed'
    ).order_by(DonationRequest.collected_time.desc()).all()
    total_meals = sum(r.surplus_listing.quantity for r in completed if r.surplus_listing)
    return render_template('ngo/donation_history.html',
                           org=org, completed=completed, total_meals=total_meals)


@ngo_bp.route('/profile', methods=['GET', 'POST'])
@ngo_required
def profile():
    org = get_org()
    if request.method == 'POST':
        if org is None:
            org = Organization(user_id=current_user.id)
            db.session.add(org)
        org.organization_name = request.form.get('organization_name', '').strip()
        org.city = request.form.get('city', '').strip()
        org.address = request.form.get('address', '').strip()
        org.contact_number = request.form.get('contact_number', '').strip()
        try:
            org.capacity = float(request.form.get('capacity') or 0)
            org.latitude = float(request.form.get('latitude') or 0)
            org.longitude = float(request.form.get('longitude') or 0)
        except ValueError:
            pass
        org.accepted_food_categories = request.form.get('accepted_categories', '').strip()
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('ngo.profile'))
    return render_template('ngo/profile.html', org=org)
