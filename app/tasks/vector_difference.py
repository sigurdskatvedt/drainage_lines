from qgis.core import QgsProcessingFeedback, QgsVectorLayer, QgsProject
from .base_task import BaseTask
from qgis import processing
from dual_logger import log, ProgressBar
import logging


class VectorDifferenceTask(BaseTask):

    def __init__(self, description, primary_name, difference_name, output_vector_name):
        super().__init__(description)
        self.primary_name = primary_name
        self.difference_name = difference_name
        self.output_vector_name = output_vector_name
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        log(f'Starting task: {self.description()}')

        project = QgsProject.instance()
        map_layers = project.mapLayers().values()

        for layer in map_layers:
            log(f"Layer {layer.name()} has {layer.sourceCrs().toProj()}")
            if layer.name() == self.primary_name:
                primary_layer_path = layer
            elif layer.name() == self.difference_name:
                difference_layer_path = layer

        try:
            params = {
                'INPUT': primary_layer_path,
                'OVERLAY': difference_layer_path,
                'OUTPUT': 'memory:'
            }
            result = processing.run("native:difference",
                                    params,
                                    feedback=self.feedback)
            output_vector = result['OUTPUT']

            output_vector.setName(self.output_vector_name)
            QgsProject.instance().addMapLayer(output_vector)

            if output_vector:
                log(f'Task "{self.description()}" completed successfully.',
                    level=logging.INFO)
                return True

            log(f'Task "{self.description()}" encountered an error during vector difference calculation.',
                level=logging.ERROR)
            return False

        except Exception as e:
            self.exception = e
            log(f'Task "{self.description}" failed: {e}', level=logging.ERROR)
            return False
