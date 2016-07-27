import socket
import ipyparallel as ipp

rc = ipp.Client()
ar = rc[:].apply_async(socket.gethostname)
pid_map = ar.get_dict()
print(pid_map)
