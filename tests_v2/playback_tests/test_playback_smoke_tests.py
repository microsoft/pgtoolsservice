from pathlib import Path

import pytest

import tests_v2
from ossdbtoolsservice.hosting.message_recorder import RecordedSession
from tests_v2.test_utils.message_server_client_wrapper import MessageServerClientWrapper
from tests_v2.test_utils.playback.playback import Playback
from tests_v2.test_utils.playback.playback_config import PlaybackConfiguration
from tests_v2.test_utils.playback.playback_db import PlaybackDB


def test_pagila_smoke_test(
    server_client_wrapper: MessageServerClientWrapper, pagila_playback_db: PlaybackDB
) -> None:
    recording = (
        Path(tests_v2.__file__).parent / "test_data" / "recordings" / "pagila-smoke-test.json"
    )
    with open(recording) as f:
        recorded_session: RecordedSession = RecordedSession.model_validate_json(f.read())

    config = PlaybackConfiguration.default()
    config.timeout = 3
    # Ignore completions notification and responses
    config.ignore_server_notification_methods.extend(["textDocument/intelliSenseReady"])
    playback = Playback(server_client_wrapper, config)

    playback.run(recorded_session)


@pytest.mark.playback
def test_user_transaction_smoke_test(
    server_client_wrapper: MessageServerClientWrapper, pagila_playback_db: PlaybackDB
) -> None:
    recording = (
        Path(tests_v2.__file__).parent / "test_data" / "recordings" / "test-user-tx.json"
    )
    with open(recording) as f:
        recorded_session: RecordedSession = RecordedSession.model_validate_json(f.read())

    config = PlaybackConfiguration.default()
    config.timeout = 3
    # Ignore completions notification and responses
    config.ignore_server_notification_methods.extend(
        ["textDocument/intelliSenseReady", "textDocument/statusChanged"]
    )
    config.ignore_responses.extend(["textDocument/completion", "textDocument/definition"])

    playback = Playback(server_client_wrapper, config)

    playback.run(recorded_session)
