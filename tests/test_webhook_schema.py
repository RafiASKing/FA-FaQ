from app.schemas.webhook_schema import WhatsAppWebhookPayload


def test_get_message_body_prefers_caption_over_body():
    payload = WhatsAppWebhookPayload(
        event="onmessage",
        data={
            "body": "/9j/" + ("A" * 500),
            "caption": "ini caption pertanyaan",
            "type": "image",
            "mimetype": "image/jpeg",
        },
    )

    assert payload.get_message_body() == "ini caption pertanyaan"


def test_has_image_payload_true_for_image_type():
    payload = WhatsAppWebhookPayload(
        event="onmessage",
        data={
            "type": "image",
            "body": "short",
        },
    )

    assert payload.has_image_payload() is True


def test_has_image_payload_false_for_chat_text():
    payload = WhatsAppWebhookPayload(
        event="onmessage",
        data={
            "type": "chat",
            "body": "@faq kenapa request discharge ED gagal?",
        },
    )

    assert payload.has_image_payload() is False
