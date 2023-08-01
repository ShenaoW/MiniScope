from .context import pgc

from pgc.utils.algorithm import string

from nose2.tools import params


@params(
    (['abc', 'bcf']),
    (['abc', 'bc1sasd']),
    (['abc', 'bcasa']),
    (['abcbc', 'bcasd']),
)
def test_lcs(args):
    assert string.lcs(args[0], args[1]) == 'bc'

@params(
    ('gdb://localhost:1234'),
    ('rap://localhost:8078'),
    ('666://localhost:9999'),
    ('11.45.1.4')
)
def test_is_http_url(s):
    assert string.is_http_url(s) == False

@params(
    (['sundays', 'saturday']),
    (['aaaa', ''])
)

def test_levenshtein_distance(args):
    assert string.levenshtein_distance(args[0], args[1]) == 4