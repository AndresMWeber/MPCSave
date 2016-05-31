#!/usr/bin/env python
"""
    :module: view
    :platform: Maya 2012-2016
    :synopsis: This is a GUI that saves a new version of your scene file and automates naming
    :plans:
    	1.  Set it up so that it parses .mb/.ma to start with
    	2.  Needs file browser for changing root folder
    	3.  Also needs appending to existing version collections
"""
__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"
__version__ = 1.0
__updated__ = "2016_05_27"

import pymel.core as pm
import string
import getpass as gp
import maya.cmds as cmds
import maya.mel as mel
import sys as sys
import os

# importing the colors module
from aw.maya.env import aw_windows as wind
import save.model as model
reload(wind)
reload(model)


class MPCSaveUI(object):
    def __init__(self):        
        #VAR SETUP#
        self.save_data = model.saveData(os.path.abspath(cmds.file(q=True, sn=True)))
        
        self._setupUI()
    
    def _setupUI(self):
        #UI SETUP#
        title='AW_Save_Plus'
        self.go_green_cl=[.1,.4,.2]
        self.title_blue_cl=[.1,.15,.2]
        self.go_yellow_cl=[0.947, 0.638, 0.130]
        if(pm.windowPref(title, q=True, ex=True)):
            pm.windowPref(title, remove=True)
        if(pm.window(title, q=True,ex=True)):
            pm.deleteUI(title)
        self.window = pm.window(title,t=title, w=890, h=105)
        
        self.fl = pm.formLayout()
        self.title_tx = pm.symbolButton(image='save_105.png', w=105, h=105)
        self.col = pm.columnLayout(p=self.fl)
        pm.text(l='Saving to Directory:', fn='boldLabelFont')
        self._updateFile(False)
        self.filePath_tx = pm.text('filePath_tx', l=self.file)
        pm.text(l='')
        self.header = pm.text('header_tf',fn='boldLabelFont', l='Filename')
        self.origFile_om = wind.AW_optionMenu(label='', options=['Original Folder', 'Auto-detect'], parent=self.col, cc=self._changeOrigFolder_om)
        if self.save_data.dir.is_new_file: self.origFile_om.setSelect(2)
        
        self.layout = pm.formLayout(nd=100)
        
        self.fileDescr_tf = pm.textField('fileDescr_tf',text=self.fileDescr, p=self.layout, w=200, cc=self._changeFileDescr)
        self.discipline_om = wind.AW_optionMenu(label='_', options=self.disciplines, parent=self.layout, cc=self._changeDiscipline)
        self.spacer = pm.text(l='_v', p=self.layout,w=10)
        self.version_tf = pm.textField('version_tf',text='%03d'%self.version, p=self.layout, w=30, cc= self._changeVersionNumber)
        self.versionOptional_om = wind.AW_optionMenu(label='', options=['']+list(string.lowercase), parent=self.layout, cc=self._changeVersionOptional_om)
        self.optionalNote_tf = pm.textField('optionalNote_tf', text='(optional note)', p=self.layout, w=150, cc=self._changeOptionalNoteTx)
        self.type = wind.AW_optionMenu(label='_', options=['.ma','.mb'], parent=self.layout, cc=self._changeType_om)
        if self.initialFileType=='ma': self.type.setSelect(1)
        if self.initialFileType=='mb': self.type.setSelect(2)
        self.save_btn = pm.button(label='Save', command=self._save,h=20, bgc=self.go_yellow_cl)

        pm.formLayout(self.layout, e=True, af=[(self.fileDescr_tf, 'left', 0),
                                               (self.spacer,'top',5)],
                                               ac=[(self.discipline_om.optionMenu, 'left',5, self.fileDescr_tf),
                                                   (self.spacer, 'left',5, self.discipline_om.optionMenu),
                                                   (self.version_tf, 'left',5, self.spacer),
                                                   (self.versionOptional_om.optionMenu, 'left',5,self.version_tf),
                                                   (self.optionalNote_tf, 'left',5,self.versionOptional_om.optionMenu),
                                                   (self.type.optionMenu, 'left',5,self.optionalNote_tf),
                                                   (self.save_btn, 'left',5,self.type.optionMenu)])
        pm.formLayout(self.fl, e=True, af=[(self.col, 'top', 10)], ac=[(self.col, 'left',10, self.title_tx)])
        
        self._setVersionOption(self.versionOption_startup)
        self._getDiscipline()
        self._updateFilename()
        self._updateFilePathTx()
        
        self.window.show()
    
    
    def _save(self, *args):
        """Saves the file from self.file."""
        self._updateFilename()
        if self.origFile_om.getSelect()==1: self._updateFile(True)
        else: self._updateFile(False)
        self._updateFilePathTx()
        print 'Saving as new file:\n%s' % (self.file)        
        
        #creating the user dir if it doesn't exist
        if not os.path.exists(os.path.dirname(self.file)):
            os.makedirs(os.path.dirname(self.file))
        
        #save the file
        cmds.file( rn=self.file )
        cmds.file( f=True, s=True, type = self.fileType[self.type.getSelect()-1] )
        
        if self.type.getSelect(str=True) == '.mb':
            mel.eval('catch(`addRecentFile "%s" "%s"`);' % (self.file, "mayaBinary"))
        elif self.type.getSelect(str=True) == '.ma':
            mel.eval('catch(`addRecentFile "%s" "%s"`);' % (self.file, "mayaAscii"))
        self._close()
                    
    
 
    def _updateFilename(self):
        """Updates the filename with latest internal vars.
        Returns: str
        """
        if self.fileDescr == '': pm.error("You need to enter a file description")
        
        #Checking whether or not to append an optional note to the filename formatter
        self.optionalNote = self.optionalNote_tf.getText()
        optional = self.optionalNote
        if optional == '(optional note)':
            optional = None
        
        self._formatFilename(self.fileDescr,
                             self.discipline_om.getSelect(str=True),
                             'v%s' % str(self.version_tf.getText() + str(self.versionOptional_om.getSelect(str=True)) ),
                             self.initials,
                             self.type.getSelect(str=True),
                             optional = optional)
        
        if self.origFile_om.getSelect()==1: self._updateFile(True)
        else: self._updateFile(False)
        
        return self.filename
    
    

    def _updateFile( self, origFolder ):
        """Updates self.file with the most recent internal vars + formats it as an os.path type.
        returns os.path
        """
        file_result = os.path.join( self.folder_project, self.folder_discipline, self.username, self.filename )
        if origFolder:
            file_result = os.path.join( self.origFolder,  self.filename )
        self.file = file_result
        return file_result
                                 
    def _setDiscipline(self, discipline, *args):
        """Updates self.folder_discipline with the selected discipline path."""
        self.discipline_om.setSelect(self.disciplines.index(discipline)+1)
        self._updateFilename()
        self._updateFilePathTx()
    
    def _setVersionOption(self, option, *args):
        self.versionOptional_om.setSelect(self.versionOption_startup)
        self._updateFilename()
        self._updateFilePathTx()
    
    def _changeVersionNumber(self, *args):
        """Updates the file path textField onChange of discipline_om."""
        self.version=self.version_tf.getText()
        self._updateFilename()
        self._updateFilePathTx()
        
    def _changeDiscipline(self, *args):
        """Updates the file path textField onChange of discipline_om."""
        self._setDiscipline(self.discipline_om.getSelect(str=True))
        self._updateFilePathTx()
        
    def _changeOptionalNoteTx(self, *args):
        """Updates the file path textField onChange of optionalNote_tx."""
        self.optionalNote = self.optionalNote_tf.getText()
        self._updateFilename()
        self._updateFilePathTx()
    
    def _changeVersionOptional_om(self, *args):
        """Updates the file path textField onChange of versionOptional_om."""
        self._updateFilename()
        self._updateFilePathTx()
        
    def _changeType_om(self, *args):
        """Updates the file path textField onChange of type_om."""
        self._updateFilename()
        self._updateFilePathTx()
    
    def _changeOrigFolder_om(self, *args):
        """Updates the file path to the original folder onChange of changeOrigFolder_om"""
        self._updateFilename()
        self._updateFilePathTx()
        
    def _changeFileDescr(self, *args):
        """Updates the file path textField onChange of fileDescr_tf."""
        self.fileDescr = "_".join( self.fileDescr_tf.getText().split(" ") )
        self._updateFilename()
        self._updateFilePathTx()
        
    def _updateFilePathTx(self):
        """Updates the file path textField with latest internal vars."""
        self.filePath_tx.setLabel( self.file )
    
    def _close ( self ):
        """closes the window.  Completely Useless one line function. I hate me."""
        self.window.delete()

if __name__=='__main__':
    ui = MPCSaveUI()