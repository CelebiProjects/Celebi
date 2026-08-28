"""Tests for viewing past impressions by short id."""
import os
import unittest
from unittest.mock import MagicMock, patch
from colored import Fore, Style
import prepare
import CelebiChrono.kernel.vobject as vobj
from CelebiChrono.kernel.chern_cache import ChernCache
from CelebiChrono.kernel.chern_communicator import ChernCommunicator
import CelebiChrono.kernel.vtask as vtsk
from CelebiChrono.interface.shell_modules import visualization

CHERN_CACHE = ChernCache.instance()


class TestResolveImpressionUuid(unittest.TestCase):
    """Resolving a short impression id to a full uuid."""

    def setUp(self):
        """Set Up."""
        self.cwd = os.getcwd()
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        self.task = vobj.VObject("FitTask")
        self.task.impress()

    def tearDown(self):
        """Tear Down."""
        os.chdir(self.cwd)
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_expands_short_prefix_to_full_uuid(self):
        """A 7-char prefix resolves to the full impression uuid."""
        print(Fore.BLUE + "Testing short prefix resolution..." + Style.RESET)
        impression = self.task.impression()
        resolved = self.task.resolve_impression_uuid(impression.short_uuid())
        self.assertEqual(resolved, impression.uuid)

    def test_accepts_full_uuid_unchanged(self):
        """A full uuid resolves to itself."""
        print(Fore.BLUE + "Testing full uuid resolution..." + Style.RESET)
        impression = self.task.impression()
        resolved = self.task.resolve_impression_uuid(impression.uuid)
        self.assertEqual(resolved, impression.uuid)

    def test_ambiguous_prefix_raises(self):
        """A prefix matching more than one impression is an error."""
        print(Fore.BLUE + "Testing ambiguous prefix..." + Style.RESET)
        impressions_dir = os.path.join(
            self.task.project_path(), ".celebi", "impressions"
        )
        for suffix in ("aaa", "bbb"):
            os.makedirs(os.path.join(impressions_dir, f"dupprefix{suffix}"))

        with self.assertRaises(ValueError) as ctx:
            self.task.resolve_impression_uuid("dupprefix")
        self.assertIn("dupprefix", str(ctx.exception))

    def test_unknown_token_returned_unchanged(self):
        """An unmatched token comes back as-is so callers can report it."""
        print(Fore.BLUE + "Testing unknown token..." + Style.RESET)
        self.assertEqual(
            self.task.resolve_impression_uuid("nosuchimpression"),
            "nosuchimpression",
        )


class TestImpviewImpression(unittest.TestCase):
    """impview can target a specific impression."""

    def setUp(self):
        """Set Up."""
        self.cwd = os.getcwd()
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")

    def tearDown(self):
        """Tear Down."""
        os.chdir(self.cwd)
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_impview_passes_given_impression(self):
        """impview(impression) forwards that impression, not the current one."""
        print(Fore.BLUE + "Testing impview with explicit impression..." + Style.RESET)
        task = vtsk.VTask("FitTask")
        task.impress()
        other = vtsk.VTask("GenTask")
        other.impress()
        other_impression = other.impression()

        with patch.object(ChernCommunicator, "instance") as mock_instance:
            mock_communicator = MagicMock()
            mock_instance.return_value = mock_communicator

            task.impview(other_impression)
            mock_communicator.impview.assert_called_once_with(other_impression)


class TestCliViewImpression(unittest.TestCase):
    """celebi-cli view/viewurl forward the impression argument."""

    def test_view_command_forwards_impression(self):
        """view_command passes the positional impression id to shell.view."""
        from click.testing import CliRunner
        from CelebiChrono.celebi_cli.commands import visualization as cli_vis
        with patch("CelebiChrono.interface.shell.view") as shell_view:
            shell_view.return_value = MagicMock()
            shell_view.return_value.messages = []
            result = CliRunner().invoke(cli_vis.view_command, ["abc1234"])
        self.assertEqual(result.exit_code, 0, result.output)
        shell_view.assert_called_once_with("abc1234")

    def test_viewurl_command_forwards_impression(self):
        """viewurl_command passes the positional impression id to shell.viewurl."""
        from click.testing import CliRunner
        from CelebiChrono.celebi_cli.commands import visualization as cli_vis
        with patch("CelebiChrono.interface.shell.viewurl") as shell_viewurl:
            shell_viewurl.return_value = MagicMock()
            shell_viewurl.return_value.messages = []
            result = CliRunner().invoke(cli_vis.viewurl_command, ["abc1234"])
        self.assertEqual(result.exit_code, 0, result.output)
        shell_viewurl.assert_called_once_with("abc1234")


class TestViewCompletion(unittest.TestCase):
    """view tab-completion offers history short ids, not browsers."""

    def setUp(self):
        """Set Up."""
        self.cwd = os.getcwd()
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        self.task = vobj.VObject("FitTask")
        self.task.impress()
        self.old_uuid = self.task.impression().uuid
        celebi_yaml = os.path.join(self.task.path, "celebi.yaml")
        with open(celebi_yaml, "a", encoding="utf-8") as f:
            f.write("# touch\n")
        CHERN_CACHE.impression_consult_table.clear()
        CHERN_CACHE.project_modification_time = (None, 0)
        self.task.impress()
        self.new_uuid = self.task.impression().uuid

    def tearDown(self):
        """Tear Down."""
        os.chdir(self.cwd)
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_complete_view_offers_history_short_ids(self):
        """complete_view returns the short ids of the task's lineage."""
        from CelebiChrono.interface.chern_shell import completions as compl
        with patch.object(
            compl.MANAGER, "current_object", return_value=self.task
        ):
            matches = compl.ChernShellCompletions().complete_view(
                None, "view", 0, 4
            )
        self.assertEqual(
            set(matches), {self.new_uuid[:7], self.old_uuid[:7]}
        )


class TestShellViewImpression(unittest.TestCase):
    """Shell view()/viewurl() accept a short impression id."""

    def setUp(self):
        """Set Up."""
        self.mock_obj = MagicMock()
        self.mock_obj.is_task.return_value = True
        self.impression = MagicMock()
        self.impression.uuid = "11111111-2222-3333-4444-555555555555"
        self.mock_obj.resolve_impression_uuid.return_value = self.impression.uuid
        self.mock_obj.impression_in_history.return_value = True
        self.mock_obj.impview.return_value = "http://dite/imp-view/proj/11111111-2222-3333-4444-555555555555"
        self.manager_patch = patch.object(
            visualization.MANAGER, "current_object", return_value=self.mock_obj
        )
        self.vimpression_patch = patch.object(
            visualization, "VImpression"
        )
        self.mock_vimpr = self.vimpression_patch.start()
        self.mock_vimpr.return_value.is_zombie.return_value = False
        self.manager_patch.start()

    def tearDown(self):
        """Tear Down."""
        self.manager_patch.stop()
        self.vimpression_patch.stop()

    def test_view_opens_url_for_given_impression(self):
        """view('1111111') resolves the id and opens its url."""
        print(Fore.BLUE + "Testing view with impression id..." + Style.RESET)
        with patch.object(visualization, "webbrowser") as mock_browser:
            result = visualization.view("1111111")
        self.mock_obj.resolve_impression_uuid.assert_called_once_with("1111111")
        self.mock_obj.impview.assert_called_once_with(self.mock_vimpr.return_value)
        mock_browser.open.assert_called_once_with(
            "http://dite/imp-view/proj/11111111-2222-3333-4444-555555555555"
        )
        self.assertIn("success", [entry[1] for entry in result.messages])

    def test_viewurl_returns_url_for_given_impression(self):
        """viewurl('1111111') puts the resolved url in message.data."""
        print(Fore.BLUE + "Testing viewurl with impression id..." + Style.RESET)
        result = visualization.viewurl("1111111")
        self.mock_obj.resolve_impression_uuid.assert_called_once_with("1111111")
        self.assertEqual(
            result.data["url"],
            "http://dite/imp-view/proj/11111111-2222-3333-4444-555555555555",
        )

    def test_view_warns_when_impression_is_outside_lineage(self):
        """view warns but still opens when the impression is foreign."""
        print(Fore.BLUE + "Testing view foreign impression warning..." + Style.RESET)
        self.mock_obj.impression_in_history.return_value = False
        with patch.object(visualization, "webbrowser") as mock_browser:
            result = visualization.view("1111111")
        self.assertIn("warning", [entry[1] for entry in result.messages])
        mock_browser.open.assert_called_once()

    def test_view_reports_unknown_impression(self):
        """view errors when the impression does not exist."""
        print(Fore.BLUE + "Testing view unknown impression..." + Style.RESET)
        self.mock_vimpr.return_value.is_zombie.return_value = True
        with patch.object(visualization, "webbrowser") as mock_browser:
            result = visualization.view("deadbeef")
        self.assertIn("error", [entry[1] for entry in result.messages])
        mock_browser.open.assert_not_called()


class TestViewPassesImpressionObject(unittest.TestCase):
    """view() hands impview an impression object, not a bare uuid str."""

    def setUp(self):
        """Set Up."""
        self.cwd = os.getcwd()
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        self.task = vtsk.VTask("FitTask")
        self.task.impress()
        self.uuid = self.task.impression().uuid
        self.manager_patch = patch.object(
            visualization.MANAGER, "current_object", return_value=self.task
        )
        self.manager_patch.start()

    def tearDown(self):
        """Tear Down."""
        self.manager_patch.stop()
        os.chdir(self.cwd)
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_view_opens_url_built_from_impression_uuid(self):
        """view(short_id) reaches the communicator with an object carrying .uuid."""
        print(Fore.BLUE + "Testing view short id end-to-end..." + Style.RESET)

        def impview_side_effect(impression):
            # Mirrors ChernCommunicator.impview: needs impression.uuid.
            return f"http://dite/imp-view/proj/{impression.uuid}"

        with patch.object(ChernCommunicator, "instance") as mock_instance:
            mock_communicator = MagicMock()
            mock_communicator.impview.side_effect = impview_side_effect
            mock_instance.return_value = mock_communicator
            with patch.object(visualization, "webbrowser") as mock_browser:
                result = visualization.view(self.uuid[:7])
        self.assertIn("success", [entry[1] for entry in result.messages])
        mock_browser.open.assert_called_once_with(
            f"http://dite/imp-view/proj/{self.uuid}"
        )


class TestImpressionInHistory(unittest.TestCase):
    """Checking whether an impression belongs to the object's lineage."""

    def setUp(self):
        """Set Up."""
        self.cwd = os.getcwd()
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        self.task = vobj.VObject("FitTask")
        self.task.impress()
        self.old_uuid = self.task.impression().uuid

        # Change the task so the next impress produces a different uuid,
        # making old_uuid a parent of the new impression.
        celebi_yaml = os.path.join(self.task.path, "celebi.yaml")
        with open(celebi_yaml, "a", encoding="utf-8") as f:
            f.write("# touch\n")
        CHERN_CACHE.impression_consult_table.clear()
        CHERN_CACHE.project_modification_time = (None, 0)
        self.task.impress()
        self.new_uuid = self.task.impression().uuid

    def tearDown(self):
        """Tear Down."""
        os.chdir(self.cwd)
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_current_impression_is_in_history(self):
        """The object's current impression counts as its own lineage."""
        print(Fore.BLUE + "Testing current impression lineage..." + Style.RESET)
        self.assertNotEqual(self.old_uuid, self.new_uuid)
        self.assertTrue(self.task.impression_in_history(self.new_uuid))

    def test_parent_impression_is_in_history(self):
        """A superseded impression is still part of the lineage."""
        print(Fore.BLUE + "Testing parent impression lineage..." + Style.RESET)
        self.assertTrue(self.task.impression_in_history(self.old_uuid))

    def test_foreign_impression_is_not_in_history(self):
        """An impression from elsewhere is not in this object's lineage."""
        print(Fore.BLUE + "Testing foreign impression lineage..." + Style.RESET)
        other = vobj.VObject("GenTask")
        other.impress()
        other_uuid = other.impression().uuid
        self.assertNotEqual(other_uuid, self.new_uuid)
        self.assertFalse(self.task.impression_in_history(other_uuid))


if __name__ == "__main__":
    unittest.main()
