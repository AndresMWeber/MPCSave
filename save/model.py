#!/usr/bin/env python
"""
    :module: model
    :platform: None
    :synopsis: This module contains classes related to env path and file handling
    :plans:
"""
__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"
__version__ = 1.0

# Default Imports
import getpass as gp
import re
import sys
import os 
from glob import glob
from pprint import pprint
from ConfigParser import SafeConfigParser
# MPC Imports
from mpc.tessa import contexts

# Relative Path Config Setup
__location__ =  os.path.dirname(os.path.realpath(__file__))
__config__ = os.path.join(__location__, "config.ini")
try:
    parser = SafeConfigParser()
    parser.optionxform = str
    parser.read(__config__)
    config = {}
    for section in parser.sections():
        config[section]={}
        for sub_item, value in parser.items(section):
            config[section][sub_item] = value if ',' not in value else value.split(',')
    root = config['map']['server']
except KeyError as err:
    print err
    raise IOError("File not found %s"%__config__)


class SaveData(object):
    """ Class putting together all the data and interfacing with the UI
    Usage:
        a = SaveData('/jobs/macysSanta_5403623/build/char_santa_balloon/maya/scenes/model/tester.ma')
        a.dir.get_job()
        b = SaveData('/jobs/sourPatchKidsGumAndSlurpee_5600273/build/char_spk_amputee/maya/scenes/model/RELEASE/char_spk_amputee_lodA/v003/char_spk_amputee_lodA.ma')
        b.scene_file
        b.dir
    """
    def __init__(self, input_filepath):
        self.input_folder = os.path.dirname(input_filepath)
        self.input_file = os.path.basename(input_filepath)
        
        self.is_new_file = 1 if input_filepath == '' else 0
        self.username = gp.getuser()
        
        self.dir = Directory(input_filepath)
        self.scene_file = SceneFile(self.input_file)
        
    def get_filename(self):
        """ Returns the current iteration of the SceneFile object's name
        """
        template_string_copy = config['path']['template_string']
        
        if self.scene_file.optional == None:
            template_string_copy = template_string_copy.replace( '_{OPTIONAL}', '' )
        
        self.filename = template_string_copy.format( DESCRIPTION = self.scene_file.description,
                                                     DISCIPLINE  = self.scene_file.discipline,
                                                     VERSION     = '%03d' % self.scene_file.version,
                                                     INITIALS    = self.scene_file.initials,
                                                     OPTIONAL    = self.scene_file.optional,
                                                     EXT         = self.scene_file.extension)
        return self.filename
    
    def _get_discipline_folder(self):
        """ Builds the final directory for the scene file's current discipline
        """
        dir = config['discipline_LUT'][self.scene_file.discipline]
        if dir in config['map']['rig_disciplines']:
            dir = os.path.join('rig',dir)
        return config['path']['template_discipline_folder'].format(dir)


class Directory(object):
    """ Use this class to query the path values
    Usage: 
        a = Directory()
        print a
        a.tree_cache
        a.get_scenes()
        a.get_shots('build')
        a.set_cur_dir(scene='shots',shot='sh01')
        a.set_cur_dir(shot='does_not_exist')
        a.validate()
        a = Directory('/jobs/sourPatchKidsGumAndSlurpee_5600273/build/char_spk_amputee/maya/scenes/model/RELEASE/char_spk_amputee_lodA/v003/char_spk_amputee_lodA.ma')
        print a
    """
    
    def __init__(self, context_in=None):
        """ init
        Args:
            context_in (dict or str): dictionary for contexts or path string.  Leave None to source from environment
        """
        if isinstance(context_in, str):
            parse_values = self._parse_path(context_in)
            job_context = dict.fromkeys(['job','scene','shot'],None)
            for index, key in enumerate(job_context.keys()):
                try:
                    job_context[key] = parse_values[index]
                except:
                    pass
            self.context = contexts.contextFactory(job_context)
        elif isinstance(context_in, dict):
            self.context = contexts.contextFactory(context_in)
        else:
            self.context = contexts.fromEnvironment()
        
        self.tree_cache = {}
        self.refresh_tree()

    def set_cur_dir(self, job=None, shot=None, scene=None, from_dict=None):
        """ Sets the current directory from any of: job/shot/scene OR using a dictionary following the tessa format
            If you provide a shot that is not currently in the context's scene you need to provide the destination scene
        Returns (boolean): True - if we have changed and validated the target path 
                           False - if we had to revert back if the path doesn't exist
        """
        orig_context = self.context

        if from_dict:
            self.context = contexts.Shot.fromDict(from_dict)
        else:
            cur_context = dict(self.context)
            cur_context['job'] = job or cur_context['job']
            cur_context['shot'] = shot or cur_context['shot']
            cur_context['scene'] = scene or cur_context['scene']
            self.context = contexts.Shot.fromDict(cur_context)
        if not self.validate():
            self.context = orig_context
            return False
        else:
            return True
            
    def get_job(self):
        return self.context.job
    
    @staticmethod
    def get_jobs():
        return [path.replace('/%s/' % root,'')
                for path in glob('/%s/*' % root)]
    
    def get_shots(self, scene_name, filter=[]):
        """ Simple query for list of shots in the current cached tree's specified scene
        Args:
            scene_name (str): scene to be queried
            filter [str]: list of names to filter out
        Returns [str] or None: list of strings for shot names or None if scene wasn't found in current tree cache
        """
        filter += config['map']['shot_ignore_list']
        if scene_name in self.tree_cache[self.context.job.name].keys():
            return [shot for shot in self.tree_cache[self.context.job.name][scene_name] if shot not in filter]
        else:
            return None
    
    def get_scenes(self, filter=[]):
        """ Simple query for list of scenes in the current cached tree
        Args:
            filter [str]: list of names to filter out
        Returns [str] or None: list of strings for shot names or None if scene wasn't found in current tree cache
        """
        filter += config['map']['scene_ignore_list']
        return [scene for scene in self.tree_cache[self.context.job.name].keys() if scene not in filter]
        
    def refresh_tree(self):
        """ Gives us a dictionary tree with which we can browse the current job's structure
        Args (None)
        Returns (dict): dictionary of the tree
        """
        job = self.context.job
        self.tree_cache = {}
        self.tree_cache[job.name] = {}
        for scene in job.findChildren():
            if scene.name not in config['map']['scene_ignore_list']:
                self.tree_cache[job.name][scene.name]=[]
                for shot in scene.findChildren():
                    self.tree_cache[job.name][scene.name].append(shot.name)
        return self.tree_cache
    
    def build_path(self):
        """ Builds a hardlink path to the current context
        """
        return config['path']['path_format_string'].format(JOB=self.context.job.name,SCENE=self.context.scene.name,SHOT=self.context.shot.name)
    
    def validate(self):
        """ Checks whether the currently set directory exists
        """
        return contexts.validateContext(self.context)
        
    @staticmethod
    def _parse_path(file_path):
        """ Takes an input filepath and separates the first three paths assuming they are (job)/(sequence)/(shot)
        Args:
            file_path (str): input filepath
        Returns [str]: list of strings length 3 that has the first three directories (MPC style)
        """
        folders = [folder for folder in file_path.split('/') if folder != '' and folder != root]
        return folders[:3]
    
    def __repr__(self):
        pprint(self.tree_cache)
        return 'Current path is %s' % self.build_path()


class SceneFile(object):
    """ This class will store all information relating to your scene file
    """
    
    def __init__(self, description=None, discipline=None, version=None, user=None, optional=None, extension=None):
        self.description = description or config['defaults']['description']
        self.discipline = discipline or config['defaults']['discipline']
        self.version = version or config['defaults']['version']
        self.optional = optional or None
        self.user = user or (gp.getuser()[0] + gp.getuser().split('-')[-1][0])
        self.extension = extension or config['defaults']['extension']

    def increment(self, version=None, step=1):
        """ Increments the version by adding the step value to the current version or sets to a specific user entered version
        Args:
            version (int): specific version to override
            step (int): Value to increment by
        Returns (int): new value for self.version
        """
        if version == None:
            self.version += step
        else:
            self.version = version
        return self
    
    @classmethod
    def from_existing(cls, filename):
        """ Scours the previous file's name for: version number, last user, and discipline
        Args:
            filename (str): filename...
        Returns (SceneFile): scene file node from the init.
        """
        version = max(cls._findVersion(filename), 1)
        user = cls._findUser(filename)
        discipline = cls._findDiscipline(filename)
        description = cls._findDescription(filename, str(version), user, discipline)
        return cls(description=description, version=version, user=user, discipline=discipline)

    @classmethod
    def _findDiscipline(cls, filename):
        """ Case insensitive search for any of the discipline shorthands
        Args:
            filename (str): filename to check
        Returns (str): string for the discipline found or empty string
        """
        discipline_matches = re.findall('(?i)'+('|'.join(config['map']['disciplines'])), filename)
        if discipline_matches:
            return discipline_matches[-1].upper()
        return ""
    
    @classmethod
    def _findUser(cls, filename):
        """ Currently scours a filename for something like _aw_ and returns it assuming it's the username
        Args:
            filename (str): filename to check
        Returns (str): string for the discipline found or empty string
        """
        match = [match for match in re.findall(config['regex']['username'], filename)
                 if match.upper() not in config['map']['disciplines']]
        if match:
            return match[-1].lower()
        return ""
    
    @classmethod
    def _findVersion(cls, filename):
        """ Currently scours a filename for v##...n or just numbers and returns it
            Tests for best case scenario first, v before flat numbers
        Args:
            filename (str): filename to check
        Returns (int): value of version found or -1 for no version found
        """
        result, found = -1, False
        
        match = re.findall(config['regex']['leading_v'], filename)
        if match and not found:
            result, found = match[-1], True
        
        match = [find for find in re.findall(config['regex']['only_numbers'], filename) if find != '']
        if match and not found:
            result, found = match[-1], True
        
        return int(result)
    
    @classmethod
    def _findExt(cls, filename):
        """ Finds the extension of a filename with '.' stripped
        Args:
            filename (str): filename...
        Returns (str): file extension or ma as default
        """
        default = config['defaults']['extension']
        if not filename:
            return default
        else:
            return os.path.splitext(filename)[-1].replace('.','') or default
    
    @classmethod
    def _findDescription(cls, filename, version, user, discipline):
        """ Given we have found version/username/disciplines we can assume everything preceeding
            these will be the description of the file and return that.
        Args:
            filename (str): input filename
            version (str): string of the version number
            discipline (str): string of the discipline
        Returns (str): string for the description or "untitiled"
        """ 
        default = config['defaults']['description']
        indices = [filename.rfind(user), filename.rfind(version), filename.rfind(discipline)]        
        upper_indices = [filename.rfind(user.upper()), filename.rfind(version.upper()), filename.rfind(discipline.upper())]
        min_index = min([index for index in indices + upper_indices if index > 0])
        try:
            separator_index = min([index for index 
                                   in [filename[0:min_index].rfind('.'), filename[0:min_index].rfind('_')] 
                                   if index > 0])
            return filename[:separator_index]
        except ValueError as err:
            return default
        except TypeError as err:
            return default
        
    def __repr__(self):
        """ Returns the representation of its current contents separated by comma
        """
        return ', '.join([self.description, str(self.version), self.discipline, self.user])
    
    def __str__(self):
        """ Returns the string value of its current contents separated by comma        
        """
        return ', '.join([self.description, str(self.version), self.discipline, self.user])