from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy import and_, or_, update, delete, select
from config import load_config

config = load_config()

engine = create_async_engine(config.database_url, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String)
    pace: Mapped[str] = mapped_column(String)
    time: Mapped[str] = mapped_column(String)

class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_user: Mapped[int] = mapped_column(ForeignKey("users.id"))
    to_user: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String)  # "like" или "dislike"

async def get_matches_for(user_id: int):
    async with async_session_maker() as session:
        # Получаем текущего пользователя
        user = await session.get(User, user_id)
        if not user:
            return []

        # Ищем пользователей с такими же параметрами, но без уже поставленного лайка/дизлайка
        stmt = select(User).where(
            and_(
                User.city == user.city,
                User.location == user.location,
                User.time == user.time,
                User.id != user.id,
                ~User.id.in_(
                    select(Like.to_user).where(Like.from_user == user.id)
                )
            )
        )
        result = await session.execute(stmt)
        return result.scalars().all()


async def save_like(from_user: int, to_user: int, status: str):
    async with async_session_maker() as session:
        like = Like(from_user=from_user, to_user=to_user, status=status)
        session.add(like)
        await session.commit()


async def check_mutual_like(user1: int, user2: int):
    async with async_session_maker() as session:
        stmt = select(Like).where(
            and_(
                Like.from_user == user2,
                Like.to_user == user1,
                Like.status == "like"
            )
        )
        result = await session.execute(stmt)
        return result.scalar() is not None
