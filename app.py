"""
FoodWise AI — Application Entry Point
"""
import os
from app import create_app, db
from app.models import User, Organization, FoodHistory, ImpactMetric

app = create_app(os.environ.get('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Organization=Organization,
                FoodHistory=FoodHistory, ImpactMetric=ImpactMetric)


@app.cli.command('seed-admin')
def seed_admin():
    """Create the default admin account from environment variables."""
    email = os.environ.get('ADMIN_EMAIL', 'admin@foodwise.ai')
    password = os.environ.get('ADMIN_PASSWORD', 'Admin@FoodWise123')

    if User.query.filter_by(email=email).first():
        print(f'Admin {email} already exists.')
        return

    admin = User(full_name='FoodWise Admin', email=email, role='admin', phone='')
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f'Admin account created: {email}')


@app.cli.command('seed-demo')
def seed_demo():
    """Seed demo provider + NGO + food history for demonstration."""
    from app.services.impact_service import ImpactService
    import random
    from datetime import date, timedelta

    random.seed(1)

    # Provider
    prov_email = 'demo.canteen@foodwise.ai'
    if not User.query.filter_by(email=prov_email).first():
        prov_user = User(full_name='Demo College Canteen', email=prov_email,
                         phone='9800000001', role='provider')
        prov_user.set_password('Demo@1234')
        db.session.add(prov_user)
        db.session.flush()
        prov_org = Organization(user_id=prov_user.id,
                                organization_name='GreenField College Canteen',
                                organization_type='canteen',
                                city='Bangalore',
                                latitude=12.9716, longitude=77.5946)
        db.session.add(prov_org)
        db.session.flush()
        impact = ImpactMetric(organization_id=prov_org.id)
        db.session.add(impact)
        db.session.flush()

        # Seed 60 days of history
        today = date.today()
        for offset in range(60, 0, -1):
            d = today - timedelta(days=offset)
            for meal in ('breakfast', 'lunch', 'dinner'):
                base = {'breakfast': 120, 'lunch': 350, 'dinner': 200}[meal]
                people = base + random.randint(-20, 20)
                prepared = int(people * random.uniform(1.10, 1.20))
                consumed = int(prepared * random.uniform(0.78, 0.95))
                surplus = max(prepared - consumed, 0)
                entry = FoodHistory(
                    organization_id=prov_org.id,
                    date=d, day_of_week=d.weekday(), meal_type=meal,
                    number_of_people=people, food_prepared=prepared,
                    food_consumed=consumed, surplus_food=surplus,
                    event_type='normal', holiday=False,
                    weather_condition='clear', temperature=28.0,
                )
                db.session.add(entry)
        db.session.commit()
        ImpactService.update_for_org(prov_org.id)
        print(f'Demo provider created: {prov_email} / Demo@1234')

    # NGO
    ngo_email = 'demo.ngo@foodwise.ai'
    if not User.query.filter_by(email=ngo_email).first():
        ngo_user = User(full_name='Helping Hands Foundation', email=ngo_email,
                        phone='9800000002', role='ngo')
        ngo_user.set_password('Demo@1234')
        db.session.add(ngo_user)
        db.session.flush()
        ngo_org = Organization(user_id=ngo_user.id,
                               organization_name='Helping Hands Foundation',
                               organization_type='ngo',
                               city='Bangalore',
                               latitude=12.9600, longitude=77.6100,
                               capacity=500,
                               accepted_food_categories='rice,dal,bread,vegetables,mixed')
        db.session.add(ngo_org)
        db.session.commit()
        print(f'Demo NGO created: {ngo_email} / Demo@1234')

    print('Demo seed complete.')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
