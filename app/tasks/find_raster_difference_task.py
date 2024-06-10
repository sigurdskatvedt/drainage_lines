from qgis.core import QgsProcessingFeedback, QgsRasterLayer
from .base_task import BaseTask
from qgis import processing
from dual_logger import log, ProgressBar
import logging


class FindDifferenceRastersTask(BaseTask):

    def __init__(self, description, raster1_path, raster2_path, output_raster):
        super().__init__(description)
        self.raster1_path = raster1_path
        self.raster2_path = raster2_path
        self.output_raster = output_raster
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        log(f'Starting task: {self.description()}')

        raster1_layer = QgsRasterLayer(self.raster1_path, "Raster_1")
        raster2_layer = QgsRasterLayer(self.raster2_path, "Raster_2")

        try:
            expression = f'"{raster1_layer.name()}@1" - "{raster2_layer.name()}@1"'
            params = {
                'EXPRESSION': expression,
                'LAYERS': [raster1_layer, raster2_layer],
                'OUTPUT': self.output_raster
            }
            result = processing.run("native:rastercalc",
                                    params,
                                    feedback=self.feedback)
            self.output_raster = result['OUTPUT']

            if self.output_raster:
                log(f'Task "{self.description()}" completed successfully.',
                    level=logging.INFO)
                return True

            log(f'Task "{self.description()}" encountered an error during raster difference calculation.',
                level=logging.ERROR)
            return False

        except Exception as e:
            self.exception = e
            log(f'Task "{self.description()}" failed: {e}', level=logging.ERROR)
            return False
