from qgis.core import QgsProcessingFeedback
from .base_task import BaseTask
from qgis import processing
from dual_logger import log, ProgressBar
import logging


class RasterToIntTask(BaseTask):

    def __init__(self, description, input_raster, output_raster):
        super().__init__(description)
        self.input_raster = input_raster
        self.output_raster = output_raster
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        log(f'Starting task: {self.description()}')

        try:
            params = {
                'INPUT': self.input_raster,
                'OUTPUT': self.output_raster,
                'DATA_TYPE': 2  # Type 2 corresponds to Int16 in GDAL
            }

            result = processing.run("gdal:translate",
                                    params,
                                    feedback=self.feedback)
            self.output_raster = result['OUTPUT']

            if self.output_raster:
                log(f'Task "{self.description}" completed successfully.',
                    level=logging.INFO)
                return True
            log(f'Task "{self.description}" encountered an error during transformation.',
                level=logging.ERROR)
            return False
        except Exception as e:
            self.exception = e
            log(f'Task "{self.description}" failed: {e}', level=logging.ERROR)
            return False
