import os
import csv
import array
import gzip
import urllib

from bisect import bisect_left
from contextlib import closing
from cStringIO import StringIO

from .utils import CommentedFile


def binary_search(a, x, lo=0, hi=None):
    hi = hi if hi is not None else len(a)
    pos = bisect_left(a, x, lo, hi)
    return (pos - 1 if pos != hi and a[pos] >= x else -1)


class Software77GeoDatabase(object):
    """The provided ``storage`` must be a persistent mapping object."""

    _test_path = os.path.join(
        os.path.dirname(__file__), 'static', 'ip2country.csv.gz'
        )

    _storage = None

    def __init__(self, storage):
        object.__setattr__(self, '_storage', storage)

        storage.setdefault('ip_index', ())
        storage.setdefault('country_index', ())

        # This attribute is accessible from the outside. When the database
        # is updated, it contains a sorted list of (country code, country
        # name) values.
        storage.setdefault('countries', ())

    def __setattr__(self, name, value):
        self._storage[name] = value

    def __getattr__(self, name):
        try:
            return self._storage[name]
        except KeyError:
            raise AttributeError(name)

    def update(self, url=None):
        if url:
            with closing(urllib.urlopen(url)) as response:
                resource = StringIO(response.read())
        else:
            resource = open(self._test_path, 'rb')

        database = []
        with gzip.GzipFile(fileobj=resource) as stream:
            stream = CommentedFile(stream)

            for row in csv.reader(stream, delimiter=',', quotechar='"'):
                if len(row) >= 6:
                    database.append(row)

        database.sort(key=lambda x: float(x[0]))

        # Update IP index
        index = self.ip_index = array.array('L', (
            int(data[0]) for data in database))

        # Update country database
        countries = self.countries = list(sorted(set(
            ((data[5].strip(), data[6].decode('utf-8'))
             for data in database)),
            key=lambda (code, name): name))

        # Update country index
        self.country_index = array.array('B', (
            countries.index(
                (data[5].strip(), data[6].decode('utf-8'))
                ) for data in database))

        return len(index)

    def lookup(self, ip):
        # Formats the IP, without port, to a list
        ip = ip.split(':', 1)[0]
        ip_list = map(int, ip.split('.'))

        # Validates the address for conversion to long format
        if len(ip_list) != 4:
            raise ValueError('Invalid IP address "%s"' % ip)

        # Converts the IP to long IP format
        long_ip = ip_list[3] + (ip_list[2] << 8) + \
                  (ip_list[1] << 16) + \
                  (ip_list[0] << 24)

        pos = binary_search(self.ip_index, long_ip)
        if pos > 0:
            i = self.country_index[pos]
            return self.countries[i]
