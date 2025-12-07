import os
import unittest
from colored import Fore, Style
import CelebiChrono.kernel.vobject as vobj
from CelebiChrono.kernel.chern_cache import ChernCache
import prepare

CHERN_CACHE = ChernCache.instance()


class TestChernProject(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.cwd)

    def test_impression(self):
        print(Fore.BLUE + "Testing impression..." + Style.RESET)

        print("#1 Test whether the change could be identified.")
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        obj_gen = vobj.VObject("Gen")
        obj_genTask = vobj.VObject("GenTask")
        obj_fit = vobj.VObject("Fit")
        obj_fitTask = vobj.VObject("FitTask")

        self.assertFalse(obj_gen.is_impressed())
        self.assertFalse(obj_genTask.is_impressed())
        self.assertTrue(obj_fit.is_impressed())
        self.assertFalse(obj_fitTask.is_impressed())

        self.assertEqual(obj_gen.status(), "new")
        self.assertEqual(obj_genTask.status(), "new")
        self.assertEqual(obj_fit.status(), "impressed")
        self.assertEqual(obj_fitTask.status(), "new")

        self.assertEqual(str(obj_fit.impression()), "7d70b48cea88412791a48e8996cf365e")
        self.assertEqual(str(obj_gen.impression()), "8927389570404d57a9efb6a202b4c065")


        os.chdir("..")
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()

        print("#2 Test whether the impression could be done.")
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        obj_gen = vobj.VObject("Gen")
        obj_genTask = vobj.VObject("GenTask")
        obj_fit = vobj.VObject("Fit")
        obj_fitTask = vobj.VObject("FitTask")
        obj_fitTask.impress()

        self.assertEqual(obj_gen.status(), "impressed")
        self.assertEqual(obj_genTask.status(), "impressed")
        self.assertEqual(obj_fit.status(), "impressed")
        self.assertEqual(obj_fitTask.status(), "impressed")

        self.assertTrue(obj_gen.is_impressed_fast())
        self.assertTrue(obj_genTask.is_impressed_fast())
        self.assertTrue(obj_fit.is_impressed_fast())
        self.assertTrue(obj_fitTask.is_impressed_fast())

        self.assertTrue(obj_gen.is_impressed())
        self.assertTrue(obj_genTask.is_impressed())
        self.assertTrue(obj_fit.is_impressed())
        self.assertTrue(obj_fitTask.is_impressed())

        list1 = [str(x) for x in obj_fitTask.pred_impressions()]
        list2 = [str(x) for x in sorted([obj_fit.impression(), obj_genTask.impression()], key=lambda x: x.uuid)]
        self.assertEqual(list1, list2)

        os.chdir("..")
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()

    def test_clean(self):
        print(Fore.BLUE + "Testing Clean Commands..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        obj_gen = vobj.VObject("Gen")
        obj_genTask = vobj.VObject("GenTask")
        obj_fit = vobj.VObject("Fit")
        obj_fitTask = vobj.VObject("FitTask")
        obj_fitTask.impress()

        obj_fitTask.clean_impressions()
        self.assertEqual(obj_gen.status(), "impressed")
        self.assertEqual(obj_genTask.status(), "impressed")
        self.assertEqual(obj_fit.status(), "impressed")
        self.assertEqual(obj_fitTask.status(), "new")

        os.chdir("..")
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()

    def test_alias(self):
        print(Fore.BLUE + "Testing Alias Commands..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        obj_gen = vobj.VObject("Gen")
        obj_genTask = vobj.VObject("GenTask")
        obj_fit = vobj.VObject("Fit")
        obj_fitTask = vobj.VObject("FitTask")
        # obj_fitTask.impress()

        self.assertEqual([x for x in obj_fitTask.get_alias_list()], ['gen'])
        self.assertEqual(obj_fitTask.alias_to_path("gen"), "GenTask")
        self.assertEqual(obj_fitTask.path_to_alias("GenTask"), "gen")
        self.assertEqual(str(obj_fitTask.alias_to_impression("gen")), "539d17968ab344e5ade4638c232bd29f")
        self.assertTrue(obj_fitTask.has_alias("gen"))
        self.assertFalse(obj_fitTask.has_alias("non_existing_alias"))

        obj_fitTask.set_alias("new_alias", "GenTask")
        self.assertEqual([x for x in obj_fitTask.get_alias_list()], ['gen'])
        obj_fitTask.remove_alias("gen")
        self.assertEqual([x for x in obj_fitTask.get_alias_list()], [])
        obj_fitTask.set_alias("new_alias", "GenTask")
        self.assertEqual([x for x in obj_fitTask.get_alias_list()], ['new_alias'])

        os.chdir("..")
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()

    def test_arc_management(self):
        print(Fore.BLUE + "Testing Arc Management Commands..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        obj_gen = vobj.VObject("Gen")
        obj_genTask = vobj.VObject("GenTask")
        obj_fit = vobj.VObject("Fit")
        obj_fitTask = vobj.VObject("FitTask")

        self.assertTrue(obj_fitTask.has_predecessor(obj_genTask))
        self.assertTrue(obj_fitTask.has_predecessor_recursively(obj_gen))
        self.assertTrue(obj_genTask.has_successor(obj_fitTask))
        self.assertFalse(obj_fitTask.has_predecessor(obj_gen))

        obj_fitTask.remove_input("gen")
        CHERN_CACHE.__init__()

        self.assertFalse(obj_fitTask.has_predecessor(obj_genTask))
        self.assertFalse(obj_fitTask.has_predecessor_recursively(obj_gen))
        self.assertFalse(obj_genTask.has_successor(obj_fitTask))
        self.assertFalse(obj_fitTask.has_predecessor(obj_gen))

        os.chdir("..")
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()

    def test_execution(self):
        print(Fore.BLUE + "Testing Execution Commands..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        obj_gen = vobj.VObject("Gen")
        obj_genTask = vobj.VObject("GenTask")
        obj_fit = vobj.VObject("Fit")
        obj_fitTask = vobj.VObject("FitTask")

        os.chdir("..")
        prepare.remove_chern_project("demo_genfit_new")
        CHERN_CACHE.__init__()

    def test_core(self):
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
        self.assertEqual([obj.invariant_path() for obj in obj_task1.successors()], ['tasksDuplicate/taskAna2'])
        # self.assertEqual([obj.invariant_path() for obj in obj_task1.predecessors()], ['tasksDuplicate/taskGen'])
        self.assertEqual([obj.invariant_path() for obj in obj_task1.predecessors()], ['tasksDuplicate/taskGen', 'code/ana1'])
        vobj.VObject("tasksDuplicate").rm()

        imp_taskAna1 = str(vobj.VObject("tasks/taskAna1").impression())
        imp_taskAna2 = str(vobj.VObject("tasks/taskAna2").impression())
        imp_taskQA = str(vobj.VObject("tasks/taskQA").impression())
        imp_taskGen = str(vobj.VObject("tasks/taskGen").impression())

        # Extract status from tuple for move_to_check
        status, _ = obj_folder.move_to_check("tasks")
        self.assertFalse(status)

        status, _ = obj_folder.move_to_check("tasksMoved")
        self.assertTrue(status)

        obj_folder.move_to("tasksMoved")
        self.assertIn('tasksMoved', [obj.invariant_path() for obj in obj_top.sub_objects()])

        for task, imp in zip(["taskAna1", "taskAna2", "taskQA", "taskGen"],
                             [imp_taskAna1, imp_taskAna2, imp_taskQA, imp_taskGen]):
            self.assertTrue(vobj.VObject(f"tasksMoved/{task}").is_impressed())
            self.assertEqual(str(vobj.VObject(f"tasksMoved/{task}").impression()), imp)

        obj_task1 = vobj.VObject("tasksMoved/taskAna1")
        self.assertEqual([obj.invariant_path() for obj in obj_task1.successors()], ['tasksMoved/taskAna2'])
        self.assertEqual(
            sorted(obj.invariant_path() for obj in obj_task1.predecessors()),
            sorted(['tasksMoved/taskGen', 'code/ana1'])
        )

        vobj.VObject("tasksMoved").rm()
        self.assertNotIn("tasksMoved", [obj.invariant_path() for obj in obj_top.sub_objects()])
        self.assertTrue(vobj.VObject("tasksMoved").is_zombie())
        self.assertTrue(vobj.VObject("tasksMoved/taskAna1").is_zombie())
        self.assertTrue(os.path.exists(f".chern/impressions/{imp_taskAna1}"))
        self.assertEqual(vobj.VObject("code/ana1").successors(), [])

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_init(self):
        print(Fore.BLUE + "Testing Init Commands..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")

        obj_top = vobj.VObject(".")
        obj_alg = vobj.VObject("code/ana1")
        obj_tsk = vobj.VObject("tasks/taskAna1")
        obj_err = vobj.VObject("NotExists")

        for obj, name in [(obj_top, "."), (obj_alg, "code/ana1"), (obj_tsk, "tasks/taskAna1"), (obj_err, "NotExists")]:
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
        CHERN_CACHE.__init__()


if __name__ == "__main__":
    unittest.main(verbosity=2)
