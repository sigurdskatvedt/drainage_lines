from qgis.core import QgsProcessingFeedback
from .base_task import BaseTask
from qgis import processing
from dual_logger import log, ProgressBar
import logging


class DouglasPeuckerTask(BaseTask):

    def __init__(self, description, input_vector, output_vector):
        super().__init__(description)
        self.input_vector = input_vector
        self.output_vector = output_vector
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        log(f'Starting task: {self.description()}')

        try:
            params = {
                'INPUT': self.input_vector,
                'METHOD': 0,
                'TOLERANCE': 1,
                'OUTPUT': self.output_vector
            }
            result = processing.run("native:simplifygeometries",
                                    params,
                                    feedback=self.feedback)
            self.output_vector = result['OUTPUT']

            if self.output_vector:
                log(f'Task "{self.description()}" completed successfully.',
                    level=logging.INFO)
                return True
            log(f'Task "{self.description}" encountered an error during geometry simplification.',
                level=logging.ERROR)
            return False
        except Exception as e:
            self.exception = e
            log(f'Task "{self.description}" failed: {e}', level=logging.ERROR)
            return False
