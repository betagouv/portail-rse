import filetype
from django.core.validators import FileExtensionValidator
from django.forms import FileField
from django.forms import ModelForm
from django.forms import ValidationError

from analyseia.models import AnalyseIA

MAX_UPLOAD_SIZE = 50 * 1024 * 1024


def validate_pdf_content(value):
    kind = filetype.guess(value)
    if (not kind) or kind.extension != "pdf":
        raise ValidationError(
            "Le fichier %(value)s n'est pas un pdf.",
            params={"value": value},
        )


def validate_file_size(value):
    if value.size > MAX_UPLOAD_SIZE:
        raise ValidationError(
            "La taille du fichier dépasse la taille maximale autorisée"
        )


class AnalyseIAForm(ModelForm):
    fichier = FileField(
        validators=[
            FileExtensionValidator(["pdf"]),
            validate_pdf_content,
            validate_file_size,
        ],
        help_text="Sélectionnez des documents contenant des <b>données publiques</b> susceptibles de répondre à vos exigences ESG.<br>Taille maximale : <b>50 Mo</b>. Format supporté : <b>PDF</b>. Langue du document : <b>Français</b>.",
    )

    class Meta:
        model = AnalyseIA
        fields = ["fichier"]
        labels = {"fichier": "Ajouter un fichier"}
