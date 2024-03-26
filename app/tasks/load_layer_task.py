from .base_task import BaseTask
from dual_logger import log
import logging
import processing
from variables import saving_folder
from qgis.core import QgsVectorLayer


def fix_invalid_geometries(input_layer):
    """
    Fixes invalid geometries in a given layer.

    Args:
        input_layer (QgsVectorLayer): The layer to fix.

    Returns:
        QgsVectorLayer: A new layer with fixed geometries.
    """
    result = processing.run("native:fixgeometries", {
        'INPUT': input_layer,
        'OUTPUT': 'memory:'
    })
    fixed_layer = result['OUTPUT']

    return fixed_layer


class LoadLayerTask(BaseTask):
    def __init__(self, description, layer_name, file_path):
        super().__init__(description, layer_name)
        self.file_path = file_path
        self.layer_name = layer_name
        self.fixed_layer = None
        self.output = None

    def task(self):
        log(f"Loading layer from {self.file_path}", level=logging.INFO)
        layer = QgsVectorLayer(self.file_path, self.layer_name, 'ogr')
        if layer.featureCount() == 0:
            log(f"Layer contains no features: {self.file_path}", level=logging.WARNING)
            return False
        if not layer.isValid():
            log(f"Layer is not valid: {self.file_path}", level=logging.ERROR)
            return False
        self.output = layer
        log(f"Completed task, fixed geometries for layer: {self.file_path}", level=logging.INFO)
        return True
