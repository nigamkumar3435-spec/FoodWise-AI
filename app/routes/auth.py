from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from app import db
from app.models.user import User
from app.models.organization import Organization
from app.models.food_history import ImpactMetric

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'provider')
        org_name = request.form.get('organization_name', '').strip()
        org_type = request.form.get('organization_type', '').strip()
        city = request.form.get('city', '').strip()
        capacity = request.form.get('capacity', 0)
        accepted_categories = request.form.get('accepted_categories', '').strip()

        # Validation
        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not email or '@' not in email:
            errors.append('A valid email is required.')
        if User.query.filter_by(email=email).first():
            errors.append('Email is already registered.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if role not in ('provider', 'ngo'):
            errors.append('Invalid role selected.')
        if not org_name:
            errors.append('Organization name is required.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('auth/register.html',
                                   form_data=request.form)

        user = User(full_name=full_name, email=email, phone=phone, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.id before commit

        org = Organization(
            user_id=user.id,
            organization_name=org_name,
            organization_type=org_type if org_type else role,
            city=city,
        )
        if role == 'ngo':
            try:
                org.capacity = float(capacity) if capacity else 0.0
            except ValueError:
                org.capacity = 0.0
            org.accepted_food_categories = accepted_categories

        db.session.add(org)

        # Create blank impact metric for providers
        if role == 'provider':
            db.session.flush()
            impact = ImpactMetric(organization_id=org.id)
            db.session.add(impact)

        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form_data={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for(_dashboard_endpoint(user)))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


def _redirect_by_role(user):
    return redirect(url_for(_dashboard_endpoint(user)))


def _dashboard_endpoint(user):
    if user.is_admin():
        return 'admin.dashboard'
    elif user.is_ngo():
        return 'ngo.dashboard'
    else:
        return 'provider.dashboard'
