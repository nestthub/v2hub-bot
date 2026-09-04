from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """FSM flows for multi-step administrative actions."""

    waiting_user_id = State()
    """Waiting for an admin to send a Telegram ID to look up."""

    waiting_stats_period = State()
    """Waiting for an admin to type a custom `start : end` date range."""

    # ── Broadcasts ───────────────────────────────────────────────────────────
    # Two authoring modes:
    #  - "copy": the admin sends one message (text/media/etc.) and it is
    #    re-sent to every recipient via Bot.copy_message, byte-for-byte,
    #    keeping whatever native formatting/attachments it already has.
    #  - "compose": the admin sends the content (text and/or media) and then
    #    builds a keyboard on top of it (callback_data and/or URL buttons),
    #    one button at a time.

    choosing_broadcast_mode = State()
    """Waiting for the admin to pick copy vs. compose mode."""

    waiting_broadcast_message = State()
    """Copy mode: waiting for the message to be copied to every recipient."""

    waiting_broadcast_content = State()
    """Compose mode: waiting for the content (text/media) to broadcast."""

    waiting_broadcast_keyboard = State()
    """Compose mode: waiting for the label of the button being added."""

    confirming_broadcast = State()
    """Broadcast content (and optional keyboard) ready; waiting for confirm/cancel."""

    # ── Providers ────────────────────────────────────────────────────────────

    waiting_provider_create_owner_id = State()
    """Waiting for the Telegram ID of the user who will own the new provider."""

    waiting_provider_create_name = State()
    """Waiting for the new provider's name."""

    waiting_provider_create_url = State()
    """Waiting for the new provider's URL (or a skip)."""

    waiting_provider_rename = State()
    """Waiting for a new name for an existing provider."""

    waiting_provider_new_url = State()
    """Waiting for a new URL for an existing provider (or a skip/clear)."""
