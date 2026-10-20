from tempfile import NamedTemporaryFile

from django.http import HttpResponse

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def xlsx_bytes(workbook):
    with NamedTemporaryFile() as tmp:
        workbook.save(tmp.name)
        tmp.seek(0)
        return tmp.read()


def xlsx_response(workbook, filename):
    response = HttpResponse(
        xlsx_bytes(workbook),
        content_type="application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f"filename={filename}"

    return response
