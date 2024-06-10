from qgis.core import QgsProcessingFeedback
from .base_task import BaseTask
from qgis import processing
from dual_logger import log, ProgressBar
import logging


class ClassifyFlowTask(BaseTask):

    def __init__(self, description, input_raster, classified_layer,
                 ):
        super().__init__(description)
        self.input_raster = input_raster
        self.classified_layer = classified_layer
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(
            description)  # Initialize the progress bar here
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        log(f'Starting task: {self.description()}')
        classif = [
            '0', '10000', '-9999', '10000', '20000', '1', '20000', '50000',
            '2', '50000', '100000', '3', '100000', '500000', '4', '500000',
            '1000000', '5', '1000000', '1000000000', '6'
        ]

        try:
            params = {
                'INPUT_RASTER': self.input_raster,
                'RASTER_BAND':
                1,  # Assuming you are classifying the first band
                'TABLE': classif,
                'NO_DATA': -9999,  # Specify the no data value if needed
                'RANGE_BOUNDARIES':
                0,  # 0 = min < value <= max, 1 = min <= value < max
                'OPTIONS': 'COMPRESS=LZW',  # Add compression option here
                'OUTPUT': self.classified_layer
            }
            result = processing.run("qgis:reclassifybytable",
                                    params,
                                    feedback=self.feedback)
            self.classified_layer = result['OUTPUT']

            if self.classified_layer:
                log(f'Task "{self.description()}" completed successfully.',
                    level=logging.INFO)
                return True
            log(f'Task "{self.description()}" encountered an error during classification.',
                level=logging.ERROR)
            return False
        except Exception as e:
            self.exception = e
            log(f'Task "{self.description()}" failed: {e}', level=logging.ERROR)
            return False
