from io import BytesIO

from django.http import HttpResponse
from pptx.oxml.ns import qn


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


def find_shape(shapes, name):
    for shape in shapes:
        if shape.name == name:
            return shape
        if shape.shape_type == 6:  # GROUPE
            result = find_shape(shape.shapes, name)
            if result:
                return result


def remove_shape(shape):
    shape._element.getparent().remove(shape._element)


def remove_slide(presentation, slide_index):
    """supprime la diapo et sa référence pour être plus portable"""
    xml_slides = presentation.slides._sldIdLst
    slide_elem = xml_slides[slide_index]
    rId = slide_elem.get(qn("r:id"))
    presentation.part.drop_rel(rId)
    xml_slides.remove(slide_elem)
