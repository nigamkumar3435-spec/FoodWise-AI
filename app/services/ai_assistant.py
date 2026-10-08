"""
AIAssistant — rule-based intelligent food management assistant.
Derives all answers from real database values for the organization.
Falls back to an external LLM if configured (see llm_service.py).
"""
from datetime import date, timedelta
from app.models.food_history import FoodHistory, DemandPrediction, ImpactMetric
from app.models.surplus import SurplusListing, DonationRequest
from app.models.organization import Organization
from app import db


class AIAssistant:
    def __init__(self, organization_id: int):
        self.org_id = organization_id
        self._stats = None

    def _load_stats(self):
        if self._stats is not None:
            return self._stats

        today = date.today()
        week_ago = today - timedelta(days=7)
        two_weeks_ago = today - timedelta(days=14)
        month_ago = today - timedelta(days=30)

        last_7 = FoodHistory.query.filter(
            FoodHistory.organization_id == self.org_id,
            FoodHistory.date >= week_ago
        ).all()
        prev_7 = FoodHistory.query.filter(
            FoodHistory.organization_id == self.org_id,
            FoodHistory.date >= two_weeks_ago,
            FoodHistory.date < week_ago
        ).all()
        last_30 = FoodHistory.query.filter(
            FoodHistory.organization_id == self.org_id,
            FoodHistory.date >= month_ago
        ).all()

        def waste_pct(records):
            total_prep = sum(r.food_prepared or 0 for r in records)
            total_surplus = sum(r.surplus_food or 0 for r in records)
            return round(total_surplus / total_prep * 100, 1) if total_prep else 0.0

        # Day with highest waste this week
        worst_day = None
        worst_day_waste = 0
        for r in last_7:
            if r.waste_percentage > worst_day_waste:
                worst_day_waste = r.waste_percentage
                worst_day = r

        # Meal with highest surplus
        meal_surplus = {}
        for r in last_7:
            mt = r.meal_type or 'unknown'
            meal_surplus[mt] = meal_surplus.get(mt, 0) + (r.surplus_food or 0)
        worst_meal = max(meal_surplus, key=meal_surplus.get) if meal_surplus else None
        worst_meal_surplus = meal_surplus.get(worst_meal, 0) if worst_meal else 0

        impact = ImpactMetric.query.filter_by(organization_id=self.org_id).first()
        completed_donations = DonationRequest.query.join(SurplusListing).filter(
            SurplusListing.provider_id == self.org_id,
            DonationRequest.request_status == 'completed'
        ).count()

        self._stats = {
            'last_7': last_7,
            'prev_7': prev_7,
            'last_30': last_30,
            'waste_pct_this_week': waste_pct(last_7),
            'waste_pct_last_week': waste_pct(prev_7),
            'total_surplus_week': sum(r.surplus_food or 0 for r in last_7),
            'total_prepared_week': sum(r.food_prepared or 0 for r in last_7),
            'total_consumed_week': sum(r.food_consumed or 0 for r in last_7),
            'worst_day': worst_day,
            'worst_day_waste': worst_day_waste,
            'worst_meal': worst_meal,
            'worst_meal_surplus': worst_meal_surplus,
            'impact': impact,
            'completed_donations': completed_donations,
        }
        return self._stats

    def answer(self, question: str) -> str:
        """Generate an answer grounded in real data."""
        # Try external LLM first if configured
        try:
            from app.services.llm_service import LLMService
            llm = LLMService()
            if llm.is_available():
                context = self._build_context_string()
                return llm.ask(question, context)
        except Exception:
            pass

        # Rule-based engine
        return self._rule_based_answer(question.lower())

    def _rule_based_answer(self, q: str) -> str:
        s = self._load_stats()
        today = date.today()

        # --- Tomorrow's preparation ---
        if any(kw in q for kw in ['tomorrow', 'prepare tomorrow', 'how much', 'predict']):
            pred = DemandPrediction.query.filter_by(
                organization_id=self.org_id,
                prediction_date=today + timedelta(days=1)
            ).order_by(DemandPrediction.created_at.desc()).first()
            if pred:
                return (
                    f"Based on your ML prediction for tomorrow:\n\n"
                    f"• **Predicted demand:** {round(pred.predicted_demand)} meals\n"
                    f"• **Recommended preparation:** {round(pred.recommended_preparation)} meals "
                    f"(includes {pred.confidence_score:.0%} confidence safety buffer)\n\n"
                    f"Head to the **Predict** page to get an updated forecast with tomorrow's conditions."
                )
            if s['last_7']:
                avg = round(s['total_consumed_week'] / max(len(s['last_7']), 1))
                return (
                    f"No prediction has been made for tomorrow yet.\n\n"
                    f"Based on your last 7 days, average consumption was **{avg} meals per session**.\n\n"
                    f"Use the **Predict** page to generate a machine-learning forecast."
                )
            return "No historical data found yet. Add food records first to enable predictions."

        # --- Waste increase explanation ---
        if any(kw in q for kw in ['waste increase', 'waste increased', 'why waste', 'waste went up']):
            this = s['waste_pct_this_week']
            last = s['waste_pct_last_week']
            if this > last and last > 0:
                diff = round(this - last, 1)
                resp = (
                    f"Your food waste **increased from {last}% last week to {this}% this week** "
                    f"(+{diff} percentage points).\n\n"
                )
                if s['worst_day']:
                    day_name = s['worst_day'].date.strftime('%A')
                    resp += (
                        f"The largest surplus occurred on **{day_name} {s['worst_day'].meal_type}** "
                        f"({round(s['worst_day_waste'])}% waste).\n\n"
                    )
                if s['worst_meal']:
                    resp += (
                        f"**{s['worst_meal'].capitalize()}** had the highest surplus this week "
                        f"({round(s['worst_meal_surplus'])} meals).\n\n"
                    )
                resp += "Consider reducing preparation for the identified high-waste periods by 7–10%."
                return resp
            elif this <= last:
                return (
                    f"Good news — your waste did not increase this week.\n\n"
                    f"This week: **{this}%** vs last week: **{last}%**."
                )
            return "Insufficient data to compare waste trends. Add more history records."

        # --- Reduce waste tips ---
        if any(kw in q for kw in ['reduce', 'tips', 'how can i', 'improve', 'suggestion']):
            tips = [
                "1. **Use ML predictions** before each meal session to calibrate preparation.",
                "2. **Reduce Friday dinner** preparation — weekends often have lower institutional attendance.",
                "3. **Track event days** (conferences, holidays) and adjust separately.",
                "4. **Set a 5% safety buffer** rather than 15–20% — the model accounts for uncertainty.",
                "5. **List surplus immediately** — food redistribution maximises utilization.",
            ]
            if s['worst_meal']:
                tips.insert(0, f"0. Your highest surplus meal is **{s['worst_meal']}** — focus there first.")
            return "\n".join(tips)

        # --- Highest waste day ---
        if any(kw in q for kw in ['highest waste', 'worst day', 'most waste', 'which day']):
            if s['worst_day']:
                day_name = s['worst_day'].date.strftime('%A, %d %b')
                return (
                    f"The day with the **highest food waste** this week was "
                    f"**{day_name}** ({s['worst_day'].meal_type}) "
                    f"with {round(s['worst_day_waste'])}% waste "
                    f"({round(s['worst_day'].surplus_food or 0)} surplus meals)."
                )
            return "No food history found for this week. Please add records."

        # --- Food saved this month ---
        if any(kw in q for kw in ['food saved', 'how much saved', 'saved this month', 'savings']):
            if s['impact']:
                return (
                    f"This month your organization has:\n\n"
                    f"• **Food saved:** {round(s['impact'].total_food_saved_kg, 1)} kg\n"
                    f"• **Meals redistributed:** {s['impact'].meals_saved}\n"
                    f"• **Successful donations:** {s['completed_donations']}\n"
                    f"• **Estimated money saved:** ₹{round(s['impact'].money_saved):,}\n\n"
                    f"Keep adding surplus listings to increase your impact!"
                )
            return "No impact data available yet. Complete your first donation to see savings."

        # --- Current week summary ---
        if any(kw in q for kw in ['this week', 'weekly', 'summary', 'report', 'overview']):
            if not s['last_7']:
                return "No data available for this week yet."
            sessions = len(s['last_7'])
            return (
                f"**This week's summary ({sessions} sessions):**\n\n"
                f"• Total prepared: **{round(s['total_prepared_week'])} meals**\n"
                f"• Total consumed: **{round(s['total_consumed_week'])} meals**\n"
                f"• Total surplus: **{round(s['total_surplus_week'])} meals**\n"
                f"• Waste rate: **{s['waste_pct_this_week']}%**\n"
                f"• Successful donations: **{s['completed_donations']}**\n\n"
                + (f"Waste is {'higher' if s['waste_pct_this_week'] > s['waste_pct_last_week'] else 'lower'} "
                   f"than last week ({s['waste_pct_last_week']}%).")
            )

        # --- Default ---
        return (
            "I can help you with:\n\n"
            "• **How much food to prepare tomorrow?**\n"
            "• **Why did food waste increase this week?**\n"
            "• **How can I reduce food waste?**\n"
            "• **Which day has the highest food waste?**\n"
            "• **How much food did we save this month?**\n"
            "• **Give me this week's summary.**\n\n"
            "Please ask one of the above or a similar question."
        )

    def _build_context_string(self) -> str:
        """Build a plain-text context summary for LLM prompting."""
        s = self._load_stats()
        lines = [
            f"Organization food waste this week: {s['waste_pct_this_week']}%",
            f"Organization food waste last week: {s['waste_pct_last_week']}%",
            f"Total surplus this week: {round(s['total_surplus_week'])} meals",
            f"Total prepared this week: {round(s['total_prepared_week'])} meals",
            f"Total consumed this week: {round(s['total_consumed_week'])} meals",
            f"Completed donations: {s['completed_donations']}",
        ]
        if s['worst_day']:
            lines.append(
                f"Highest waste day: {s['worst_day'].date} ({s['worst_day'].meal_type}), "
                f"waste%={round(s['worst_day_waste'])}"
            )
        if s['impact']:
            lines.append(f"Total food saved kg: {round(s['impact'].total_food_saved_kg, 1)}")
            lines.append(f"Total meals saved: {s['impact'].meals_saved}")
        return "\n".join(lines)
