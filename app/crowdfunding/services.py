"""Crowdfunding services."""
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy.orm import SessionTransaction

from app.crowdfunding import repository
from app.entities.crowdfunding import (
    ContributionCreate,
    ContributionInDB,
    GoalCreate,
    GoalInDB,
    LeaderboardEntry,
    MonthlyGoalCreate,
    MonthlyGoalInDB,
    MonthlyGoalSummary,
    ProjectCreate,
    ProjectInDB,
    ProjectSummary,
    ProjectUpdate,
    TierCreate,
    TierInDB,
    TierUpdate,
)
from app.infra.custom_decorators import database_uow
from app.infra.database import get_async_session


@database_uow()
async def create_project(
    project: ProjectCreate,
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
) -> ProjectInDB:
    """Create a new crowdfunding project."""
    existing = await repository.get_project_by_slug(
        project.slug,
        transaction=transaction,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Project with this slug already exists',
        )
    _project = await repository.create_project(
        project,
        transaction=transaction,
    )
    return ProjectInDB.model_validate(_project)


@database_uow()
async def get_project(
    project_id: int | None = None,
    slug: str | None = None,
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
) -> ProjectInDB:
    """Get project by ID or slug."""
    if project_id:
        _project = await repository.get_project_by_id(
            project_id,
            transaction=transaction,
        )
    elif slug:
        _project = await repository.get_project_by_slug(
            slug,
            transaction=transaction,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Either project_id or slug must be provided',
        )
    if not _project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Project not found',
        )
    return ProjectInDB.model_validate(_project)


@database_uow()
async def list_projects(
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
    published_only: bool = True,
    active_only: bool = True,
    limit: int | None = None,
    offset: int = 0,
) -> list[ProjectInDB]:
    """List projects."""
    projects = await repository.list_projects(
        transaction=transaction,
        published_only=published_only,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )
    return [ProjectInDB.model_validate(p) for p in projects]


@database_uow()
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
) -> ProjectInDB:
    """Update project."""
    _project = await repository.update_project(
        project_id,
        project_update,
        transaction=transaction,
    )
    if not _project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Project not found',
        )
    return ProjectInDB.model_validate(_project)


@database_uow()
async def create_tier(
    tier: TierCreate,
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
) -> TierInDB:
    """Create a new tier."""
    project = await repository.get_project_by_id(
        tier.project_id,
        transaction=transaction,
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Project not found',
        )
    _tier = await repository.create_tier(
        tier,
        transaction=transaction,
    )
    return TierInDB.model_validate(_tier)


@database_uow()
async def get_tier(
    tier_id: int,
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
) -> TierInDB:
    """Get tier by ID."""
    _tier = await repository.get_tier_by_id(
        tier_id,
        transaction=transaction,
    )
    if not _tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Tier not found',
        )
    return TierInDB.model_validate(_tier)


@database_uow()
async def list_tiers(
    project_id: int,
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
    active_only: bool = True,
) -> list[TierInDB]:
    """List tiers by project."""
    tiers = await repository.list_tiers_by_project(
        project_id,
        transaction=transaction,
        active_only=active_only,
    )
    return [TierInDB.model_validate(t) for t in tiers]


@database_uow()
async def update_tier(
    tier_id: int,
    tier_update: TierUpdate,
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
) -> TierInDB:
    """Update tier."""
    _tier = await repository.update_tier(
        tier_id,
        tier_update,
        transaction=transaction,
    )
    if not _tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Tier not found',
        )
    return TierInDB.model_validate(_tier)


@database_uow()
async def process_contribution(
    contribution: ContributionCreate,
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
) -> ContributionInDB:
    """Process a contribution (checkout)."""
    project = await repository.get_project_by_id(
        contribution.project_id,
        transaction=transaction,
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Project not found',
        )
    if not project.active or not project.published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Project is not active or published',
        )
    if contribution.tier_id:
        tier = await repository.get_tier_by_id(
            contribution.tier_id,
            transaction=transaction,
        )
        if not tier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Tier not found',
            )
        if not tier.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Tier is not active',
            )
        if tier.max_backers and tier.current_backers >= tier.max_backers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Tier is full',
            )
    customer = await bootstrap.cart_uow.get_customer(
        contribution.user_id,
        payment_gateway='STRIPE',
        bootstrap=bootstrap,
    )
    payment_intent = bootstrap.payment.create_payment_intent(
        amount=float(contribution.amount),
        currency='brl',
        customer_id=customer.customer_uuid,
        payment_method=contribution.payment_method_id,
        installments=contribution.installments,
    )
    payment_response = bootstrap.payment.create_credit_card_payment(
        payment_gateway='STRIPE',
        customer_id=customer.customer_uuid,
        amount=contribution.amount,
        card_token=contribution.payment_method_id,
        installments=contribution.installments,
        payment_intent_id=payment_intent['id'],
        payment_method=contribution.payment_method_id,
        customer_email='',
    )
    payment_id = None
    _contribution = await repository.create_contribution(
        contribution,
        payment_id=payment_id,
        transaction=transaction,
    )
    if payment_response.get('status') == 'succeeded':
        await repository.update_contribution_status(
            _contribution.contribution_id,
            'paid',
            payment_id=payment_id,
            transaction=transaction,
        )
        await repository.update_project_amounts(
            contribution.project_id,
            contribution.amount,
            transaction=transaction,
        )
        if contribution.tier_id:
            pass
        await _update_goals_amounts(
            contribution.project_id,
            contribution.amount,
            transaction=transaction,
        )
        now = datetime.now()
        await _update_monthly_goal_amount(
            contribution.project_id,
            contribution.amount,
            now.month,
            now.year,
            transaction=transaction,
        )
    return ContributionInDB.model_validate(_contribution)


async def _update_goals_amounts(
    project_id: int,
    amount: Decimal,
    *,
    transaction: SessionTransaction,
) -> None:
    """Update all goals amounts."""
    goals = await repository.list_goals_by_project(
        project_id,
        transaction=transaction,
    )
    for goal in goals:
        await repository.update_goal_amount(
            goal.goal_id,
            amount,
            transaction=transaction,
        )


async def _update_monthly_goal_amount(
    project_id: int,
    amount: Decimal,
    month: int,
    year: int,
    *,
    transaction: SessionTransaction,
) -> None:
    """Update monthly goal amount."""
    monthly_goal = await repository.get_monthly_goal_by_project_and_date(
        project_id,
        month,
        year,
        transaction=transaction,
    )
    if monthly_goal:
        await repository.update_monthly_goal_amount(
            monthly_goal.monthly_goal_id,
            amount,
            transaction=transaction,
        )


@database_uow()
async def get_leaderboard(
    project_id: int,
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
    limit: int = 100,
) -> list[LeaderboardEntry]:
    """Get leaderboard for a project."""
    leaderboard = await repository.get_leaderboard(
        project_id,
        transaction=transaction,
        limit=limit,
    )
    return [
        LeaderboardEntry(
            user_id=user.user_id,
            user_name=user.name,
            total_contributed=total,
            contributions_count=count,
        )
        for user, total, count in leaderboard
    ]


@database_uow()
async def get_project_summary(
    project_id: int,
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
) -> ProjectSummary:
    """Get project summary with totals."""
    project = await repository.get_project_by_id(
        project_id,
        transaction=transaction,
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Project not found',
        )
    total = await repository.get_total_contributions(
        project_id,
        transaction=transaction,
    )
    progress = (
        (project.current_amount / project.goal_amount * 100)
        if project.goal_amount > 0
        else Decimal('0')
    )
    return ProjectSummary(
        project_id=project.project_id,
        title=project.title,
        current_amount=project.current_amount,
        goal_amount=project.goal_amount,
        backers_count=project.backers_count,
        progress_percentage=progress,
        total_contributions=total,
    )


@database_uow()
async def create_goal(
    goal: GoalCreate,
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
) -> GoalInDB:
    """Create a new goal."""
    project = await repository.get_project_by_id(
        goal.project_id,
        transaction=transaction,
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Project not found',
        )
    _goal = await repository.create_goal(
        goal,
        transaction=transaction,
    )
    return GoalInDB.model_validate(_goal)


@database_uow()
async def list_goals(
    project_id: int,
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
) -> list[GoalInDB]:
    """List goals by project."""
    goals = await repository.list_goals_by_project(
        project_id,
        transaction=transaction,
    )
    return [GoalInDB.model_validate(g) for g in goals]


@database_uow()
async def create_monthly_goal(
    monthly_goal: MonthlyGoalCreate,
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
) -> MonthlyGoalInDB:
    """Create a new monthly goal."""
    project = await repository.get_project_by_id(
        monthly_goal.project_id,
        transaction=transaction,
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Project not found',
        )
    existing = await repository.get_monthly_goal_by_project_and_date(
        monthly_goal.project_id,
        monthly_goal.month,
        monthly_goal.year,
        transaction=transaction,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Monthly goal for this month and year already exists',
        )
    _monthly_goal = await repository.create_monthly_goal(
        monthly_goal,
        transaction=transaction,
    )
    return MonthlyGoalInDB.model_validate(_monthly_goal)


@database_uow()
async def list_monthly_goals(
    project_id: int,
    *,
    transaction: SessionTransaction,
    bootstrap: Any,
) -> list[MonthlyGoalSummary]:
    """List monthly goals by project."""
    monthly_goals = await repository.list_monthly_goals_by_project(
        project_id,
        transaction=transaction,
    )
    result = []
    for mg in monthly_goals:
        total_paid = await repository.get_monthly_total_paid(
            project_id,
            mg.month,
            mg.year,
            transaction=transaction,
        )
        progress = (
            (mg.current_amount / mg.target_amount * 100)
            if mg.target_amount > 0
            else Decimal('0')
        )
        result.append(
            MonthlyGoalSummary(
                monthly_goal_id=mg.monthly_goal_id,
                month=mg.month,
                year=mg.year,
                current_amount=mg.current_amount,
                target_amount=mg.target_amount,
                progress_percentage=progress,
                total_paid_in_month=total_paid,
            ),
        )
    return result
