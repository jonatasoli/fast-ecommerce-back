from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.infra.models.base import Base


class UploadedImage(Base):
    __tablename__ = 'uploaded_image'

    uploaded_image_id: Mapped[int] = mapped_column(primary_key=True)
    original: Mapped[str]
    small: Mapped[str]
    thumb: Mapped[str]
    icon: Mapped[str]
    uploaded: Mapped[bool] = mapped_column(default=False)
    mimetype: Mapped[str] = mapped_column(nullable=True)
    name: Mapped[str] = mapped_column(nullable=True)
    size: Mapped[int] = mapped_column(nullable=True)
    image_bucket: Mapped[str] = mapped_column(nullable=True)
