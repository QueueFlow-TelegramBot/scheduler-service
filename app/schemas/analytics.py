from pydantic import BaseModel


class QueueEntryStatusCounts(BaseModel):
    waiting: int
    notified: int
    cancelled: int


class AnalyticsResponse(BaseModel):
    total_events_processed: int
    events_by_status: QueueEntryStatusCounts
    total_rooms: int
    rooms_by_status: dict[str, int]
    actions_per_service: dict[str, int]
