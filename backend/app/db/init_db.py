from app.db.base import Base
from app.db.session import engine

# import model để SQLAlchemy nhận metadata
from app.models.document import Document  # noqa: F401


def init_db():
    Base.metadata.create_all(bind=engine)