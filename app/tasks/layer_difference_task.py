from qgis.core import QgsProcessingFeedback, QgsVectorLayer
from .base_task import BaseTask
from dual_logger import log
import logging
import processing

class LayerDifferenceTask(BaseTask):
    def __init__(self, description, input_layer, overlay_layer):
        super().__init__(description)
        self.input_layer = input_layer
        self.overlay_layer = overlay_layer
        self.difference_layer = None

    def task(self):
        try:
            params = {
                'INPUT': self.input_layer,
                'OVERLAY': self.overlay_layer,
                'OUTPUT': 'memory:'
            }
            feedback = QgsProcessingFeedback()
            result = processing.run("native:difference", params, feedback=feedback)

            self.difference_layer = result['OUTPUT']

            if self.difference_layer:
                log(f'Task "{self.description()}" completed successfully. Result is stored in a temporary layer.', level=logging.INFO)
                return True
            else:
                log(f'Task "{self.description()}" encountered an error during the difference operation.', level=logging.ERROR)
                return False
        except Exception as e:
            self.exception = e
            log(f'Task "{self.description()}" failed: {e}', level=logging.ERROR)
            return False
