from qgis.core import QgsProcessingFeedback, QgsProject
from dual_logger import log, ProgressBar
import logging
from .base_task import BaseTask

import sys
# Add the path to Processing framework
sys.path.append('/usr/share/qgis/python/plugins/')

from qgis import processing


class DissolveAndBufferVectorTask(BaseTask):
    """
    This class handles the process of dissolving and buffering a vector layer.
    """

    def __init__(self, description, vector_layer, buffer_amount, output_path):
        super().__init__(description)
        self.vector_layer = vector_layer
        self.buffer_amount = buffer_amount
        self.output_path = output_path
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        try:
            project = QgsProject.instance()
            map_layers = project.mapLayers().values()
            for layer in map_layers:
                if layer.name() == self.vector_layer:
                    self.vector_layer = layer

            # Dissolve the vector layer
            dissolve_params = {
                'INPUT': self.vector_layer,
                'FIELD':
                [],  # Dissolve all features into one, no specific field
                'OUTPUT': 'memory:'
            }
            dissolved_result = processing.run("native:dissolve",
                                              dissolve_params,
                                              feedback=self.feedback)
            dissolved_layer = dissolved_result['OUTPUT']

            if self.buffer_amount != 0:
                # Buffer the dissolved layer
                buffer_params = {
                    'INPUT': dissolved_layer,
                    'DISTANCE': self.buffer_amount,
                    'SEGMENTS': 5,
                    'DISSOLVE': False,
                    'END_CAP_STYLE': 0,
                    'JOIN_STYLE': 0,
                    'MITER_LIMIT': 2,
                    'OUTPUT': self.output_path
                }
                self.progress_bar.change_description(
                    f"Creating buffer of {self.buffer_amount} meters for {self.field_name}"
                )
                buffered_result = processing.run("native:buffer",
                                                 buffer_params,
                                                 feedback=self.feedback)
                buffered_layer = buffered_result['OUTPUT']

                if buffered_layer:
                    log(f'Task "{self.description()}" completed successfully. Output saved to: {self.output_path}',
                        level=logging.INFO)
                    return True
                log(f'Task "{self.description()}" encountered an error during buffering.',
                    level=logging.ERROR)
                return False

            save_parameters = {
                'INPUT': dissolved_layer,
                'OUTPUT': self.output_path,
            }
            processing.run("native:savefeatures", save_parameters)
            return True
        except Exception as e:
            self.exception = e
            log(f'Task "{self.description()}" failed: {e}',
                level=logging.ERROR)
            return False
