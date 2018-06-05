# coding: utf-8

from __future__ import division, print_function, unicode_literals, absolute_import

import os
import unittest

from fireworks import Firework, Workflow, FWorker
from fireworks.core.rocket_launcher import rapidfire
from atomate.utils.testing import AtomateTest
from pymatgen.core import Molecule
from pymatgen.io.qchem_io.inputs import QCInput
from pymatgen.io.qchem_io.outputs import QCOutput
from atomate.qchem.powerups import use_fake_qchem
from atomate.qchem.workflows.base.double_FF_opt import get_wf_double_FF_opt
import numpy as np

module_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
db_dir = os.path.join(module_dir, "..", "..", "..", "common", "test_files")

class TestDoubleFFOpt(AtomateTest):

    def test_double_FF_opt(self):
        # location of test files
        test_double_FF_files = os.path.join(module_dir, "..", "..", "test_files", "double_FF_wf")
        # define starting molecule and workflow object
        initial_qcin = QCInput.from_file(os.path.join(test_double_FF_files, "block", "launcher_first", "mol.qin.opt_0"))
        initial_mol = initial_qcin.molecule

        real_wf = get_wf_double_FF_opt(molecule=initial_mol, pcm_dielectric=10.0, max_cores=32, qchem_input_params={"basis_set": "6-311++g**", "overwrite_inputs":{"rem": {"sym_ignore": "true"}}})
        # use powerup to replace run with fake run
        ref_dirs = {"first_FF_no_pcm": os.path.join(test_double_FF_files, "block", "launcher_first"),
                    "second_FF_with_pcm": os.path.join(test_double_FF_files, "block", "launcher_second")}
        fake_wf = use_fake_qchem(real_wf, ref_dirs)
        self.lp.add_wf(fake_wf)
        rapidfire(self.lp, fworker=FWorker(env={"db_file": os.path.join(db_dir, "db.json")}))

        wf_test = self.lp.get_wf_by_fw_id(1)
        self.assertTrue(all([s == 'COMPLETED' for s in wf_test.fw_states.values()]))

        first_FF = self.get_task_collection().find_one({"task_label": "first_FF_no_pcm"})
        self.assertEqual(first_FF["calcs_reversed"][0]["input"]["solvent"],None)
        self.assertEqual(first_FF["num_frequencies_flattened"],1)
        first_FF_final_mol = Molecule.from_dict(first_FF["output"]["optimized_molecule"])
        
        second_FF = self.get_task_collection().find_one({"task_label": "second_FF_with_pcm"})
        self.assertEqual(second_FF["calcs_reversed"][0]["input"]["solvent"],{"dielectric": "10.0"})
        self.assertEqual(second_FF["num_frequencies_flattened"],1)
        second_FF_initial_mol = Molecule.from_dict(second_FF["input"]["initial_molecule"])

        self.assertEqual(first_FF_final_mol, second_FF_initial_mol)


if __name__ == '__main__':
    unittest.main()