import pytest
from la_taint_nodes import (
    get_max_hard_taints,
    get_max_soft_taints,
    set_expected_taints
)


@pytest.mark.parametrize(
    "wnode_num,expected",
    [
        (1, 0),
        (2, 1),
        (3, 1),
        (4, 2),
        (5, 2),
        (6, 3)
    ]
)
def test_get_max_hard_taints(wnode_num, expected):
    assert get_max_hard_taints(wnode_num) == expected


@pytest.mark.parametrize(
    "wnode_num,hard_taints,expected",
    [
        (1, 0, 0),
        (2, 0, 1),
        (2, 1, 0),
        (3, 0, 1),
        (3, 1, 0),
        (4, 0, 2),
        (4, 1, 1),
        (4, 2, 0),
        (5, 0, 2),
        (5, 1, 1),
        (5, 2, 0),
        (6, 0, 3),
        (6, 1, 2),
        (6, 2, 1),
        (6, 3, 0),
    ]
)
def test_get_max_soft_taints(wnode_num, hard_taints, expected):
    assert hard_taints <= get_max_hard_taints(wnode_num)
    assert get_max_soft_taints(wnode_num, hard_taints) == expected


@pytest.mark.parametrize(
    "worker_nodes_sorted,expected",
    [
        pytest.param(
            {
                'worker-0': {
                    'existing_taint':
                        {
                            'effect': 'NoSchedule',
                            'key': 'la-taint-psi-cpu',
                            'value': 'NoSchedule'
                        },
                    'proposed_taint': None,
                    'cpu_pressure': 56.1
                },
                'worker-1': {
                    'existing_taint':
                        {
                            'effect': 'NoSchedule',
                            'key': 'la-taint-psi-cpu',
                            'value': 'NoSchedule'
                        },
                    'proposed_taint': None,
                    'cpu_pressure': 46.0
                },
                'worker-2': {
                    'existing_taint': None,
                    'proposed_taint': None,
                    'cpu_pressure': 18.2
                }
            },
            {
                'worker-0': {
                    'proposed_taint': {
                        'effect': 'NoSchedule',
                        'key': 'la-taint-psi-cpu',
                        'value': 'NoSchedule',
                    },
                },
                'worker-1': {
                    'proposed_taint': None,
                },
                'worker-2': {
                    'proposed_taint': None,
                }
            },
            id="Remove hard taint",
        ),
        pytest.param(
            {
                'worker-0': {
                    'existing_taint': None,
                    'proposed_taint': None,
                    'cpu_pressure': 56.1
                },
                'worker-1': {
                    'existing_taint': None,
                    'proposed_taint': None,
                    'cpu_pressure': 46.0
                },
                'worker-2': {
                    'existing_taint': None,
                    'proposed_taint': None,
                    'cpu_pressure': 18.2
                }
            },
            {
                'worker-0': {
                    'proposed_taint': {
                        'effect': 'NoSchedule',
                        'key': 'la-taint-psi-cpu',
                        'value': 'NoSchedule',
                    },
                },
                'worker-1': {
                    'proposed_taint': None,
                },
                'worker-2': {
                    'proposed_taint': None,
                }
            },
            id="Add hard taint",
        ),
        pytest.param(
            {
                'worker-0': {
                    'existing_taint': None,
                    'proposed_taint': None,
                    'cpu_pressure': 36.1
                },
                'worker-1': {
                    'existing_taint': None,
                    'proposed_taint': None,
                    'cpu_pressure': 25.0
                },
                'worker-2': {
                    'existing_taint': None,
                    'proposed_taint': None,
                    'cpu_pressure': 0.2
                }
            },
            {
                'worker-0': {
                    'proposed_taint': {
                        'effect': 'PreferNoSchedule',
                        'key': 'la-taint-psi-cpu',
                        'value': 'PreferNoSchedule',
                    },
                },
                'worker-1': {
                    'proposed_taint': None,
                },
                'worker-2': {
                    'proposed_taint': None,
                }
            },
            id="Add soft taint",
        ),
        pytest.param(
            {
                'worker-0': {
                    'existing_taint': None,
                    'proposed_taint': None,
                    'cpu_pressure': 36.1
                },
                'worker-1': {
                    'existing_taint':
                        {
                            'effect': 'NoSchedule',
                            'key': 'la-taint-psi-cpu',
                            'value': 'NoSchedule'
                        },
                    'proposed_taint': None,
                    'cpu_pressure': 25.0
                },
                'worker-2': {
                    'existing_taint': None,
                    'proposed_taint': None,
                    'cpu_pressure': 0.2
                }
            },
            {
                'worker-0': {
                    'proposed_taint': {
                        'effect': 'PreferNoSchedule',
                        'key': 'la-taint-psi-cpu',
                        'value': 'PreferNoSchedule',
                    },
                },
                'worker-1': {
                    'proposed_taint': None,
                },
                'worker-2': {
                    'proposed_taint': None,
                }
            },
            id="Swap hard taint",
        ),
        pytest.param(
            {
                'worker-0': {
                    'existing_taint': None,
                    'proposed_taint': None,
                    'cpu_pressure': 1.1
                },
                'worker-1': {
                    'existing_taint': None,
                    'proposed_taint': None,
                    'cpu_pressure': 2.0
                },
                'worker-2': {
                    'existing_taint': None,
                    'proposed_taint': None,
                    'cpu_pressure': 3.2
                }
            },
            {
                'worker-0': {
                    'proposed_taint': None,
                },
                'worker-1': {
                    'proposed_taint': None,
                },
                'worker-2': {
                    'proposed_taint': None,
                }
            },
            id="Remove all taints",
        ),
    ]
)
def test_set_expected_taints(worker_nodes_sorted, expected):
    set_expected_taints(worker_nodes_sorted)
    for node in expected:
        assert node in worker_nodes_sorted
    for node in worker_nodes_sorted:
        assert node in expected
        assert (worker_nodes_sorted[node]['proposed_taint'] ==
                expected[node]['proposed_taint'])
