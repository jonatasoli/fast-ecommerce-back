from taskiq_faststream import StreamScheduler
from loguru import logger
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_faststream import BrokerWrapper
from faststream.rabbit import RabbitBroker
from app.cart import services as cart
from app.payment import services as payment
from app.order import services as order
from config import settings
from app.infra.database import get_async_session

DEFAULT_TTL = 172800

broker = RabbitBroker(f'{settings.BROKER_URL}')

taskiq_broker = BrokerWrapper(broker)
taskiq_broker.task(
    queue='in-queue',
    schedule=[
        {
            'cron': '0 */2 * * *',
        },
    ],
)

taskiq_broker.task(
    queue='in-queue',
    schedule=[
        {
            'cron': '0 9 1 * *',  # 9 AM on 1st day of each month
        },
    ],
)

scheduler = StreamScheduler(
    broker=taskiq_broker,
    sources=[LabelScheduleSource(taskiq_broker)],
)



@broker.subscriber('in-queue')
@broker.publisher('out-queue')
async def update_pending_payments() -> str:
    """Task to get all pending payments and update."""
    logger.info('Start payment task')
    await payment.update_pending_payments()
    logger.info('Finish payment task')
    return 'Task: registered'


@broker.subscriber('in-queue')
@broker.publisher('out-queue')
async def update_pending_orders() -> str:
    """Task to get all pending payments and update."""
    logger.info('Start order task')
    await order.update_pending_orders()
    logger.info('Finish order task')
    return 'Task: registered'


@broker.subscriber('in-queue')
@broker.publisher('out-queue')
async def send_monthly_leaderboard_emails() -> str:
    """Task to send monthly leaderboard emails to all backers."""
    from app.crowdfunding import services as crowdfunding
    from app.crowdfunding import repository as crowdfunding_repo
    from app.user import repository as user_repo
    from app.mail.services import send_mail
    from app.entities.mail import MailMessage
    from app.infra.models import ProjectDB
    from sqlalchemy import select

    logger.info('Start monthly leaderboard email task')
    try:
        async with get_async_session() as session:
            async with session.begin() as transaction:
                query = select(ProjectDB).where(
                    ProjectDB.published.is_(True),
                    ProjectDB.active.is_(True),
                )
                result = await transaction.session.scalars(query)
                projects = list(result.unique().all())

                for project in projects:
                    from app.crowdfunding.repository import get_leaderboard as repo_get_leaderboard
                    leaderboard_data = await repo_get_leaderboard(
                        project.project_id,
                        transaction=transaction,
                        limit=10,
                    )

                    leaderboard = []
                    for user, total, count in leaderboard_data:
                        from app.entities.crowdfunding import LeaderboardEntry
                        leaderboard.append(LeaderboardEntry(
                            user_id=user.user_id,
                            user_name=user.name,
                            total_contributed=total,
                            contributions_count=count,
                            anonymous=False,
                        ))

                    if not leaderboard:
                        continue

                    contributions = await crowdfunding_repo.list_contributions_by_project(
                        project.project_id,
                        transaction=transaction,
                        status='paid',
                    )

                    user_ids = list(set(c.user_id for c in contributions))

                    for user_id in user_ids:
                        user = await user_repo.get_user_by_id(
                            user_id,
                            transaction=transaction,
                        )
                        if not user:
                            continue

                        leaderboard_html = '<ol>'
                        for i, entry in enumerate(leaderboard[:10], 1):
                            leaderboard_html += f'''
                            <li>
                                {entry.user_name}: R$ {entry.total_contributed:.2f} 
                                ({entry.contributions_count} contribuições)
                            </li>
                            '''
                        leaderboard_html += '</ol>'

                        message = MailMessage(
                            from_email='noreply@example.com',
                            to_emails=user.email,
                            subject=f'Leaderboard Mensal - {project.title}',
                            plain_text_content=f'Olá {user.name}, Confira o leaderboard do mês para o projeto "{project.title}". Continue apoiando!',
                            html_content=f'''
                            <html>
                            <body>
                                <p>Olá {user.name},</p>
                                <p>Confira o leaderboard do mês para o projeto "{project.title}":</p>
                                {leaderboard_html}
                                <p>Continue apoiando!</p>
                            </body>
                            </html>
                            ''',
                        )

                        send_mail(message)

        logger.info('Finish monthly leaderboard email task')
        return 'Task: completed'
    except Exception as e:
        logger.error(f'Error in monthly leaderboard email task: {e}')
        return f'Task: error - {e!s}'
