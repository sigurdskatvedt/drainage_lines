from qgis.core import QgsProject, QgsVectorLayer
from .base_task import BaseTask
from dual_logger import log
import logging
from qgis import processing


class SaveLayerToFileTask(BaseTask):

    def __init__(self, description, layer_name, file_path):
        super().__init__(description)
        self.layer_name = layer_name
        self.file_path = file_path

    def task(self):

        project = QgsProject.instance()
        mapLayers = project.mapLayers().values()
        log(f"MapLayers: {mapLayers}")
        layer = QgsProject.instance().mapLayersByName(
            self.layer_name)[0]  # Get the first layer with the given name

        if not layer.isValid():
            log(f"Layer {self.file_path} is not valid.", level=logging.ERROR)
            return False

        parameters = {
            'INPUT': layer,
            'OUTPUT': self.file_path,
        }
        processing.run("native:savefeatures", parameters)
        log(f"Layer {self.layer_name} saved to {self.file_path}.",
            level=logging.INFO)
        return True
