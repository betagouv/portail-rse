from django.shortcuts import render


def handler400(request, exception):
    return render(
        request,
        "400.html",
        {
            "message": str(exception),
        },
        status=400,
    )
