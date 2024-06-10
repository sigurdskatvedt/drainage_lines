from qgis.core import QgsProcessingFeedback, QgsProject, QgsRasterLayer, QgsVectorLayer
from .base_task import BaseTask
from qgis import processing
from dual_logger import log, ProgressBar
import logging


class VectorizeRasterTask(BaseTask):

    def __init__(self, description, input_raster_path, output_vector_path,
                 field_name):
        super().__init__(description)
        self.input_raster = input_raster_path
        self.output_vector_path = output_vector_path
        self.field_name = field_name
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(
            description)  # Initialize the progress bar here
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        log(f'Starting task: {self.description()}')

        try:
            raster_layer = QgsRasterLayer(self.input_raster, "input_raster")

            if not raster_layer.isValid():
                print("Error loading vector layer.")
                return

            params = {
                'INPUT': raster_layer,
                'BAND': 1,  # Assuming you are vectorizing the first band
                'FIELD':
                self.field_name,  # The field name in the output vector layer
                'EIGHT_CONNECTEDNESS':
                True,  # Adjust if needed for four or eight connectedness
                'OUTPUT': self.output_vector_path
            }

            result = processing.run("gdal:polygonize",
                                    params,
                                    feedback=self.feedback)

            self.progress_bar.change_description(
                f"Fixing geometries for {self.field_name}")
            fixed_output = processing.run("native:fixgeometries", {
                'INPUT': result['OUTPUT'],
                'OUTPUT': 'memory:'
            },
                                          feedback=self.feedback)

            fixed_output_layer = fixed_output['OUTPUT']
            fixed_output_layer.setName(self.field_name)
            QgsProject.instance().addMapLayer(fixed_output_layer)

            if fixed_output_layer:
                log(f'Task "{self.description()}" completed successfully.',
                    level=logging.INFO)
                return True

            log(f'Task "{self.description()}" encountered an error during vectorization.',
                level=logging.ERROR)
            return False
        except Exception as e:
            self.exception = e
            log(f'Task "{self.description()}" failed: {e}',
                level=logging.ERROR)
            return False
