from sqlalchemy.orm import Session

from app.models import WatchlistItem


class WatchlistService:
    def list_symbols(self, db: Session, user_id: int) -> list[str]:
        items = (
            db.query(WatchlistItem)
            .filter(WatchlistItem.user_id == user_id)
            .order_by(WatchlistItem.symbol.asc())
            .all()
        )
        return [item.symbol for item in items]

    def add_symbol(self, db: Session, user_id: int, symbol: str) -> bool:
        symbol = symbol.upper()
        existing = (
            db.query(WatchlistItem)
            .filter(WatchlistItem.user_id == user_id, WatchlistItem.symbol == symbol)
            .first()
        )
        if existing:
            return False
        db.add(WatchlistItem(user_id=user_id, symbol=symbol))
        db.commit()
        return True

    def remove_symbol(self, db: Session, user_id: int, symbol: str) -> bool:
        symbol = symbol.upper()
        item = (
            db.query(WatchlistItem)
            .filter(WatchlistItem.user_id == user_id, WatchlistItem.symbol == symbol)
            .first()
        )
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True

