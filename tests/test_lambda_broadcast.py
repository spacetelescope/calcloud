from . import conftest


def test_broadcast_handler(s3_client):
    from calcloud import io
    from broadcast import broadcast_handler

    comm = io.get_io_bundle()

    ipsts = ["ipppsso11", "ipppsso22", "ipppsso33"]
    msg_type = "cancel"
    broadcasted_msg = [f"{msg_type}-{ipst}" for ipst in ipsts]
    msg = comm.messages.broadcast(msg_type, ipsts)

    event = conftest.get_message_event(msg)
    context = {}

    # do a normal broadcast and assert that the messages put by the braodcast handler matches the expected broadcasted message
    broadcast_handler.lambda_handler(event, context)
    assert sorted(comm.messages.listl()) == sorted(broadcasted_msg)

    # test check_for_kill(), this should prevent broadcasted messages from being put
    comm.clean()
    comm.messages.put("broadcast-kill")
    broadcast_handler.lambda_handler(event, context)
    current_messages = comm.messages.listl()

    for message in broadcasted_msg:
        assert message not in current_messages
