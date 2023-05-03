import demistomock as demisto  # noqa: F401
import pytest
import unittest
from RankServiceOwners import score, main, rank, _canonicalize, aggregate
from contextlib import nullcontext as does_not_raise


@pytest.mark.parametrize('owners,k,expected_out,expected_raises', [
    # different names
    (
        [
            {
                'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1',
                'timestamp': '', 'rankingscore': 1, 'justification': 'source1'
            },
        ],
        1,
        [
            {
                'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1',
                'timestamp': '', 'rankingscore': 1, 'justification': 'source1'
            },
        ],
        does_not_raise(),
    ),
    (
        [
            {
                'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1',
                'timestamp': '', 'rankingscore': 1, 'justification': 'source1'
            },
        ],
        0,
        None,
        pytest.raises(ValueError),
    ),
    (
        [
            {
                'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1',
                'timestamp': '', 'rankingscore': 1, 'justification': 'source1'
            },
        ],
        -1,
        None,
        pytest.raises(ValueError),
    ),
    (
        [
            {'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': ''},
        ],
        1,
        None,
        pytest.raises(KeyError),
    ),
])
def test_rank(owners, k, expected_out, expected_raises):
    with expected_raises:
        assert rank(owners, k=k) == expected_out


@pytest.mark.parametrize('owner,expected_out', [
    # email with casing, whitespace
    (
        {'name': 'Alice ', 'email': 'aLiCe@example.com ', 'source': 'source1', 'timestamp': '1'},
        {'name': 'Alice ', 'email': 'alice@example.com', 'source': 'source1', 'timestamp': '1',
         'canonicalization': 'alice@example.com'},
    ),
    # name with casing, whitespace
    (
        {'name': 'Alice ', 'email': '', 'source': 'source1', 'timestamp': '1'},
        {'name': 'alice', 'email': '', 'source': 'source1', 'timestamp': '1', 'canonicalization': 'alice'},
    ),
    # neither
    (
        {'name': '', 'email': '', 'source': 'source1', 'timestamp': '1'},
        {'name': '', 'email': '', 'source': 'source1', 'timestamp': '1', 'canonicalization': ''},
    ),
])
def test_canonicalize(owner, expected_out):
    assert _canonicalize(owner) == expected_out


@pytest.mark.parametrize('owners,expected_out', [
    # same email, different names, sources, timestamps
    (
        [
            {'name': 'Alice ', 'email': 'alice@example.com', 'source': 'source1', 'timestamp': '1',
             'canonicalization': 'alice@example.com'},
            {'name': 'Bob ', 'email': 'alice@example.com', 'source': 'source2', 'timestamp': '2',
             'canonicalization': 'alice@example.com'},
        ],
        [
            {'name': 'Alice ', 'email': 'alice@example.com', 'source': 'source1 | source2', 'timestamp': '2', 'count': 2},
        ]
    ),
    # same email, no names
    (
        [
            {'name': '', 'email': 'alice@example.com', 'source': 'source1', 'timestamp': '1',
             'canonicalization': 'alice@example.com'},
            {'name': '', 'email': 'alice@example.com', 'source': 'source1', 'timestamp': '1',
             'canonicalization': 'alice@example.com'},
        ],
        [
            {'name': '', 'email': 'alice@example.com', 'source': 'source1', 'timestamp': '1', 'count': 2},
        ]
    ),
    # same email, same names
    (
        [
            {'name': 'Alice', 'email': 'alice@example.com', 'source': 'source1', 'timestamp': '1',
             'canonicalization': 'alice@example.com'},
            {'name': 'Alice', 'email': 'bob@example.com', 'source': 'source2', 'timestamp': '2',
             'canonicalization': 'bob@example.com'},
            {'name': 'Alice', 'email': 'alice@example.com', 'source': 'source2', 'timestamp': '2',
             'canonicalization': 'alice@example.com'},
        ],
        [
            {'name': 'Alice', 'email': 'alice@example.com', 'source': 'source1 | source2', 'timestamp': '2', 'count': 2},
            {'name': 'Alice', 'email': 'bob@example.com', 'source': 'source2', 'timestamp': '2', 'count': 1},
        ]
    ),
    # no email, different names
    (
        [
            {'name': 'alice', 'email': '', 'source': 'source1', 'timestamp': '1', 'canonicalization': 'alice'},
            {'name': 'bob', 'email': '', 'source': 'source2', 'timestamp': '2', 'canonicalization': 'bob'},
        ],
        [
            {'name': 'alice', 'email': '', 'source': 'source1', 'timestamp': '1', 'count': 1},
            {'name': 'bob', 'email': '', 'source': 'source2', 'timestamp': '2', 'count': 1},
        ]
    ),
    # no email, same names
    (
        [
            {'name': 'alice', 'email': '', 'source': 'source1', 'timestamp': '1', 'canonicalization': 'alice'},
            {'name': 'alice', 'email': '', 'source': 'source2', 'timestamp': '2', 'canonicalization': 'alice'},
        ],
        [
            {'name': 'alice', 'email': '', 'source': 'source1 | source2', 'timestamp': '2', 'count': 2},
        ]
    ),
    # some emails present, others missing
    (
        [
            {'name': 'Alice', 'email': 'alice@example.com', 'source': 'source1', 'timestamp': '1',
             'canonicalization': 'alice@example.com'},
            {'name': 'alice', 'email': '', 'source': 'source3', 'timestamp': '3',
             'canonicalization': 'alice'},
            {'name': 'Bob', 'email': 'alice@example.com', 'source': 'source2', 'timestamp': '2',
             'canonicalization': 'alice@example.com'},
            {'name': 'alice', 'email': '', 'source': 'source4', 'timestamp': '4',
             'canonicalization': 'alice'},
        ],
        [
            {'name': 'Alice', 'email': 'alice@example.com', 'source': 'source1 | source2', 'timestamp': '2', 'count': 2},
            {'name': 'alice', 'email': '', 'source': 'source3 | source4', 'timestamp': '4', 'count': 2},
        ]
    ),
    # empty input
    (
        [],
        []
    )
])
def test_aggregate(owners, expected_out):
    assert sorted(aggregate(owners), key=lambda x: sorted(x.items())) == sorted(expected_out, key=lambda x: sorted(x.items()))


@pytest.mark.parametrize('deduplicated, expected_out', [
    # equal counts
    (
        [
            {'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1 | source2', 'timestamp': '2', 'count': 2},
            {'name': 'aa', 'email': '', 'source': 'source3 | source4', 'timestamp': '4', 'count': 2},
        ],
        [
            {'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1 | source2', 'timestamp': '2', 'rankingscore': 1.0},
            {'name': 'aa', 'email': '', 'source': 'source3 | source4', 'timestamp': '4', 'rankingscore': 1.0},
        ]
    ),
    # unequal counts
    (
        [
            {'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '2', 'count': 1},
            {'name': 'aa', 'email': '', 'source': 'source3 | source4', 'timestamp': '4', 'count': 2},
        ],
        [
            {'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '2', 'rankingscore': 0.5},
            {'name': 'aa', 'email': '', 'source': 'source3 | source4', 'timestamp': '4', 'rankingscore': 1.0},
        ]
    ),
    # empty owners
    (
        [],
        []
    )
])
def test_score(deduplicated, expected_out):
    assert score(deduplicated) == expected_out


@pytest.mark.parametrize('owners, expected_out', [
    # ideal input
    (
        [
            {'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1'},
            {'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1'},
        ],
        [
            {
                'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1',
                'rankingscore': 1.0, 'justification': 'source1'
            },
        ]
    ),
    # empty input
    (
        [],
        []
    ),
    # ideal input with new string field added
    (
        [
            {'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1', 'new field': 'val1'},
            {'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1', 'new field': 'val2'},
        ],
        [
            {
                'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1',
                'rankingscore': 1, 'justification': 'source1', 'new field': 'val1 | val2'
            },
        ]
    ),
    # ideal input with new numerical field added
    (
        [
            {'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1', 'new field': 1},
            {'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1', 'new field': 2},
        ],
        [
            {
                'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1',
                'rankingscore': 1, 'justification': 'source1', 'new field': 2,
            },
        ]
    ),
    # ideal input with some new field values added
    (
        [
            {'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1', 'new field': 1},
            {'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1'},
        ],
        [
            {
                'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1',
                'rankingscore': 1, 'justification': 'source1', 'new field': 1,
            },
        ]
    ),
    # ideal input with some new field values added
    (
        [
            {'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1', 'new field': 'val1'},
            {'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1'},
        ],
        [
            {
                'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1',
                'rankingscore': 1, 'justification': 'source1', 'new field': 'val1',
            },
        ]
    ),
    # ideal input with some new field values added that we can't handle
    (
        [
            {'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1', 'new field': None},
            {'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1'},
        ],
        [
            {
                'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1',
                'rankingscore': 1, 'justification': 'source1',
            },
        ]
    ),
    # bad inputs -- None
    (
        None,
        []
    ),
    # bad inputs -- None
    (
        [None],
        []
    ),
    # bad input -- name is None
    (
        [
            {'name': None, 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1'},
        ],
        [
            {
                'name': '', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1',
                'rankingscore': 1, 'justification': 'source1'
            },
        ]
    ),
    # bad input -- email is None
    (
        [
            {'name': 'a', 'email': None, 'source': 'source1', 'timestamp': '1'},
        ],
        [
            {
                'name': 'a', 'email': None, 'source': 'source1', 'timestamp': '1',
                'rankingscore': 1, 'justification': 'source1'
            },
        ]
    ),
    # bad input -- source is None
    (
        [
            {'name': 'a', 'email': 'email1@gmail.com', 'source': None, 'timestamp': '1'},
        ],
        [
            {
                'name': 'a', 'email': 'email1@gmail.com', 'source': '', 'timestamp': '1',
                'rankingscore': 1, 'justification': ''
            },
        ]
    ),
    # bad input -- timestamp is None
    (
        [
            {'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': None},
        ],
        [
            {
                'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1',
                'timestamp': '', 'rankingscore': 1, 'justification': 'source1'
            },
        ]
    ),
    # bad input -- missing name
    (
        [
            {'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1'},
        ],
        [
            {
                'name': '', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '1',
                'rankingscore': 1, 'justification': 'source1'
            },
        ]
    ),
    # bad input -- missing email
    (
        [
            {'name': 'a', 'source': 'source1', 'timestamp': '1'},
        ],
        [
            {
                'name': 'a', 'email': '', 'source': 'source1', 'timestamp': '1',
                'rankingscore': 1, 'justification': 'source1'
            },
        ]
    ),
    # bad input -- missing source
    (
        [
            {'name': 'a', 'email': 'email1@gmail.com', 'timestamp': '1'},
        ],
        [
            {
                'name': 'a', 'email': 'email1@gmail.com', 'source': '', 'timestamp': '1',
                'rankingscore': 1, 'justification': ''
            },
        ]
    ),
    # bad input -- missing timestamp
    (
        [
            {'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1'},
        ],
        [
            {
                'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': '',
                'rankingscore': 1, 'justification': 'source1'
            },
        ]
    ),
    # timestamp as numerical type
    (
        [
            {'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': 1},
            {'name': 'a', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': 2},
        ],
        [
            {
                'name': 'aa', 'email': 'email1@gmail.com', 'source': 'source1', 'timestamp': 2,
                'rankingscore': 1.0, 'justification': 'source1'
            },
        ]
    ),
])
def test_main(mocker, owners, expected_out, capfd):
    # Construct payload
    arg_payload = {}
    arg_payload["owners"] = owners
    mocker.patch.object(demisto,
                        'args',
                        return_value=arg_payload)

    # Execute main using a mock that we can inspect for `executeCommand`
    demisto_execution_mock = mocker.patch.object(demisto, 'executeCommand')
    with capfd.disabled():  # avoids test failures on demisto.error statements
        main()

    # Verify the output value was set
    expected_calls_to_mock_object = [unittest.mock.call('setAlert', {'asmserviceowner': expected_out})]
    assert demisto_execution_mock.call_args_list == expected_calls_to_mock_object
