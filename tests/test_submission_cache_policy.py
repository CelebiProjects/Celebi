"""A leaf submission must retain cache settings of its upstream tasks."""
from types import SimpleNamespace
from CelebiChrono.kernel.vobj_execution import _submission_cache_policy


def node(name, task=True, cache=True, parents=()):
    return SimpleNamespace(path=name, is_task=lambda: task,
                           predecessors=lambda: list(parents),
                           impression=lambda: SimpleNamespace(uuid=name),
                           cache_on_runner=lambda: cache)


def test_leaf_includes_dependencies_and_preserves_disabled_cache():
    data = node('data')
    algorithm = node('algorithm', task=False, parents=(data,))
    partition = node('partition', cache=False, parents=(algorithm, data))
    final = node('final', parents=(partition, algorithm))
    objects = {x.path: x for x in (data, algorithm, partition, final)}
    owner = SimpleNamespace(get_vtask=objects.__getitem__)
    assert _submission_cache_policy(owner, [final]) == {
        'data': True, 'partition': False, 'final': True}


def test_shared_dependencies_are_visited_once():
    calls = []
    data = node('data')
    data.predecessors = lambda: calls.append('data') or []
    first = node('first', parents=(data,))
    second = node('second', parents=(data,))
    objects = {x.path: x for x in (data, first, second)}
    owner = SimpleNamespace(get_vtask=objects.__getitem__)
    assert set(_submission_cache_policy(owner, [first, second, first])) == set(objects)
    assert calls == ['data']
