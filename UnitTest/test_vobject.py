"""Test vobject."""
import os
import unittest
from colored import Fore, Style
import prepare
import CelebiChrono.kernel.vobject as vobj
from CelebiChrono.kernel.chern_cache import ChernCache

CHERN_CACHE = ChernCache.instance()


class TestChernProject(unittest.TestCase):

    """Test Chern Project."""
    def setUp(self):
        """Set Up."""
        self.cwd = os.getcwd()

    def tearDown(self):
        """Tear Down."""
        os.chdir(self.cwd)

    def test_impression(self):
        """Test impression."""
        print(Fore.BLUE + "Testing impression..." + Style.RESET)

        print("#1 Test whether the change could be identified.")
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        obj_gen = vobj.VObject("Gen")
        obj_gen_task = vobj.VObject("GenTask")
        obj_fit = vobj.VObject("Fit")
        obj_fit_task = vobj.VObject("FitTask")

        self.assertFalse(obj_gen.is_impressed())
        self.assertFalse(obj_gen_task.is_impressed())
        self.assertTrue(obj_fit.is_impressed())
        self.assertFalse(obj_fit_task.is_impressed())

        self.assertEqual(obj_gen.status(), "new")
        self.assertEqual(obj_gen_task.status(), "new")
        self.assertEqual(obj_fit.status(), "impressed")
        self.assertEqual(obj_fit_task.status(), "new")

        self.assertEqual(str(obj_fit.impression()), "b9317045ab8ada5356d457803196b581")
        self.assertEqual(str(obj_gen.impression()), "3490657eb3256fe5e227d25af825fd0a")


        os.chdir("..")
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

        print("#2 Test whether the impression could be done.")
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        obj_gen = vobj.VObject("Gen")
        obj_gen_task = vobj.VObject("GenTask")
        obj_fit = vobj.VObject("Fit")
        obj_fit_task = vobj.VObject("FitTask")
        obj_fit_task.impress()

        self.assertEqual(obj_gen.status(), "impressed")
        self.assertEqual(obj_gen_task.status(), "impressed")
        self.assertEqual(obj_fit.status(), "impressed")
        self.assertEqual(obj_fit_task.status(), "impressed")

        self.assertTrue(obj_gen.is_impressed_fast())
        self.assertTrue(obj_gen_task.is_impressed_fast())
        self.assertTrue(obj_fit.is_impressed_fast())
        self.assertTrue(obj_fit_task.is_impressed_fast())

        self.assertTrue(obj_gen.is_impressed())
        self.assertTrue(obj_gen_task.is_impressed())
        self.assertTrue(obj_fit.is_impressed())
        self.assertTrue(obj_fit_task.is_impressed())

        list1 = [str(x) for x in obj_fit_task.pred_impressions()]
        list2 = [
            str(x)
            for x in sorted(
                [obj_fit.impression(), obj_gen_task.impression()], key=lambda x: x.uuid
            )
        ]
        self.assertEqual(list1, list2)

        os.chdir("..")
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_clean(self):
        """Test clean."""
        print(Fore.BLUE + "Testing Clean Commands..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        obj_gen = vobj.VObject("Gen")
        obj_gen_task = vobj.VObject("GenTask")
        obj_fit = vobj.VObject("Fit")
        obj_fit_task = vobj.VObject("FitTask")
        obj_fit_task.impress()

        obj_fit_task.clean_impressions()
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

        self.assertEqual(obj_gen.status(), "impressed")
        self.assertEqual(obj_gen_task.status(), "impressed")
        self.assertEqual(obj_fit.status(), "impressed")
        self.assertEqual(obj_fit_task.status(), "new")

        os.chdir("..")
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_alias(self):
        """Test alias."""
        print(Fore.BLUE + "Testing Alias Commands..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        _obj_gen = vobj.VObject("Gen")
        _obj_gen_task = vobj.VObject("GenTask")
        _obj_fit = vobj.VObject("Fit")
        obj_fit_task = vobj.VObject("FitTask")
        obj_fit_task.impress()

        self.assertEqual(list(obj_fit_task.get_alias_list()), ['gen'])
        self.assertEqual(obj_fit_task.alias_to_path("gen"), "GenTask")
        self.assertEqual(obj_fit_task.path_to_alias("GenTask"), "gen")
        self.assertEqual(
            str(obj_fit_task.alias_to_impression("gen")), "a7b794cfffdcdf3e5f4fdb2fbd517d06"
        )
        self.assertTrue(obj_fit_task.has_alias("gen"))
        self.assertFalse(obj_fit_task.has_alias("non_existing_alias"))

        obj_fit_task.set_alias("new_alias", "GenTask")
        self.assertEqual(list(obj_fit_task.get_alias_list()), ['gen'])
        obj_fit_task.remove_alias("gen")
        self.assertEqual(list(obj_fit_task.get_alias_list()), [])
        obj_fit_task.set_alias("new_alias", "GenTask")
        self.assertEqual(list(obj_fit_task.get_alias_list()), ['new_alias'])

        os.chdir("..")
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_arc_management(self):
        """Test arc management."""
        print(Fore.BLUE + "Testing Arc Management Commands..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        obj_gen = vobj.VObject("Gen")
        obj_gen_task = vobj.VObject("GenTask")
        _obj_fit = vobj.VObject("Fit")
        obj_fit_task = vobj.VObject("FitTask")

        self.assertTrue(obj_fit_task.has_predecessor(obj_gen_task))
        self.assertTrue(obj_fit_task.has_predecessor_recursively(obj_gen))
        self.assertTrue(obj_gen_task.has_successor(obj_fit_task))
        self.assertFalse(obj_fit_task.has_predecessor(obj_gen))

        obj_fit_task.remove_input("gen")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

        self.assertFalse(obj_fit_task.has_predecessor(obj_gen_task))
        self.assertFalse(obj_fit_task.has_predecessor_recursively(obj_gen))
        self.assertFalse(obj_gen_task.has_successor(obj_fit_task))
        self.assertFalse(obj_fit_task.has_predecessor(obj_gen))

        os.chdir("..")
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_execution(self):
        """Test execution."""
        print(Fore.BLUE + "Testing Execution Commands..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        _obj_gen = vobj.VObject("Gen")
        _obj_gen_task = vobj.VObject("GenTask")
        _obj_fit = vobj.VObject("Fit")
        _obj_fit_task = vobj.VObject("FitTask")

        os.chdir("..")
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_arc_cache_invalidation(self):
        """Test arc cache invalidation."""
        print(Fore.BLUE + "Testing Arc Cache Invalidation..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        _obj_gen = vobj.VObject("Gen")
        obj_gen_task = vobj.VObject("GenTask")
        _obj_fit = vobj.VObject("Fit")
        obj_fit_task = vobj.VObject("FitTask")

        # Read predecessors to populate the cache
        initial_preds = [p.invariant_path() for p in obj_fit_task.predecessors()]
        self.assertIn("GenTask", initial_preds)

        # Remove the arc; the cache should be invalidated
        obj_fit_task.remove_input("gen")
        preds_after_remove = [p.invariant_path() for p in obj_fit_task.predecessors()]
        self.assertNotIn("GenTask", preds_after_remove)

        # Add the arc back; the cache should be invalidated again
        obj_fit_task.add_arc_from(obj_gen_task)
        preds_after_add = [p.invariant_path() for p in obj_fit_task.predecessors()]
        self.assertIn("GenTask", preds_after_add)

        os.chdir("..")
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_core(self):
        """Test core."""
        print(Fore.BLUE + "Testing Core Commands..." + Style.RESET)
        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")

        obj_top = vobj.VObject(".")
        self.assertEqual(
            sorted(obj.invariant_path() for obj in obj_top.sub_objects()),
            sorted(['tasks', 'includes', 'code'])
        )

        obj_includes = vobj.VObject("includes")
        self.assertEqual(
            sorted(obj.invariant_path() for obj in obj_includes.sub_objects()),
            sorted(['includes/inc', 'includes/inc2'])
        )

        obj_task1 = vobj.VObject("tasks/taskAna2")
        self.assertEqual(obj_task1.sub_objects(), [])

        obj_folder = vobj.VObject("tasks")

        # Extract status from tuple for copy_to_check
        status, _ = obj_folder.copy_to_check("tasksDuplicate")
        self.assertTrue(status)

        status, _ = obj_folder.copy_to_check("tasks")
        self.assertFalse(status)

        status, _ = obj_folder.copy_to_check("includes")
        self.assertFalse(status)

        obj_folder.copy_to("tasksDuplicate")

        self.assertIn('tasksDuplicate', [obj.invariant_path() for obj in obj_top.sub_objects()])
        self.assertFalse(vobj.VObject("tasksDuplicate").is_zombie())

        for task in ["taskAna1", "taskAna2", "taskQA", "taskGen"]:
            self.assertTrue(vobj.VObject(f"tasksDuplicate/{task}").is_impressed())

        obj_task1 = vobj.VObject("tasksDuplicate/taskAna1")
        self.assertEqual(
            [obj.invariant_path() for obj in obj_task1.successors()],
            ['tasksDuplicate/taskAna2'],
        )
        # self.assertEqual([obj.invariant_path() for obj in obj_task1.predecessors()],
        #                  ['tasksDuplicate/taskGen'])
        self.assertEqual(
            [obj.invariant_path() for obj in obj_task1.predecessors()],
            ['tasksDuplicate/taskGen', 'code/ana1'],
        )
        vobj.VObject("tasksDuplicate").rm()

        imp_task_ana1 = str(vobj.VObject("tasks/taskAna1").impression())
        imp_task_ana2 = str(vobj.VObject("tasks/taskAna2").impression())
        imp_task_qa = str(vobj.VObject("tasks/taskQA").impression())
        imp_task_gen = str(vobj.VObject("tasks/taskGen").impression())

        # Extract status from tuple for move_to_check
        status, _ = obj_folder.move_to_check("tasks")
        self.assertFalse(status)

        status, _ = obj_folder.move_to_check("tasksMoved")
        self.assertTrue(status)

        obj_folder.move_to("tasksMoved")
        self.assertIn('tasksMoved', [obj.invariant_path() for obj in obj_top.sub_objects()])

        for task, imp in zip(["taskAna1", "taskAna2", "taskQA", "taskGen"],
                             [imp_task_ana1, imp_task_ana2, imp_task_qa, imp_task_gen]):
            self.assertTrue(vobj.VObject(f"tasksMoved/{task}").is_impressed())
            self.assertEqual(str(vobj.VObject(f"tasksMoved/{task}").impression()), imp)

        obj_task1 = vobj.VObject("tasksMoved/taskAna1")
        self.assertEqual(
            [obj.invariant_path() for obj in obj_task1.successors()],
            ['tasksMoved/taskAna2'],
        )
        self.assertEqual(
            sorted(obj.invariant_path() for obj in obj_task1.predecessors()),
            sorted(['tasksMoved/taskGen', 'code/ana1'])
        )

        vobj.VObject("tasksMoved").rm()
        self.assertNotIn("tasksMoved", [obj.invariant_path() for obj in obj_top.sub_objects()])
        self.assertTrue(vobj.VObject("tasksMoved").is_zombie())
        self.assertTrue(vobj.VObject("tasksMoved/taskAna1").is_zombie())
        self.assertTrue(os.path.exists(f".celebi/impressions/{imp_task_ana1}"))
        self.assertEqual(vobj.VObject("code/ana1").successors(), [])

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_init(self):
        """Test init."""
        print(Fore.BLUE + "Testing Init Commands..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")

        obj_top = vobj.VObject(".")
        obj_alg = vobj.VObject("code/ana1")
        obj_tsk = vobj.VObject("tasks/taskAna1")
        obj_err = vobj.VObject("NotExists")

        for obj, name in [
            (obj_top, "."),
            (obj_alg, "code/ana1"),
            (obj_tsk, "tasks/taskAna1"),
            (obj_err, "NotExists"),
        ]:
            self.assertEqual(str(obj), name)
            self.assertEqual(repr(obj), name)
            self.assertEqual(obj.invariant_path(), name)

        self.assertEqual(obj_top.object_type(), "project")
        self.assertEqual(obj_alg.object_type(), "algorithm")
        self.assertEqual(obj_tsk.object_type(), "task")
        self.assertEqual(obj_err.object_type(), "")

        self.assertFalse(obj_top.is_zombie())
        self.assertFalse(obj_alg.is_zombie())
        self.assertFalse(obj_tsk.is_zombie())
        self.assertTrue(obj_err.is_zombie())

        self.assertFalse(obj_top.is_task_or_algorithm())
        self.assertTrue(obj_alg.is_task_or_algorithm())
        self.assertTrue(obj_tsk.is_task_or_algorithm())
        self.assertFalse(obj_err.is_task_or_algorithm())


        self.assertFalse(obj_top.is_task())
        self.assertFalse(obj_alg.is_task())
        self.assertTrue(obj_tsk.is_task())
        self.assertFalse(obj_err.is_task())

        self.assertFalse(obj_top.is_algorithm())
        self.assertTrue(obj_alg.is_algorithm())
        self.assertFalse(obj_tsk.is_algorithm())
        self.assertFalse(obj_err.is_algorithm())

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_move_task_with_external_successors(self):
        """Regression test: moving a single task with external successors.

        Before the fix, this raised:
            Error moving object: list.remove(x): x not in list
        because move_to_deal_with_arcs removed the same arc twice:
        once in the second pass (succ_object.remove_arc_from(obj))
        and again in the third pass (obj.remove_arc_to(succ_object)).
        """
        print(Fore.BLUE + "Testing move task with external successors..." + Style.RESET)
        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")

        # Create a destination directory (use distinct name to avoid
        # case-insensitive filesystem conflicts with existing 'tasks/')
        os.makedirs("Moved/.celebi", exist_ok=True)
        with open("Moved/.celebi/config.json", "w", encoding="utf-8") as f:
            f.write('{"object_type": "directory"}')

        # Impress all tasks so move_to is allowed
        for task in ["tasks/taskGen", "tasks/taskAna1", "tasks/taskAna2", "tasks/taskQA"]:
            vobj.VObject(task).impress()

        obj_task_gen = vobj.VObject("tasks/taskGen")
        # taskGen has successors taskAna1 and taskAna2, which will be
        # external after moving taskGen into Moved/
        self.assertEqual(
            sorted(obj.invariant_path() for obj in obj_task_gen.successors()),
            sorted(["tasks/taskAna1", "tasks/taskAna2"])
        )

        # This must not raise
        result = obj_task_gen.move_to("Moved/taskGen")
        self.assertFalse(result.messages)  # No error messages

        # Verify the new object exists
        self.assertFalse(vobj.VObject("Moved/taskGen").is_zombie())

        # Verify external successors now point to the new location
        obj_new = vobj.VObject("Moved/taskGen")
        self.assertEqual(
            sorted(obj.invariant_path() for obj in obj_new.successors()),
            sorted(["tasks/taskAna1", "tasks/taskAna2"])
        )

        # Verify external predecessors still point correctly
        self.assertEqual(
            sorted(obj.invariant_path() for obj in obj_new.predecessors()),
            sorted(["code/gen"])
        )

        # Verify the old location is gone
        self.assertTrue(vobj.VObject("tasks/taskGen").is_zombie())

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call


if __name__ == "__main__":
    unittest.main(verbosity=2)
