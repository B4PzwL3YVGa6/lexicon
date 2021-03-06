from __future__ import absolute_import

import pytest
from lexicon.parser import (
    generate_base_provider_parser,
    generate_cli_main_parser,
)


def test_base_provider_parser():
    baseparser = generate_base_provider_parser()
    parsed = baseparser.parse_args(['list', 'capsulecd.com', 'TXT'])
    assert parsed.action == 'list'
    assert parsed.domain == 'capsulecd.com'
    assert parsed.type == 'TXT'
    assert parsed.ttl == None
    assert parsed.output == 'TABLE'


def test_base_provider_parser_without_domain():
    baseparser = generate_base_provider_parser()
    with pytest.raises(SystemExit):
        baseparser.parse_args(['list'])


def test_base_provider_parser_without_options():
    baseparser = generate_base_provider_parser()
    with pytest.raises(SystemExit):
        baseparser.parse_args([])


def test_cli_main_parser():
    baseparser = generate_cli_main_parser()
    parsed = baseparser.parse_args(
        ['cloudflare', 'list', 'capsulecd.com', 'TXT'])
    assert parsed.provider_name == 'cloudflare'
    assert parsed.action == 'list'
    assert parsed.domain == 'capsulecd.com'
    assert parsed.type == 'TXT'
    assert parsed.output == 'TABLE'


def test_cli_main_parser_without_args():
    baseparser = generate_cli_main_parser()
    with pytest.raises(SystemExit):
        baseparser.parse_args([])
