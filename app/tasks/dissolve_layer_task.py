from qgis.core import QgsProcessingFeedback, QgsVectorLayer
from .base_task import BaseTask
import processing
from dual_logger import log
import logging

class DissolveLayerTask(BaseTask):
    def __init__(self, description, input_layer, dissolve_field=None):
        super().__init__(description)
        self.input_layer = input_layer
        self.dissolve_field = dissolve_field
        self.dissolved_layer = None

    def task(self):
        try:
            params = {
                'INPUT': self.input_layer,
                'FIELD': self.dissolve_field,
                'OUTPUT': 'memory:'
            }
            feedback = QgsProcessingFeedback()
            result = processing.run("native:dissolve", params, feedback=feedback)
            self.dissolved_layer = result['OUTPUT']

            if self.dissolved_layer:
                log(f'Task "{self.description()}" completed successfully.', level=logging.INFO)
                return True
            else:
                log(f'Task "{self.description()}" encountered an error during the dissolve operation.', level=logging.ERROR)
                return False
        except Exception as e:
            self.exception = e
            log(f'Task "{self.description()}" failed: {e}', level=logging.ERROR)
            return False

