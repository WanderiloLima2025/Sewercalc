# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Sewercalc_Dialog_Dimensionar
 Plugin para dimensionamento de redes coletoras de esgoto 
        begin                : 2025-02-07
        git sha              : $Format:%H$
        copyright            : (C) 2025 by Wanderilo  Lima
        email                : Wanderilo Lima
 ***************************************************************************/
"""

import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Sewercalc_Dialog_Dimensionar.ui'))

class SewercalcDlgDimensionar(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(SewercalcDlgDimensionar, self).__init__(parent) 
        self.setupUi(self)
