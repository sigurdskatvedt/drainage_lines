import sys
from qgis.core import QgsApplication
from qgis import pyplugin_installer
sys.path.append('/usr/share/qgis/python/pyplugin_installer/installer')

# Initialize the QGIS Application
QgsApplication.setPrefixPath('/usr', True)
qgs = QgsApplication([], False)
qgs.initQgis()

QgsPluginInstaller.fetchAvailablePlugins(False)
QgsPluginInstaller.instance().installPlugin('wbt_for_qgis')
