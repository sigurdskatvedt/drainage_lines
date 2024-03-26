from qgis.core import QgsTask, QgsProject, QgsVectorLayer, QgsVectorFileWriter
from dual_logger import log  # Make sure dual_logger.py is accessible
import logging
from PyQt5.QtCore import pyqtSignal


class BaseTask(QgsTask):
    layerLoaded = pyqtSignal(QgsVectorLayer)

    def __init__(self, description, layer_name=None):
        super().__init__(description, QgsTask.CanCancel)
        self.layer_output_name = layer_name
        self.exception = None
        self.output = None

    def run(self):
        try:
            return_val = self.task()
            return return_val
        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        if self.exception:
            log(f'Task "{self.description()}" failed: {self.exception}', level=logging.ERROR)
        elif self.output:
            # Check if the output is a string (path) or a QgsMapLayer
            if isinstance(self.output, str):
                # Assuming it's a vector layer; adjust if it could be a raster
                layer = QgsVectorLayer(self.output, self.layer_output_name, "ogr")
                if not layer.isValid():
                    log(f"Failed to load layer from path: {self.output}", level=logging.ERROR)
                    return
            else:
                # If self.output is already a QgsMapLayer, just set its name
                layer = self.output
                layer.setName(self.layer_output_name)
                if not layer.isValid():
                    # Handle invalid layer
                    return False
                # Assuming the task does more processing here
                # Emit the signal with the loaded layer
                log(f"Added layer '{layer.name()}'. Feature count is: {layer.featureCount()}", level=logging.INFO)
                project = QgsProject.instance()
                project.addMapLayer(layer)

    def cancel(self):
        log(f'Task "{self.description()}" was canceled', level=logging.WARNING)

        super().cancel()

    def task(self):
        # This method should be implemented by subclasses
        pass
