"""
ImpactService — recalculates and persists ImpactMetric for an organization.
Called after food history writes and donation completions.
"""
from datetime import date, timedelta
from app import db
from app.models.food_history import FoodHistory, ImpactMetric
from app.models.surplus import DonationRequest, SurplusListing

# Approximate kg per meal portion
KG_PER_MEAL = 0.35
# Approximate money saved per kg (INR)
MONEY_PER_KG = 80.0


class ImpactService:

    @staticmethod
    def update_for_org(organization_id: int):
        """Recompute all impact metrics for the organization from scratch."""
        history = FoodHistory.query.filter_by(organization_id=organization_id).all()

        total_prepared = sum(h.food_prepared or 0 for h in history)
        total_consumed = sum(h.food_consumed or 0 for h in history)
        total_surplus = sum(h.surplus_food or 0 for h in history)

        waste_pct = round(total_surplus / total_prepared * 100, 1) if total_prepared else 0.0

        # Completed donations for this org (as provider)
        completed = (
            db.session.query(DonationRequest)
            .join(SurplusListing, DonationRequest.surplus_listing_id == SurplusListing.id)
            .filter(
                SurplusListing.provider_id == organization_id,
                DonationRequest.request_status == 'completed',
            )
            .all()
        )
        donated_meals = sum(r.surplus_listing.quantity for r in completed if r.surplus_listing)
        donated_kg = donated_meals * KG_PER_MEAL
        money_saved = donated_kg * MONEY_PER_KG

        impact = ImpactMetric.query.filter_by(organization_id=organization_id).first()
        if impact is None:
            impact = ImpactMetric(organization_id=organization_id)
            db.session.add(impact)

        impact.total_food_saved_kg = round(donated_kg, 2)
        impact.meals_saved = int(donated_meals)
        impact.money_saved = round(money_saved, 2)
        impact.successful_donations = len(completed)
        impact.waste_reduction_percentage = waste_pct

        db.session.commit()

    @staticmethod
    def record_donation(organization_id: int, quantity: float):
        """Quick increment after a single donation completes."""
        impact = ImpactMetric.query.filter_by(organization_id=organization_id).first()
        if impact is None:
            impact = ImpactMetric(organization_id=organization_id)
            db.session.add(impact)

        kg = quantity * KG_PER_MEAL
        impact.total_food_saved_kg = round((impact.total_food_saved_kg or 0) + kg, 2)
        impact.meals_saved = (impact.meals_saved or 0) + int(quantity)
        impact.money_saved = round((impact.money_saved or 0) + kg * MONEY_PER_KG, 2)
        impact.successful_donations = (impact.successful_donations or 0) + 1
        db.session.commit()
        # Full recalc for accurate waste % and other metrics
        ImpactService.update_for_org(organization_id)
