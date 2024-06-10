from qgis.core import QgsProcessingFeedback
from .base_task import BaseTask
from qgis import processing
from dual_logger import log, ProgressBar
import logging


class CollectGeometriesTask(BaseTask):

    def __init__(self, description, input_vector, output_vector):
        super().__init__(description)
        self.input_vector = input_vector
        self.output_vector = output_vector
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)  # Initialize the progress bar here
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        log(f'Starting task: {self.description}')

        try:
            collect_params = {
                'INPUT': self.input_vector,
                'OUTPUT': self.output_vector
            }
            collected_result = processing.run("native:collect", collect_params, feedback=self.feedback)
            collected_layer = collected_result['OUTPUT']

            if collected_layer:
                log(f'Task "{self.description}" completed successfully.', level=logging.INFO)
                return True
            else:
                log(f'Task "{self.description}" encountered an error during geometry collection.', level=logging.ERROR)
                return False
        except Exception as e:
            self.exception = e
            log(f'Task "{self.description}" failed: {e}', level=logging.ERROR)
            return False

