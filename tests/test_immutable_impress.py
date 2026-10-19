"""Immutable evaluation preserves identity, visits once, and reuses payloads."""
import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from CelebiChrono.kernel.immutable_impress import impress_immutable
from CelebiChrono.kernel.vimpression import VImpression
from CelebiChrono.kernel.impression_store import ImpressionStore


def write_object(root, name, kind='task', predecessors=(), aliases=None, source='value=1\n'):
    path = root / name
    (path / '.celebi').mkdir(parents=True, exist_ok=True)
    data = {'object_type': kind, 'predecessors': list(predecessors),
            'alias_to_path': aliases or {}}
    (path / '.celebi/config.json').write_text(json.dumps(data))
    (path / 'run.py').write_text(source)
    return path


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = tmp_path / 'project'
    (root / '.celebi').mkdir(parents=True)
    (root / '.celebi/config.json').write_text(json.dumps(
        {'object_type': 'project', 'project_uuid': '1' * 32}))
    (root / '.celebi/project.json').write_text('{}')
    monkeypatch.chdir(root)
    return root


def test_same_uuid_and_payload_as_existing_implementation(project):
    from CelebiChrono.kernel.vobject import VObject
    from CelebiChrono.kernel.chern_cache import ChernCache
    from CelebiChrono.utils.path_utils import native_path_access
    write_object(project, 'algorithm', kind='algorithm')
    write_object(project, 'left', predecessors=['algorithm'], aliases={'algorithm': 'algorithm'})
    write_object(project, 'right', predecessors=['algorithm'], source='value=2\n')
    write_object(project, 'merge', predecessors=['left', 'right'], aliases={'data': 'left'})
    with native_path_access(), ChernCache.instance().freeze_project_modification_time(str(project)):
        VObject(str(project)).impress()
    store = ImpressionStore(str(project))
    expected = {}
    for name in ['algorithm', 'left', 'right', 'merge']:
        uid = json.loads((project / name / '.celebi/config.local.json').read_text())['impression']
        expected[name] = uid
    old_refs = {uid: store.read_impression_ref(uid) for uid in expected.values()}
    result = impress_immutable(project)
    assert result['objects'] == expected
    assert result['created'] == 0 and result['reused'] == 4
    assert {uid: store.read_impression_ref(uid) for uid in expected.values()} == old_refs
    # Fresh payloads must match the legacy tree/aliases as well as UUIDs.
    shutil.rmtree(project / '.celebi/impressions')
    shutil.rmtree(project / '.celebi/impressions_store')
    result = impress_immutable(project)
    assert result['objects'] == expected
    for uid, ref in old_refs.items():
        current = ImpressionStore(str(project)).read_impression_ref(uid)
        for key in ['root_tree', 'dependencies', 'alias_to_impression', 'tree', 'object_type']:
            assert current[key] == ref[key]


def test_1000_tasks_visit_each_node_once_without_mtime_or_recursive_checks(project, monkeypatch):
    from CelebiChrono.utils import csys
    from CelebiChrono.utils import path_utils
    from CelebiChrono.kernel.vobj_impression import ImpressionManagement
    write_object(project, 'algorithm', kind='algorithm')
    for n in range(1000):
        write_object(project, f'task{n}', predecessors=['algorithm'], source=f'value={n}\n')
    def forbidden(*args, **kwargs):
        raise AssertionError('Interactive invalidation path used')
    monkeypatch.setattr(csys, 'dir_mtime', forbidden)
    monkeypatch.setattr(csys, 'project_cache_invalidation_method', forbidden)
    monkeypatch.setattr(path_utils, 'exists_case_sensitive', forbidden)
    monkeypatch.setattr(path_utils, 'exists_case_insensitive', forbidden)
    monkeypatch.setattr(ImpressionManagement, 'is_impressed_fast', forbidden)
    original = VImpression.generate_imp_uuid
    calls = []
    def count(self, project_uuid, path, deps):
        calls.append(path)
        return original(self, project_uuid, path, deps)
    monkeypatch.setattr(VImpression, 'generate_imp_uuid', count)
    result = impress_immutable(project)
    assert len(calls) == len(set(calls)) == result['processed'] == 1001


def test_cross_checkout_reuse_and_only_changed_dependents_get_new_uuid(project, tmp_path, monkeypatch):
    write_object(project, 'algorithm', kind='algorithm')
    write_object(project, 'left', predecessors=['algorithm'])
    write_object(project, 'right', predecessors=['algorithm'], source='value=2\n')
    write_object(project, 'child', predecessors=['left'])
    pristine = tmp_path / 'pristine'
    shutil.copytree(project, pristine)
    cache = tmp_path / 'cache'
    first = impress_immutable(project, cache)
    refs = cache / '.celebi/impressions_store/refs/impressions'
    mtimes = {p.name: p.stat().st_mtime_ns for p in refs.iterdir()}
    monkeypatch.chdir(pristine)
    (pristine / 'README.md').write_text('new docs')
    second = impress_immutable(pristine, cache)
    assert second['objects'] == first['objects']
    assert second['created'] == 0 and second['reused'] == 4
    assert {p.name: p.stat().st_mtime_ns for p in refs.iterdir()} == mtimes
    (pristine / 'left/run.py').write_text('value=42\n')
    third = impress_immutable(pristine, cache)
    assert third['created'] == 2 and third['reused'] == 2
    assert third['objects']['left'] != first['objects']['left']
    assert third['objects']['right'] == first['objects']['right']
    assert third['objects']['child'] != first['objects']['child']
    assert len(list(refs.iterdir())) == 6  # Historical refs remain available.


@pytest.mark.parametrize('predecessors', [['missing'], ['self']])
def test_invalid_graph_rejected_before_writing_impressions(project, predecessors):
    write_object(project, 'self', predecessors=predecessors)
    with pytest.raises(ValueError, match='Missing|cycle'):
        impress_immutable(project)
    assert not (project / '.celebi/impressions').exists()


def test_cli_option_and_no_remote_sync(project, monkeypatch):
    from CelebiChrono.celebi_cli.commands import communication
    write_object(project, 'task')
    def forbidden(*args):
        raise AssertionError('Immutable mode must not contact Yuki')
    monkeypatch.setattr(communication, '_best_effort_sync_live', forbidden)
    result = CliRunner().invoke(communication.impress_command, ['--immutable'])
    assert result.exit_code == 0, result.output
    assert 'Impress 1/1' in result.output
    invalid = CliRunner().invoke(communication.impress_command, ['--cache-dir', 'cache'])
    assert invalid.exit_code != 0


def test_native_path_mode_is_context_local_and_restored_on_error(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from CelebiChrono.utils import path_utils
    calls = []
    monkeypatch.setattr(path_utils, 'exists_case_sensitive', lambda p: calls.append(p) or False)
    with pytest.raises(RuntimeError):
        with path_utils.native_path_access():
            assert path_utils.exists(str(tmp_path))
            with ThreadPoolExecutor(1) as pool:
                assert pool.submit(path_utils.exists, str(tmp_path)).result() is False
            raise RuntimeError('test cleanup')
    assert path_utils.exists(str(tmp_path)) is False
    assert len(calls) == 2


def test_missing_cached_blob_is_rebuilt(project):
    from CelebiChrono.utils.path_utils import native_path_access
    write_object(project, 'task')
    result = impress_immutable(project)
    with native_path_access():
        store = ImpressionStore(str(project))
        uid = result['objects']['task']
        tree = store.get_tree(store.read_impression_ref(uid)['root_tree'])
        missing = Path(store._blob_path(tree[0]['hash']))
        missing.unlink()
        repaired = impress_immutable(project)
        assert repaired['created'] == 1
        assert missing.is_file()


def test_immutable_runtime_files_are_never_published():
    from CelebiChrono.interface.shell_modules.server_booking import forbidden
    for name in ['immutable-impress.lock', 'immutable-impress.json',
                 'immutable-impress-progress.json']:
        assert forbidden('.celebi/' + name)
    assert not forbidden('.celebi/config.json')
