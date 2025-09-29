def proconnect(request):
    return {"proconnect": bool(request.session.get("oidc_id_token"))}
