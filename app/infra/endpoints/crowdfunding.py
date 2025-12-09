"""Crowdfunding endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer

from app.crowdfunding import services
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
from app.infra.bootstrap.cart_bootstrap import Command, bootstrap
from app.infra.database import get_async_session

crowdfunding = APIRouter(
    prefix='/crowdfunding',
    tags=['crowdfunding'],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


async def get_bootstrap() -> Command:
    """Get bootstrap."""
    return await bootstrap()


@crowdfunding.post(
    '/projects',
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project: ProjectCreate,
    *,
    token: Annotated[str, Depends(oauth2_scheme)],
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
) -> ProjectInDB:
    """Create a new crowdfunding project."""
    user = bootstrap.user.get_user(token)
    project.user_id = user.user_id
    return await services.create_project(
        project,
        bootstrap=bootstrap,
    )


@crowdfunding.get(
    '/projects/{project_id}',
    status_code=status.HTTP_200_OK,
)
async def get_project(
    project_id: int,
    *,
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
) -> ProjectInDB:
    """Get project by ID."""
    return await services.get_project(
        project_id=project_id,
        bootstrap=bootstrap,
    )


@crowdfunding.get(
    '/projects/slug/{slug}',
    status_code=status.HTTP_200_OK,
)
async def get_project_by_slug(
    slug: str,
    *,
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
) -> ProjectInDB:
    """Get project by slug."""
    return await services.get_project(
        slug=slug,
        bootstrap=bootstrap,
    )


@crowdfunding.get(
    '/projects',
    status_code=status.HTTP_200_OK,
)
async def list_projects(
    *,
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
    published_only: bool = True,
    active_only: bool = True,
    limit: int | None = None,
    offset: int = 0,
) -> list[ProjectInDB]:
    """List projects."""
    return await services.list_projects(
        bootstrap=bootstrap,
        published_only=published_only,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )


@crowdfunding.patch(
    '/projects/{project_id}',
    status_code=status.HTTP_200_OK,
)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    *,
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
) -> ProjectInDB:
    """Update project."""
    return await services.update_project(
        project_id,
        project_update,
        bootstrap=bootstrap,
    )


@crowdfunding.post(
    '/tiers',
    status_code=status.HTTP_201_CREATED,
)
async def create_tier(
    tier: TierCreate,
    *,
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
) -> TierInDB:
    """Create a new tier."""
    return await services.create_tier(
        tier,
        bootstrap=bootstrap,
    )


@crowdfunding.get(
    '/tiers/{tier_id}',
    status_code=status.HTTP_200_OK,
)
async def get_tier(
    tier_id: int,
    *,
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
) -> TierInDB:
    """Get tier by ID."""
    return await services.get_tier(
        tier_id,
        bootstrap=bootstrap,
    )


@crowdfunding.get(
    '/projects/{project_id}/tiers',
    status_code=status.HTTP_200_OK,
)
async def list_tiers(
    project_id: int,
    *,
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
    active_only: bool = True,
) -> list[TierInDB]:
    """List tiers by project."""
    return await services.list_tiers(
        project_id,
        bootstrap=bootstrap,
        active_only=active_only,
    )


@crowdfunding.patch(
    '/tiers/{tier_id}',
    status_code=status.HTTP_200_OK,
)
async def update_tier(
    tier_id: int,
    tier_update: TierUpdate,
    *,
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
) -> TierInDB:
    """Update tier."""
    return await services.update_tier(
        tier_id,
        tier_update,
        bootstrap=bootstrap,
    )


@crowdfunding.post(
    '/contributions',
    status_code=status.HTTP_201_CREATED,
)
async def create_contribution(
    contribution: ContributionCreate,
    *,
    token: Annotated[str, Depends(oauth2_scheme)],
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
) -> ContributionInDB:
    """Create a contribution (checkout)."""
    user = bootstrap.user.get_user(token)
    contribution.user_id = user.user_id
    return await services.process_contribution(
        contribution,
        bootstrap=bootstrap,
    )


@crowdfunding.get(
    '/projects/{project_id}/leaderboard',
    status_code=status.HTTP_200_OK,
)
async def get_leaderboard(
    project_id: int,
    *,
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
    limit: int = 100,
) -> list[LeaderboardEntry]:
    """Get leaderboard for a project."""
    return await services.get_leaderboard(
        project_id,
        bootstrap=bootstrap,
        limit=limit,
    )


@crowdfunding.get(
    '/projects/{project_id}/summary',
    status_code=status.HTTP_200_OK,
)
async def get_project_summary(
    project_id: int,
    *,
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
) -> ProjectSummary:
    """Get project summary with total contributions."""
    return await services.get_project_summary(
        project_id,
        bootstrap=bootstrap,
    )


@crowdfunding.post(
    '/goals',
    status_code=status.HTTP_201_CREATED,
)
async def create_goal(
    goal: GoalCreate,
    *,
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
) -> GoalInDB:
    """Create a new goal."""
    return await services.create_goal(
        goal,
        bootstrap=bootstrap,
    )


@crowdfunding.get(
    '/projects/{project_id}/goals',
    status_code=status.HTTP_200_OK,
)
async def list_goals(
    project_id: int,
    *,
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
) -> list[GoalInDB]:
    """List goals by project."""
    return await services.list_goals(
        project_id,
        bootstrap=bootstrap,
    )


@crowdfunding.post(
    '/monthly-goals',
    status_code=status.HTTP_201_CREATED,
)
async def create_monthly_goal(
    monthly_goal: MonthlyGoalCreate,
    *,
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
) -> MonthlyGoalInDB:
    """Create a new monthly goal."""
    return await services.create_monthly_goal(
        monthly_goal,
        bootstrap=bootstrap,
    )


@crowdfunding.get(
    '/projects/{project_id}/monthly-goals',
    status_code=status.HTTP_200_OK,
)
async def list_monthly_goals(
    project_id: int,
    *,
    bootstrap: Annotated[Command, Depends(get_bootstrap)],
) -> list[MonthlyGoalSummary]:
    """List monthly goals by project."""
    return await services.list_monthly_goals(
        project_id,
        bootstrap=bootstrap,
    )
