#!/usr/bin/env python
"""
    :module: attribute
    :platform: None
    :synopsis: This module tests the model.py module
    :plans:
"""
__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"
__version__ = 1.0
#mpcSave_contextManager
import unittest
from save import model

class TestSceneFile(unittest.TestCase):

    def setUp(self):
        self.fixtures=[]

    def tearDown(self):
        for fixture in self.fixtures:
            del fixture
    
    def testSceneFile_from_existing(self):
        """ Tests _findVersion, _findDiscipline, and _findUser all in one
        """
        self.assertEqual(model.SceneFile.from_existing("this_483_is_a_t_v493_est_v34322_lookdev_dsfiv39lename_v1032_aw.asdf").__str__(),
                          "this_483_is_a_t_v493_est_v34322_lookdev_dsfiv39lename, 1032, LOOKDEV, aw")
        self.assertEqual(model.SceneFile.from_existing("94_this_is_a_test_dsf_38493_ilename_1032_cr.mb").__str__(),
                          "94_this_is_a_test_dsf_38493_ilename, 1032, MDL, cr")
        self.assertEqual(model.SceneFile.from_existing("43_this_is_a_test_43_dsfilename_1032_dk.ma").__str__(),
                          "43_this_is_a_test_43_dsfilename, 1032, MDL, dk")
        self.assertEqual(model.SceneFile.from_existing("this_is_a_test_48290_dsfilename_1032.fml").__str__(),
                          "this, 1032, MDL, is")
        self.assertEqual(model.SceneFile.from_existing("this_is_a_test_29547_dsfilename_V1032.fum").__str__(),
                          "this, 1032, MDL, is")
        self.assertEqual(model.SceneFile.from_existing("testing_crappy_last_3049_349_andWeDidntCare1049.osx").__str__(),
                          "testing_crappy_last_3049, 349, MDL, aw")
        self.assertEqual(model.SceneFile.from_existing("anim_cave.v005.ma").__str__(),
                          "anim, 5, ANIM, aw")
        self.assertEqual(model.SceneFile.from_existing("mpc_human_rig_v02_jf.mb").__str__(),
                          "mpc_human_rig, 2, RIG, jf")
        self.assertEqual(model.SceneFile.from_existing("SBN_SOC_EarthANIM_013_ac.aep").__str__(),
                          "SBN_SOC, 13, ANIM, ac")
        self.assertEqual(model.SceneFile.from_existing("macys_PV_020_fx_v006.mb").__str__(),
                          "macys, 6, FX, pv")
        self.assertEqual(model.SceneFile.from_existing("Also_checkfor_no_result_stupid_4v9320_03v93_3942djf39_39fk_.fbx").__str__(),
                          "Also_checkfor, 1, MDL, no")
    
    def testSceneFile_from_existing_description(self):
        self.assertEqual(model.SceneFile.from_existing('char_jellyfish_puffHeadA_LAYOUT_v05_mn_test.ma').__str__(),
                         "char_jellyfish_puffHeadA, 5, LAYOUT, mn")
        self.assertEqual(model.SceneFile.from_existing('v01_brian_aw_LAYOUT.mc').__str__(),
                         "untitled, 1, LAYOUT, aw")
        
    def testSceneFile_findExt_existing(self):
        self.assertEqual(model.SceneFile._findExt('test'),'ma')

    def testSceneFile_findExt_not_existing_default(self):
        self.assertEqual(model.SceneFile._findExt('test.mb'),'mb')

    def testSceneFile_increment_version_default_increment(self):
        dir = model.SceneFile.from_existing('macys_PV_020_fx_v006.mb').increment()
        self.assertEqual(dir.version, 7)
        
    def testSceneFile_increment_version_version_input(self):
        dir = model.SceneFile.from_existing('macys_PV_020_fx_v006.mb').increment(5)
        self.assertEqual(dir.version, 5)

class TestDirectory(unittest.TestCase):

    def setUp(self):
        self.fixtures=[]
        #self.mock_contexts = patch('path.to.lib.contexts', Mock(fromEnvironment='test'))
        #self.fixtures.append(self.mock_contexts)
        
    def tearDown(self):
        for fixture in self.fixtures:
            del fixture

    def testDirectory_refresh_tree_scene_ignored(self):
        #Mehhhhhhhhhhhhhhh, don't think this is test-worthy?
        pass

    def testDirectory_refresh_tree_scene_found_list(self):
        #directory = model.Directory().tree_cache={'test_job': {'test_scene01': ['test_shot1','test_shot2'], 'test_scene02': []}}
        #self.assertEquals(directorytree_cache,
        #                  {'test_job': {'test_scene01': ['test_shot1','test_shot2'], 'test_scene02': []}})
        pass
        
    def testDirectory_refresh_tree_scene_found_no_list(self):
        pass
        #self.assertEquals(Directory().refresh_tree(), [])

if __name__ == '__main__':
    unittest.main()
