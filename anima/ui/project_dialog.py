# -*- coding: utf-8 -*-
# Copyright (c) 2012-2017, Anima Istanbul
#
# This module is part of anima-tools and is released under the BSD 2
# License: http://www.opensource.org/licenses/BSD-2-Clause
import re

from anima import logger
from anima.ui.base import AnimaDialogBase, ui_caller
from anima.ui import IS_PYSIDE, IS_PYSIDE2, IS_PYQT4
from anima.ui.lib import QtCore, QtWidgets, QtGui


if IS_PYSIDE():
    from anima.ui.ui_compiled import project_dialog_UI_pyside as project_dialog_UI
elif IS_PYSIDE2():
    from anima.ui.ui_compiled import project_dialog_UI_pyside2 as project_dialog_UI
elif IS_PYQT4():
    from anima.ui.ui_compiled import project_dialog_UI_pyqt4 as project_dialog_UI


def UI(app_in=None, executor=None, **kwargs):
    """
    :param app_in: A Qt Application instance, which you can pass to let the UI
      be attached to the given applications event process.

    :param executor: Instead of calling app.exec_ the UI will call this given
      function. It also passes the created app instance to this executor.

    """
    return ui_caller(app_in, executor, MainDialog, **kwargs)


class MainDialog(QtWidgets.QDialog, project_dialog_UI.Ui_Dialog, AnimaDialogBase):
    """The Project Dialog
    """

    def __init__(self, parent=None, project=None):
        logger.debug("initializing the interface")
        super(MainDialog, self).__init__(parent)
        self.setupUi(self)

        # store the logged in user
        self.logged_in_user = None

        self.project = project

        self.mode = 'Create'
        if self.project:
            self.mode = 'Update'

        self.dialog_label.setText('%s Project' % self.mode)

        from anima.ui.models import ValidatedLineEdit
        # add name_lineEdit
        self.name_lineEdit = ValidatedLineEdit(
            message_field=self.name_validator_label
        )
        self.name_fields_verticalLayout.insertWidget(
            0, self.name_lineEdit
        )

        # add code_lineEdit
        self.code_lineEdit = ValidatedLineEdit(
            message_field=self.code_validator_label
        )
        self.code_fields_verticalLayout.insertWidget(
            0, self.code_lineEdit
        )

        self._setup_signals()

        self._set_defaults()

        if self.project:
            self.fill_ui_with_project(self.project)

    def show(self):
        """overridden show method
        """
        logger.debug('MainDialog.show is started')
        self.logged_in_user = self.get_logged_in_user()
        if not self.logged_in_user:
            self.reject()
            return_val = None
        else:
            return_val = super(MainDialog, self).show()

        logger.debug('MainDialog.show is finished')
        return return_val

    def _setup_signals(self):
        """creates the signals
        """
        # name_lineEdit is changed
        QtCore.QObject.connect(
            self.name_lineEdit,
            QtCore.SIGNAL('textChanged(QString)'),
            self.name_line_edit_changed
        )

        # code_lineEdit is changed
        QtCore.QObject.connect(
            self.code_lineEdit,
            QtCore.SIGNAL('textChanged(QString)'),
            self.code_line_edit_changed
        )

        # create_image_format_pushButton
        QtCore.QObject.connect(
            self.create_image_format_pushButton,
            QtCore.SIGNAL('clicked()'),
            self.create_image_format_push_button_clicked
        )

        # update_image_format_pushButton
        QtCore.QObject.connect(
            self.update_image_format_pushButton,
            QtCore.SIGNAL('clicked()'),
            self.update_image_format_push_button_clicked
        )

        # create_repository_pushButton
        QtCore.QObject.connect(
            self.create_repository_pushButton,
            QtCore.SIGNAL('clicked()'),
            self.create_repository_push_button_clicked
        )

        # update_repository_pushButton
        QtCore.QObject.connect(
            self.update_repository_pushButton,
            QtCore.SIGNAL('clicked()'),
            self.update_repository_push_button_clicked
        )

        # create_structure_pushButton
        QtCore.QObject.connect(
            self.create_structure_pushButton,
            QtCore.SIGNAL('clicked()'),
            self.create_structure_push_button_clicked
        )

        # update_structure_pushButton
        QtCore.QObject.connect(
            self.update_structure_pushButton,
            QtCore.SIGNAL('clicked()'),
            self.update_structure_push_button_clicked
        )

    def _set_defaults(self):
        """setup the default values
        """
        # set size policies
        # self.name_lineEdit

        self.type_comboBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )

        self.status_comboBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )

        self.client_comboBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )

        self.agency_comboBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )

        self.production_company_comboBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )

        # invalidate the name and code fields by default
        self.name_lineEdit.set_invalid('Enter a name')
        self.code_lineEdit.set_invalid('Enter a code')

        # update type field
        from stalker import db, Type
        project_types = \
            db.DBSession.query(Type.id, Type.name)\
                .filter(Type.target_entity_type == 'Project')\
                .order_by(Type.name)\
                .all()

        self.type_comboBox.clear()
        self.type_comboBox.addItem('', -1)
        for type_id, type_name in project_types:
            self.type_comboBox.addItem(type_name, type_id)

        self.fill_image_format_combo_box()
        self.fill_repository_combo_box()
        self.fill_structure_combo_box()

        # fill status field
        sql = """select
        "SimpleEntities".id,
        "SimpleEntities".name
    from "Statuses"
    join "SimpleEntities" on "Statuses".id = "SimpleEntities".id
    join "StatusList_Statuses" on "Statuses".id = "StatusList_Statuses".status_id
    join "StatusLists" on "StatusLists".id = "StatusList_Statuses".status_list_id
    where "StatusLists".target_entity_type = 'Project'"""

        all_project_statuses = \
            db.DBSession.connection().execute(sql).fetchall()

        for st_id, st_name in all_project_statuses:
            self.status_comboBox.addItem(st_name, st_id)

    def fill_repository_combo_box(self):
        """fills the repository_comboBox with Repository instances
        """
        # fill the repository field
        from stalker import db, Repository
        all_repos = db.DBSession \
            .query(Repository.id, Repository.name) \
            .order_by(Repository.name) \
            .all()
        self.repository_comboBox.clear()
        for repo_id, repo_name in all_repos:
            self.repository_comboBox.addItem(repo_name, repo_id)

    def fill_structure_combo_box(self):
        """fills the structure_comboBox with Structure instances
        """
        # fill the structure field
        from stalker import db, Structure
        all_structures = db.DBSession \
            .query(Structure.id, Structure.name) \
            .order_by(Structure.name) \
            .all()
        self.structure_comboBox.clear()
        for st_id, st_name in all_structures:
            self.structure_comboBox.addItem(st_name, st_id)

    def fill_image_format_combo_box(self):
        """fills the image_format_comboBox
        """
        # fill the image format field
        from stalker import db, ImageFormat
        all_image_formats = db.DBSession \
            .query(ImageFormat.id, ImageFormat.name, ImageFormat.width,
                   ImageFormat.height) \
            .order_by(ImageFormat.name) \
            .all()
        self.image_format_comboBox.clear()
        for imf_id, imf_name, imf_width, imf_height in all_image_formats:
            imf_text = '%s (%s x %s)' % (imf_name, imf_width, imf_height)
            self.image_format_comboBox.addItem(imf_text, imf_id)

    def name_line_edit_changed(self, text):
        """runs when the name_lineEdit text has changed
        """
        if re.findall(r'[^a-zA-Z0-9\-_ ]+', text):
            self.name_lineEdit.set_invalid('Invalid character')
        else:
            if text == '':
                self.name_lineEdit.set_invalid('Enter a name')
            else:
                self.name_lineEdit.set_valid()

        # update code field also
        formatted_text = re.sub(r'[^A-Z0-9_]+', '', text)
        self.code_lineEdit.setText(formatted_text)

    def code_line_edit_changed(self, text):
        """runs when the code_lineEdit text has changed
        """
        if re.findall(r'[^a-zA-Z0-9_]+', text):
            self.code_lineEdit.set_invalid('Invalid character')
        else:
            if text == '':
                self.code_lineEdit.set_invalid('Enter a code')
            else:
                if len(text) > 16:
                    self.code_lineEdit.set_invalid('Code is too long (>16)')
                else:
                    self.code_lineEdit.set_valid()

    def fill_ui_with_project(self, project):
        """fills the UI fields with the given project

        :param project: A Stalker Project instance
        :return:
        """
        if not project:
            return
        self.project = project

        self.name_lineEdit.setText(project.name)
        self.name_lineEdit.set_valid()
        self.code_lineEdit.setText(project.code)
        self.code_lineEdit.set_valid()

        if project.type:
            index = self.type_comboBox.findData(project.type.id)
            if index:
                self.type_comboBox.setCurrentIndex(index)

        if project.image_format:
            index = self.image_format_comboBox.findData(
                project.image_format.id
            )
            if index:
                self.image_format_comboBox.setCurrentIndex(index)

        self.fps_spinBox.setValue(project.fps)

        if project.repository:
            # TODO: allow multiple repositories
            index = self.repository_comboBox.findText(
                project.repository.name,
                QtCore.Qt.MatchExactly
            )
            if index:
                self.repository_comboBox.setCurrentIndex(index)

        if project.structure:
            index = self.structure_comboBox.findText(
                project.structure.name,
                QtCore.Qt.MatchExactly
            )
            if index:
                self.repository_comboBox.setCurrentIndex(index)

        if project.status:
            index = self.status_comboBox.findText(
                project.status.name,
                QtCore.Qt.MatchExactly
            )
            if index:
                self.status_comboBox.setCurrentIndex(index)

    def create_image_format_push_button_clicked(self):
        """runs when create_image_format_pushButton is clicked
        """
        try:
            # PySide
            accepted = QtWidgets.QDialog.DialogCode.Accepted
        except AttributeError:
            # PyQt4
            accepted = QtWidgets.QDialog.Accepted

        from anima.ui import image_format_dialog
        create_image_format_dialog = \
            image_format_dialog.MainDialog(parent=self)
        create_image_format_dialog.exec_()
        result = create_image_format_dialog.result()

        if result == accepted:
            image_format = create_image_format_dialog.image_format

            # select the created image format
            self.fill_image_format_combo_box()
            index = self.image_format_comboBox.findData(image_format.id)
            if index:
                self.image_format_comboBox.setCurrentIndex(index)

        create_image_format_dialog.deleteLater()

    def update_image_format_push_button_clicked(self):
        """runs when update_image_format_pushButton is clicked
        """
        try:
            # PySide
            accepted = QtWidgets.QDialog.DialogCode.Accepted
        except AttributeError:
            # PyQt4
            accepted = QtWidgets.QDialog.Accepted

        image_format = self.get_current_image_format()

        from anima.ui import image_format_dialog
        update_image_format_dialog = \
            image_format_dialog.MainDialog(parent=self,
                                           image_format=image_format)
        update_image_format_dialog.exec_()
        result = update_image_format_dialog.result()

        if result == accepted:
            image_format = update_image_format_dialog.image_format

            # select the created image format
            self.fill_image_format_combo_box()
            index = self.image_format_comboBox.findData(image_format.id)
            if index:
                self.image_format_comboBox.setCurrentIndex(index)

        update_image_format_dialog.deleteLater()

    def create_repository_push_button_clicked(self):
        """runs when create_repository_pushButton is clicked
        """
        try:
            # PySide
            accepted = QtWidgets.QDialog.DialogCode.Accepted
        except AttributeError:
            # PyQt4
            accepted = QtWidgets.QDialog.Accepted

        from anima.ui import repository_dialog
        create_repository_dialog = \
            repository_dialog.MainDialog(parent=self)
        create_repository_dialog.exec_()
        result = create_repository_dialog.result()

        if result == accepted:
            repository = create_repository_dialog.repository

            # select the created repository
            self.fill_repository_combo_box()
            index = self.repository_comboBox.findData(repository.id)
            if index:
                self.repository_comboBox.setCurrentIndex(index)

        create_repository_dialog.deleteLater()

    def update_repository_push_button_clicked(self):
        """runs when update_repository_pushButton is clicked
        """
        try:
            # PySide
            accepted = QtWidgets.QDialog.DialogCode.Accepted
        except AttributeError:
            # PyQt4
            accepted = QtWidgets.QDialog.Accepted

        repo = self.get_current_repository()
        if not repo:
            return

        from anima.ui import repository_dialog
        update_repository_dialog = \
            repository_dialog.MainDialog(parent=self, repository=repo)
        update_repository_dialog.exec_()
        result = update_repository_dialog.result()

        if result == accepted:
            repository = update_repository_dialog.repository

            # select the created repository
            self.fill_repository_combo_box()
            index = self.repository_comboBox.findData(repository.id)
            if index:
                self.repository_comboBox.setCurrentIndex(index)

        update_repository_dialog.deleteLater()

    def create_structure_push_button_clicked(self):
        """runs when create_structure_pushButton is clicked
        """
        try:
            # PySide
            accepted = QtWidgets.QDialog.DialogCode.Accepted
        except AttributeError:
            # PyQt4
            accepted = QtWidgets.QDialog.Accepted

        from anima.ui import structure_dialog
        create_structure_dialog = \
            structure_dialog.MainDialog(parent=self)
        create_structure_dialog.exec_()
        result = create_structure_dialog.result()

        if result == accepted:
            structure = create_structure_dialog.structure

            # select the created repository
            self.fill_structure_combo_box()
            index = self.structure_comboBox.findData(structure.id)
            if index:
                self.structure_comboBox.setCurrentIndex(index)

        create_structure_dialog.deleteLater()

    def update_structure_push_button_clicked(self):
        """runs when update_structure_pushButton is clicked
        """
        try:
            # PySide
            accepted = QtWidgets.QDialog.DialogCode.Accepted
        except AttributeError:
            # PyQt4
            accepted = QtWidgets.QDialog.Accepted

        structure = self.get_current_structure()
        if not structure:
            return

        from anima.ui import structure_dialog
        update_structure_dialog = \
            structure_dialog.MainDialog(parent=self, structure=structure)
        update_structure_dialog.exec_()
        result = update_structure_dialog.result()

        if result == accepted:
            structure = update_structure_dialog.structure

            # select the created repository
            self.fill_structure_combo_box()
            index = self.structure_comboBox.findData(structure.id)
            if index:
                self.structure_comboBox.setCurrentIndex(index)

        update_structure_dialog.deleteLater()

    def get_current_image_format(self):
        """returns the currently selected image format instance from the UI
        """
        from stalker import ImageFormat
        index = self.image_format_comboBox.currentIndex()
        image_format_id = self.image_format_comboBox.itemData(index)
        image_format = ImageFormat.query.get(image_format_id)
        return image_format

    def get_current_repository(self):
        """returns the currently selected repository instance from the UI
        """
        from stalker import Repository
        index = self.repository_comboBox.currentIndex()
        repo_id = self.repository_comboBox.itemData(index)
        repo = Repository.query.get(repo_id)
        return repo

    def get_current_structure(self):
        """returns the currently selected structure instance from the UI
        """
        from stalker import Structure
        index = self.structure_comboBox.currentIndex()
        structure_id = self.structure_comboBox.itemData(index)
        structure = Structure.query.get(structure_id)
        return structure

    def accept(self):
        """create/update the project
        """
        # Name
        if not self.name_lineEdit.is_valid:
            QtWidgets.QMessageBox.critical(
                self,
                'Error',
                'Please fix <b>name</b> field!'
            )
            return
        name = self.name_lineEdit.text()

        # Code
        if not self.code_lineEdit.is_valid:
            QtWidgets.QMessageBox.critical(
                self,
                'Error',
                'Please fix <b>code</b> field!'
            )
            return
        code = self.code_lineEdit.text()

        # Type
        from stalker import Type
        index = self.type_comboBox.currentIndex()
        type_id = self.type_comboBox.itemData(index)
        type = Type.query.get(type_id)  # None type is ok

        # Image Format
        image_format = self.get_current_image_format()
        if not image_format:
            QtWidgets.QMessageBox.critical(
                self,
                'Error',
                'Please select an valid <b>Image Format</b>!'
            )
            return

        # FPS
        fps = self.fps_spinBox.value()

        # Repository
        repo = self.get_current_repository()
        if not repo:
            QtWidgets.QMessageBox.critical(
                self,
                'Error',
                'Please select an valid <b>Repository</b>!'
            )
            return

        # Structure
        structure = self.get_current_structure()
        if not structure:
            QtWidgets.QMessageBox.critical(
                self,
                'Error',
                'Please select an valid <b>Structure</b>!'
            )
            return

        # Status
        from stalker import Status
        index = self.status_comboBox.currentIndex()
        status_id = self.status_comboBox.itemData(index)
        status = Status.query.get(status_id)
        if not status:
            QtWidgets.QMessageBox.critical(
                self,
                'Error',
                'Please select an valid <b>Status</b>!'
            )
            return

        # TODO: Add Client Data fields (which I don't care for now)
        logged_in_user = self.get_logged_in_user()

        # create or update project
        from stalker import db
        if self.mode == 'Create':
            # create a new project
            from stalker import Project
            new_project = Project(
                name=name,
                code=code,
                type=type,
                repositories=[repo],
                structure=structure,
                image_format=image_format,
                fps=fps,
                created_by=logged_in_user
            )
            db.DBSession.add(new_project)
            try:
                db.DBSession.commit()
            except Exception as e:
                db.DBSession.rollback()
                QtWidgets.QMessageBox.critical(
                    self,
                    'Error',
                    str(e)
                )
                return

        else:
            # update the project
            self.project.updated_by = logged_in_user
            self.project.name = name
            self.project.code = code
            self.project.type = type
            self.project.repositories = [repo]
            self.project.structure = structure
            self.project.image_format = image_format
            self.project.fps = fps
            db.DBSession.add(self.project)
            try:
                db.DBSession.commit()
            except Exception as e:
                db.DBSession.rollback()
                QtWidgets.QMessageBox.critical(
                    self,
                    'Error',
                    str(e)
                )
                return

        super(MainDialog, self).accept()
