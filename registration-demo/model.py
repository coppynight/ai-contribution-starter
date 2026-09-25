"""A deliberately small, immutable teaching model for event registration."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Booking:
    booking_id: str
    people: int


@dataclass(frozen=True)
class Event:
    capacity: int = 8
    remaining: int = 8
    bookings: tuple[Booking, ...] = ()


def register(event: Event, booking_id: str, people: int = 1) -> Event:
    if people < 1 or people > event.remaining:
        raise ValueError("The party must fit into the remaining capacity.")
    if any(booking.booking_id == booking_id for booking in event.bookings):
        raise ValueError("Booking IDs must be unique.")
    return replace(
        event,
        remaining=event.remaining - people,
        bookings=event.bookings + (Booking(booking_id, people),),
    )


def cancel_legacy(event: Event, booking_id: str) -> Event:
    """Old assumption: every booking represents one person."""
    if not any(booking.booking_id == booking_id for booking in event.bookings):
        raise ValueError("Unknown booking.")
    return replace(
        event,
        remaining=event.remaining + 1,
        bookings=tuple(b for b in event.bookings if b.booking_id != booking_id),
    )


def cancel_fixed(event: Event, booking_id: str) -> Event:
    """Return the places that this booking actually reserved."""
    booking = next((b for b in event.bookings if b.booking_id == booking_id), None)
    if booking is None:
        raise ValueError("Unknown booking.")
    return replace(
        event,
        remaining=event.remaining + booking.people,
        bookings=tuple(b for b in event.bookings if b.booking_id != booking_id),
    )
