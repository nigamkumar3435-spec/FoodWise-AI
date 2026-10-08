from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import date, timedelta

from app import db
from app.models.user import User
from app.models.organization import Organization
from app.models.food_history import FoodHistory, DemandPrediction, ImpactMetric
from app.models.surplus import SurplusListing, DonationRequest

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return login_required(decorated)


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_providers = User.query.filter_by(role='provider', is_active=True).count()
    total_ngos = User.query.filter_by(role='ngo', is_active=True).count()
    total_listings = SurplusListing.query.count()
    total_available = SurplusListing.query.filter_by(status='available').count()
    total_donations = DonationRequest.query.filter_by(request_status='completed').count()
    total_food_saved = db.session.query(
        db.func.sum(ImpactMetric.total_food_saved_kg)).scalar() or 0
    total_meals_saved = db.session.query(
        db.func.sum(ImpactMetric.meals_saved)).scalar() or 0

    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_listings = SurplusListing.query.order_by(SurplusListing.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                           total_providers=total_providers,
                           total_ngos=total_ngos,
                           total_listings=total_listings,
                           total_available=total_available,
                           total_donations=total_donations,
                           total_food_saved=round(total_food_saved, 1),
                           total_meals_saved=total_meals_saved,
                           recent_users=recent_users,
                           recent_listings=recent_listings)


@admin_bp.route('/users')
@admin_required
def users():
    role_filter = request.args.get('role', '')
    q = User.query
    if role_filter:
        q = q.filter_by(role=role_filter)
    users = q.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users, role_filter=role_filter)


@admin_bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin():
        flash('Cannot deactivate admin accounts.', 'warning')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        action = 'activated' if user.is_active else 'deactivated'
        flash(f'User {user.email} {action}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/listings')
@admin_required
def listings():
    status_filter = request.args.get('status', '')
    q = SurplusListing.query
    if status_filter:
        q = q.filter_by(status=status_filter)
    listings = q.order_by(SurplusListing.created_at.desc()).all()
    return render_template('admin/listings.html', listings=listings, status_filter=status_filter)


@admin_bp.route('/listings/delete/<int:listing_id>', methods=['POST'])
@admin_required
def delete_listing(listing_id):
    listing = SurplusListing.query.get_or_404(listing_id)
    db.session.delete(listing)
    db.session.commit()
    flash('Listing deleted.', 'success')
    return redirect(url_for('admin.listings'))


@admin_bp.route('/donations')
@admin_required
def donations():
    reqs = DonationRequest.query.order_by(DonationRequest.request_time.desc()).all()
    return render_template('admin/donations.html', requests=reqs)


@admin_bp.route('/analytics')
@admin_required
def analytics():
    since = date.today() - timedelta(days=30)
    history = FoodHistory.query.filter(FoodHistory.date >= since).all()
    total_prepared = sum(h.food_prepared or 0 for h in history)
    total_consumed = sum(h.food_consumed or 0 for h in history)
    total_surplus = sum(h.surplus_food or 0 for h in history)
    waste_pct = round(total_surplus / total_prepared * 100, 1) if total_prepared else 0

    orgs = Organization.query.all()
    return render_template('admin/analytics.html',
                           total_prepared=total_prepared,
                           total_consumed=total_consumed,
                           total_surplus=total_surplus,
                           waste_pct=waste_pct,
                           orgs=orgs)
