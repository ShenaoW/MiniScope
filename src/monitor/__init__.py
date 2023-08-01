import threading

from .mitm import MitmProxy
from .objection import Objection


def run_mitm():
    MitmProxy()


def run_objection():
    objection_server = Objection()
    objection_server.request_api("androidSslPinningDisable")
    objection_server.request_api("androidRootDetectionDisable")


def run_mitm_objection(server=None):
    if server == 'mitm' or server is None:
        mitm_thread = threading.Thread(target=run_mitm)
        mitm_thread.start()
    if server == 'objection' or server is None:
        objection_thread = threading.Thread(target=run_objection)
        objection_thread.start()

