"""Crowdfunding entities."""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    """Base project model."""

    title: str
    slug: str
    description: dict | None = None
    short_description: str | None = None
    story: dict | None = None
    risks_and_challenges: dict | None = None
    main_image: str | None = None
    video_url: str | None = None
    category: str | None = None
    location: str | None = None
    start_date: datetime
    end_date: datetime
    goal_amount: Decimal
    active: bool = True
    published: bool = False


class ProjectCreate(ProjectBase):
    """Create project model."""

    user_id: int | None = None


class ProjectUpdate(BaseModel):
    """Update project model."""

    title: str | None = None
    description: dict | None = None
    short_description: str | None = None
    story: dict | None = None
    risks_and_challenges: dict | None = None
    main_image: str | None = None
    video_url: str | None = None
    category: str | None = None
    location: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    goal_amount: Decimal | None = None
    active: bool | None = None
    published: bool | None = None


class ProjectInDB(ProjectBase):
    """Project in database model."""

    project_id: int
    user_id: int
    current_amount: Decimal
    backers_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TierBase(BaseModel):
    """Base tier model."""

    name: str
    description: str | None = None
    amount: Decimal
    is_recurring: bool = False
    recurring_interval: str | None = None
    max_backers: int | None = None
    estimated_delivery: date | None = None
    active: bool = True
    order: int = 0


class TierCreate(TierBase):
    """Create tier model."""

    project_id: int


class TierUpdate(BaseModel):
    """Update tier model."""

    name: str | None = None
    description: str | None = None
    amount: Decimal | None = None
    is_recurring: bool | None = None
    recurring_interval: str | None = None
    max_backers: int | None = None
    estimated_delivery: date | None = None
    active: bool | None = None
    order: int | None = None


class TierInDB(TierBase):
    """Tier in database model."""

    tier_id: int
    project_id: int
    current_backers: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContributionBase(BaseModel):
    """Base contribution model."""

    amount: Decimal
    is_recurring: bool = False
    anonymous: bool = False


class ContributionCreate(ContributionBase):
    """Create contribution model."""

    project_id: int
    tier_id: int | None = None
    user_id: int | None = None
    payment_method_id: str
    payment_gateway: str = 'STRIPE'
    installments: int = 1


class ContributionInDB(ContributionBase):
    """Contribution in database model."""

    contribution_id: int
    project_id: int
    tier_id: int | None
    user_id: int
    recurring_subscription_id: str | None
    payment_id: int | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GoalBase(BaseModel):
    """Base goal model."""

    title: str
    description: str | None = None
    target_amount: Decimal
    order: int = 0


class GoalCreate(GoalBase):
    """Create goal model."""

    project_id: int


class GoalUpdate(BaseModel):
    """Update goal model."""

    title: str | None = None
    description: str | None = None
    target_amount: Decimal | None = None
    order: int | None = None


class GoalInDB(GoalBase):
    """Goal in database model."""

    goal_id: int
    project_id: int
    current_amount: Decimal
    achieved: bool
    achieved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MonthlyGoalBase(BaseModel):
    """Base monthly goal model."""

    month: int
    year: int
    target_amount: Decimal


class MonthlyGoalCreate(MonthlyGoalBase):
    """Create monthly goal model."""

    project_id: int


class MonthlyGoalUpdate(BaseModel):
    """Update monthly goal model."""

    month: int | None = None
    year: int | None = None
    target_amount: Decimal | None = None


class MonthlyGoalInDB(MonthlyGoalBase):
    """Monthly goal in database model."""

    monthly_goal_id: int
    project_id: int
    current_amount: Decimal
    achieved: bool
    achieved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeaderboardEntry(BaseModel):
    """Leaderboard entry model."""

    user_id: int
    user_name: str
    total_contributed: Decimal
    contributions_count: int
    anonymous: bool = False


class ProjectSummary(BaseModel):
    """Project summary with totals."""

    project_id: int
    title: str
    current_amount: Decimal
    goal_amount: Decimal
    backers_count: int
    progress_percentage: Decimal
    total_contributions: Decimal


class MonthlyGoalSummary(BaseModel):
    """Monthly goal summary."""

    monthly_goal_id: int
    month: int
    year: int
    current_amount: Decimal
    target_amount: Decimal
    progress_percentage: Decimal
    total_paid_in_month: Decimal
