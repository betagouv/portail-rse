from io import BytesIO

from django.http import HttpResponse


def pptx_response(presentation, filename):
    buffer = BytesIO()
    presentation.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
    response["Content-Disposition"] = f"filename={filename}"

    return response
