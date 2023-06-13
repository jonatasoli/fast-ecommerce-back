from sqlalchemy import Boolean, Column, Integer, String

from ext.database import Base


class UploadedImage(Base):
    id = Column(String(512), nullable=False, primary_key=True)
    original = Column(String(512))
    small = Column(String(512))
    thumb = Column(String(512))
    icon = Column(String(512))
    uploaded = Column(Boolean, default=False)

    mimetype = Column(String(48), nullable=True)
    name = Column(String(512), nullable=True)
    size = Column(String(24), nullable=True)
    image_bucket = Column(String(48), nullable=True)

    def to_app_json(self, expand=False):
        return {
            'id': self.id,
            'original': self.original,
            'small': self.small,
            'thumb': self.thumb,
            'icon': self.icon,
            'uploaded': self.uploaded,
        }

    def __init__(self, _id=None):
        self.id = _id
