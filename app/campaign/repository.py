from datetime import UTC, datetime
from sqlalchemy import select
from app.infra.models import CampaignDB


def get_campaign(
    *,
    transaction,
    free_shipping: bool = False,
):
    """Get campaign."""
    today = datetime.now(tz=UTC)
    query = (select(CampaignDB)
        .where(CampaignDB.start_date >= today)
        .where(CampaignDB.end_date <= today)
        .where(CampaignDB.active.is_(True))
     )
    if free_shipping:
        query = query.where(CampaignDB.free_shipping.is_(True))
    return transaction.scalar(query)
