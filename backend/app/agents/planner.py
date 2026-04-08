"""Planner - Decides council mode and flow based on perception."""

import logging
from ..models.council import PerceptionResult, FlowPlan
from ..models.memory import UserProfile

logger = logging.getLogger(__name__)

# Rule-based mode mapping
TASK_MODE_MAP = {
    "chat": ("light_chat", 1, False),
    "emotional_sorting": ("light_chat", 2, False),
    "decision": ("full_council", 2, True),
    "creative_debate": ("full_council", 2, True),
    "worldview_interaction": ("light_chat", 2, False),
}


class Planner:
    """Plans council flow based on perception results."""

    def plan(
        self,
        perception: PerceptionResult,
        user_profile: UserProfile | None = None,
    ) -> FlowPlan:
        """Create flow plan from perception result."""
        task_type = perception.task_type

        # Check for safety mode
        if perception.risk_flags:
            logger.info("Risk flags detected, switching to safety_mode")
            return FlowPlan(
                mode="safety_mode",
                rounds=0,
                need_knife=False,
                output_views=["practical"],
            )

        # Get base plan from task type
        mode, rounds, need_knife = TASK_MODE_MAP.get(
            task_type, ("light_chat", 1, False)
        )

        # Override with perception suggestions if valid
        if perception.suggested_mode in (
            "light_chat",
            "full_council",
            "eternal_council",
        ):
            mode = perception.suggested_mode
            if mode == "light_chat":
                need_knife = False
            elif mode == "full_council":
                need_knife = True

        # Adjust rounds based on suggested depth
        if perception.suggested_depth > rounds:
            rounds = min(perception.suggested_depth, 3)

        # User profile influence
        if user_profile:
            style = user_profile.preferred_output_style or "dramatic"
            output_views = [style, "practical"]
            if "psychological" not in output_views:
                output_views.append("psychological")
        else:
            output_views = ["dramatic", "practical"]

        return FlowPlan(
            mode=mode,
            rounds=rounds,
            need_knife=need_knife,
            output_views=output_views,
        )
