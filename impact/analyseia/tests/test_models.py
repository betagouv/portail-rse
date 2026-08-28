from analyseia.models import AnalyseIA


def test_liee_a_une_entreprise(entreprise_factory):
    entreprise = entreprise_factory()

    document = AnalyseIA.objects.create()
    entreprise.analyses_ia.add(document)

    assert document.est_liee_a_une_entreprise


def test_liee_a_une_csrd(csrd):
    document = AnalyseIA.objects.create()

    document.rapports_csrd.add(csrd)

    assert not document.est_liee_a_une_entreprise
