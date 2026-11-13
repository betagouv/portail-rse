import threading
import time

from api import egapro
from poc_lee.apis_figees import apis_externes_figees


def test_restaure_les_api_apres_des_appels_concurrents():
    original = egapro.is_index_egapro_published
    a_dedans = threading.Event()
    b_lance = threading.Event()

    def premier_appel():
        with apis_externes_figees():
            a_dedans.set()
            b_lance.wait(1)
            time.sleep(0.05)

    def second_appel():
        a_dedans.wait(1)
        b_lance.set()
        with apis_externes_figees():
            time.sleep(0.1)

    fils = [
        threading.Thread(target=premier_appel),
        threading.Thread(target=second_appel),
    ]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()

    assert egapro.is_index_egapro_published is original
