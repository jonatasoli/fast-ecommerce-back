"""Crowdfunding repository."""
import json
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.orm import SessionTransaction

from app.entities.crowdfunding import (
    ContributionCreate,
    GoalCreate,
    MonthlyGoalCreate,
    ProjectCreate,
    ProjectUpdate,
    TierCreate,
    TierUpdate,
)
from app.infra.models import (
    ContributionDB,
    GoalDB,
    MonthlyGoalDB,
    ProjectDB,
    TierDB,
    UserDB,
)


async def create_project(
    project: ProjectCreate,
    *,
    transaction: SessionTransaction,
) -> ProjectDB:
    """Create a new crowdfunding project."""
    _project = ProjectDB(
        user_id=project.user_id,
        title=project.title,
        slug=project.slug,
        description=project.description,
        short_description=project.short_description,
        story=project.story,
        risks_and_challenges=project.risks_and_challenges,
        main_image=project.main_image,
        video_url=project.video_url,
        category=project.category,
        location=project.location,
        start_date=project.start_date,
        end_date=project.end_date,
        goal_amount=project.goal_amount,
        current_amount=Decimal('0'),
        backers_count=0,
        active=project.active,
        published=project.published,
    )
    transaction.session.add(_project)
    await transaction.session.flush()
    return _project


async def get_project_by_id(
    project_id: int,
    *,
    transaction: SessionTransaction,
) -> ProjectDB | None:
    """Get project by ID."""
    query = select(ProjectDB).where(ProjectDB.project_id == project_id)
    return await transaction.session.scalar(query)


async def get_project_by_slug(
    slug: str,
    *,
    transaction: SessionTransaction,
) -> ProjectDB | None:
    """Get project by slug."""
    query = select(ProjectDB).where(ProjectDB.slug == slug)
    return await transaction.session.scalar(query)


async def list_projects(
    *,
    transaction: SessionTransaction,
    published_only: bool = True,
    active_only: bool = True,
    limit: int | None = None,
    offset: int = 0,
) -> list[ProjectDB]:
    """List projects."""
    query = select(ProjectDB)
    if published_only:
        query = query.where(ProjectDB.published.is_(True))
    if active_only:
        query = query.where(ProjectDB.active.is_(True))
    query = query.order_by(ProjectDB.created_at.desc())
    if limit:
        query = query.limit(limit).offset(offset)
    result = await transaction.session.scalars(query)
    return list(result.unique().all())


async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    *,
    transaction: SessionTransaction,
) -> ProjectDB | None:
    """Update project."""
    update_data = project_update.model_dump(exclude_unset=True)
    if update_data:
        update_data['updated_at'] = datetime.now(UTC)
        stmt = (
            update(ProjectDB)
            .where(ProjectDB.project_id == project_id)
            .values(**update_data)
        )
        await transaction.session.execute(stmt)
        await transaction.session.flush()
    return await get_project_by_id(project_id, transaction=transaction)


async def create_tier(
    tier: TierCreate,
    *,
    transaction: SessionTransaction,
) -> TierDB:
    """Create a new tier."""
    _tier = TierDB(
        project_id=tier.project_id,
        name=tier.name,
        description=tier.description,
        amount=tier.amount,
        is_recurring=tier.is_recurring,
        recurring_interval=tier.recurring_interval,
        max_backers=tier.max_backers,
        estimated_delivery=tier.estimated_delivery,
        rewards=json.dumps(tier.rewards) if tier.rewards else None,
        active=tier.active,
        order=tier.order,
        current_backers=0,
    )
    transaction.session.add(_tier)
    await transaction.session.flush()
    return _tier


async def get_tier_by_id(
    tier_id: int,
    *,
    transaction: SessionTransaction,
) -> TierDB | None:
    """Get tier by ID."""
    query = select(TierDB).where(TierDB.tier_id == tier_id)
    return await transaction.session.scalar(query)


async def list_tiers_by_project(
    project_id: int,
    *,
    transaction: SessionTransaction,
    active_only: bool = True,
) -> list[TierDB]:
    """List tiers by project."""
    query = select(TierDB).where(TierDB.project_id == project_id)
    if active_only:
        query = query.where(TierDB.active.is_(True))
    query = query.order_by(TierDB.order.asc(), TierDB.amount.asc())
    result = await transaction.session.scalars(query)
    return list(result.unique().all())


async def update_tier(
    tier_id: int,
    tier_update: TierUpdate,
    *,
    transaction: SessionTransaction,
) -> TierDB | None:
    """Update tier."""
    update_data = tier_update.model_dump(exclude_unset=True)
    if update_data:
        if 'rewards' in update_data and update_data['rewards'] is not None:
            update_data['rewards'] = json.dumps(update_data['rewards'])
        update_data['updated_at'] = datetime.now(UTC)
        stmt = (
            update(TierDB)
            .where(TierDB.tier_id == tier_id)
            .values(**update_data)
        )
        await transaction.session.execute(stmt)
        await transaction.session.flush()
    return await get_tier_by_id(tier_id, transaction=transaction)


async def update_tier_backers(
    tier_id: int,
    increment: bool = True,
    *,
    transaction: SessionTransaction,
) -> TierDB | None:
    """Update tier backers count."""
    tier = await get_tier_by_id(tier_id, transaction=transaction)
    if not tier:
        return None
    if increment:
        tier.current_backers += 1
    else:
        tier.current_backers = max(0, tier.current_backers - 1)
    tier.updated_at = datetime.now(UTC)
    transaction.session.add(tier)
    await transaction.session.flush()
    return tier


async def create_contribution(
    contribution: ContributionCreate,
    *,
    payment_id: int | None,
    transaction: SessionTransaction,
) -> ContributionDB:
    """Create a new contribution."""
    _contribution = ContributionDB(
        project_id=contribution.project_id,
        tier_id=contribution.tier_id,
        user_id=contribution.user_id,
        amount=contribution.amount,
        is_recurring=contribution.is_recurring,
        payment_id=payment_id,
        status='pending',
        anonymous=contribution.anonymous,
    )
    transaction.session.add(_contribution)
    await transaction.session.flush()
    return _contribution


async def get_contribution_by_id(
    contribution_id: int,
    *,
    transaction: SessionTransaction,
) -> ContributionDB | None:
    """Get contribution by ID."""
    query = select(ContributionDB).where(
        ContributionDB.contribution_id == contribution_id,
    )
    return await transaction.session.scalar(query)


async def list_contributions_by_project(
    project_id: int,
    *,
    transaction: SessionTransaction,
    status: str | None = None,
) -> list[ContributionDB]:
    """List contributions by project."""
    query = select(ContributionDB).where(
        ContributionDB.project_id == project_id,
    )
    if status:
        query = query.where(ContributionDB.status == status)
    query = query.order_by(ContributionDB.created_at.desc())
    result = await transaction.session.scalars(query)
    return list(result.unique().all())


async def update_contribution_status(
    contribution_id: int,
    status: str,
    *,
    payment_id: int | None = None,
    subscription_id: str | None = None,
    transaction: SessionTransaction,
) -> ContributionDB | None:
    """Update contribution status."""
    update_data = {'status': status, 'updated_at': datetime.now(UTC)}
    if payment_id:
        update_data['payment_id'] = payment_id
    if subscription_id:
        update_data['recurring_subscription_id'] = subscription_id
    stmt = (
        update(ContributionDB)
        .where(ContributionDB.contribution_id == contribution_id)
        .values(**update_data)
    )
    await transaction.session.execute(stmt)
    await transaction.session.flush()
    return await get_contribution_by_id(contribution_id, transaction=transaction)


async def update_project_amounts(
    project_id: int,
    amount: Decimal,
    *,
    transaction: SessionTransaction,
) -> None:
    """Update project current amount and backers count."""
    project = await get_project_by_id(project_id, transaction=transaction)
    if not project:
        return
    new_amount = project.current_amount + amount
    new_backers = project.backers_count + 1
    stmt = (
        update(ProjectDB)
        .where(ProjectDB.project_id == project_id)
        .values(
            current_amount=new_amount,
            backers_count=new_backers,
            updated_at=datetime.now(UTC),
        )
    )
    await transaction.session.execute(stmt)
    await transaction.session.flush()


async def create_goal(
    goal: GoalCreate,
    *,
    transaction: SessionTransaction,
) -> GoalDB:
    """Create a new goal."""
    _goal = GoalDB(
        project_id=goal.project_id,
        title=goal.title,
        description=goal.description,
        target_amount=goal.target_amount,
        current_amount=Decimal('0'),
        achieved=False,
        order=goal.order,
    )
    transaction.session.add(_goal)
    await transaction.session.flush()
    return _goal


async def get_goal_by_id(
    goal_id: int,
    *,
    transaction: SessionTransaction,
) -> GoalDB | None:
    """Get goal by ID."""
    query = select(GoalDB).where(GoalDB.goal_id == goal_id)
    return await transaction.session.scalar(query)


async def list_goals_by_project(
    project_id: int,
    *,
    transaction: SessionTransaction,
) -> list[GoalDB]:
    """List goals by project."""
    query = (
        select(GoalDB)
        .where(GoalDB.project_id == project_id)
        .order_by(GoalDB.order.asc())
    )
    result = await transaction.session.scalars(query)
    return list(result.unique().all())


async def update_goal_amount(
    goal_id: int,
    amount: Decimal,
    *,
    transaction: SessionTransaction,
) -> GoalDB | None:
    """Update goal current amount."""
    goal = await get_goal_by_id(goal_id, transaction=transaction)
    if not goal:
        return None
    new_amount = goal.current_amount + amount
    achieved = new_amount >= goal.target_amount
    update_data = {
        'current_amount': new_amount,
        'updated_at': datetime.now(UTC),
    }
    if achieved and not goal.achieved:
        update_data['achieved'] = True
        update_data['achieved_at'] = datetime.now(UTC)
    stmt = (
        update(GoalDB)
        .where(GoalDB.goal_id == goal_id)
        .values(**update_data)
    )
    await transaction.session.execute(stmt)
    await transaction.session.flush()
    return await get_goal_by_id(goal_id, transaction=transaction)


async def create_monthly_goal(
    monthly_goal: MonthlyGoalCreate,
    *,
    transaction: SessionTransaction,
) -> MonthlyGoalDB:
    """Create a new monthly goal."""
    _monthly_goal = MonthlyGoalDB(
        project_id=monthly_goal.project_id,
        month=monthly_goal.month,
        year=monthly_goal.year,
        target_amount=monthly_goal.target_amount,
        current_amount=Decimal('0'),
        achieved=False,
    )
    transaction.session.add(_monthly_goal)
    await transaction.session.flush()
    return _monthly_goal


async def get_monthly_goal_by_id(
    monthly_goal_id: int,
    *,
    transaction: SessionTransaction,
) -> MonthlyGoalDB | None:
    """Get monthly goal by ID."""
    query = select(MonthlyGoalDB).where(
        MonthlyGoalDB.monthly_goal_id == monthly_goal_id,
    )
    return await transaction.session.scalar(query)


async def get_monthly_goal_by_project_and_date(
    project_id: int,
    month: int,
    year: int,
    *,
    transaction: SessionTransaction,
) -> MonthlyGoalDB | None:
    """Get monthly goal by project and date."""
    query = select(MonthlyGoalDB).where(
        MonthlyGoalDB.project_id == project_id,
        MonthlyGoalDB.month == month,
        MonthlyGoalDB.year == year,
    )
    return await transaction.session.scalar(query)


async def list_monthly_goals_by_project(
    project_id: int,
    *,
    transaction: SessionTransaction,
) -> list[MonthlyGoalDB]:
    """List monthly goals by project."""
    query = (
        select(MonthlyGoalDB)
        .where(MonthlyGoalDB.project_id == project_id)
        .order_by(MonthlyGoalDB.year.desc(), MonthlyGoalDB.month.desc())
    )
    result = await transaction.session.scalars(query)
    return list(result.unique().all())


async def update_monthly_goal_amount(
    monthly_goal_id: int,
    amount: Decimal,
    *,
    transaction: SessionTransaction,
) -> MonthlyGoalDB | None:
    """Update monthly goal current amount."""
    monthly_goal = await get_monthly_goal_by_id(
        monthly_goal_id,
        transaction=transaction,
    )
    if not monthly_goal:
        return None
    new_amount = monthly_goal.current_amount + amount
    achieved = new_amount >= monthly_goal.target_amount
    update_data = {
        'current_amount': new_amount,
        'updated_at': datetime.now(UTC),
    }
    if achieved and not monthly_goal.achieved:
        update_data['achieved'] = True
        update_data['achieved_at'] = datetime.now(UTC)
    stmt = (
        update(MonthlyGoalDB)
        .where(MonthlyGoalDB.monthly_goal_id == monthly_goal_id)
        .values(**update_data)
    )
    await transaction.session.execute(stmt)
    await transaction.session.flush()
    return await get_monthly_goal_by_id(
        monthly_goal_id,
        transaction=transaction,
    )


async def get_leaderboard(
    project_id: int,
    *,
    transaction: SessionTransaction,
    limit: int = 100,
) -> list[tuple[UserDB, Decimal, int]]:
    """Get leaderboard for a project."""
    query = (
        select(
            UserDB,
            func.sum(ContributionDB.amount).label('total_contributed'),
            func.count(ContributionDB.contribution_id).label('contributions_count'),
        )
        .join(ContributionDB, UserDB.user_id == ContributionDB.user_id)
        .where(
            ContributionDB.project_id == project_id,
            ContributionDB.status == 'paid',
            ContributionDB.anonymous.is_(False),
        )
        .group_by(UserDB.user_id)
        .order_by(func.sum(ContributionDB.amount).desc())
        .limit(limit)
    )
    result = await transaction.session.execute(query)
    return [
        (row[0], row[1], row[2])
        for row in result.all()
    ]


async def get_total_contributions(
    project_id: int,
    *,
    transaction: SessionTransaction,
) -> Decimal:
    """Get total contributions for a project."""
    query = (
        select(func.sum(ContributionDB.amount))
        .where(
            ContributionDB.project_id == project_id,
            ContributionDB.status == 'paid',
        )
    )
    result = await transaction.session.scalar(query)
    return result or Decimal('0')


async def get_monthly_total_paid(
    project_id: int,
    month: int,
    year: int,
    *,
    transaction: SessionTransaction,
) -> Decimal:
    """Get total paid in a specific month."""
    query = (
        select(func.sum(ContributionDB.amount))
        .where(
            ContributionDB.project_id == project_id,
            ContributionDB.status == 'paid',
            func.extract('month', ContributionDB.created_at) == month,
            func.extract('year', ContributionDB.created_at) == year,
        )
    )
    result = await transaction.session.scalar(query)
    return result or Decimal('0')
