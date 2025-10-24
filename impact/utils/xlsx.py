from tempfile import NamedTemporaryFile

from django.http import HttpResponse


def xlsx_response(workbook, filename):
    with NamedTemporaryFile() as tmp:
        workbook.save(tmp.name)
        tmp.seek(0)
        xlsx_stream = tmp.read()

    response = HttpResponse(
        xlsx_stream,
        content_type="application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f"filename={filename}"

    return response
