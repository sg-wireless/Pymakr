import json
from Plugins.PycomDevice.monitor_pc import MonitorPC

def filter_by_type(data, filter_by):
    # encode is done here because somehow the & operator over two frozensets converts
    # bytes to unicode without being asked
    return [i[0].encode('utf-8') for i in data if i[1] == filter_by]

def filter_by_type_order_by_depth(data, filter_by, reverse=False):
    # encode is done here because somehow the & operator over two frozensets converts
    # bytes to unicode without being asked
    # yeah... I know...
    return [j[0] for j in
            sorted([(i[0].encode('utf-8'), i[2]) for i in
                    data if i[1] == filter_by], key=lambda tup: tup[1], reverse=reverse)]


class Sync(object):
    def __init__(self, local, pyb):
        self.local = frozenset(local)
        self.__original_local = local
        self.monitor = MonitorPC(pyb)

    def to_create_update(self):
        return list(self.local - self.remote)

    def to_delete(self):
        return list(self.remote - self.local)

    def upload_file(self, local_name, remote_name=None):
        with open(local_name, 'r') as content_file:
            content = content_file.read()

        if remote_name is None:
            remote_name = b'/flash/' + local_name
        self.monitor.write_file(remote_name, content)

    def do_sync(self):
        # delete unused files
        map(self.monitor.remove_file, filter_by_type(self.to_delete(), b'f'))

        # then delete unused directories
        map(self.monitor.remove_dir, filter_by_type_order_by_depth(self.to_delete(), b'd', True))

        # now create new directories
        map(self.monitor.create_dir, filter_by_type_order_by_depth(self.to_create_update(), b'd', False))

        # upload the new files and the ones that changed
        map(self.upload_file, filter_by_type(self.to_create_update(), b'f'))

    def sync_pyboard(self):
        remote = self.monitor.read_file(b"/flash/project.pymakr")
        if remote is None:
            remote = []
        else:
            try:
                remote = json.loads(remote)
            except ValueError:
                remote = []

        for i, element in enumerate(remote):
            remote[i] = tuple(element)

        self.remote = frozenset(remote)
        self.do_sync()
        self.monitor.write_file(b"/flash/project.pymakr", json.dumps(list(self.local)))

    def finish_sync(self):
        self.monitor.exit_monitor()