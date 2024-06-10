import os
from qgis.core import QgsProcessingFeedback
from .base_task import BaseTask
from qgis import processing
from dual_logger import log, ProgressBar
import logging


class GrassRasterToVectorTask(BaseTask):

    def __init__(self, description, input_raster, output_vector):
        super().__init__(description)
        self.input_raster = input_raster
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
                'input': self.input_raster,
                'type': 0,
                'column': 'accumulation_level',
                '-s': False,  # smooth values?
                '-v': True,  # raster values as categories?
                '-z': False,  # raster values as z coordinate
                '-b': False,  # do not build vector topology
                '-t': False,  # do not create attribute table
                'output': self.output_vector
            }
            result = processing.runAndLoadResults("grass:r.to.vect",
                                                  params,
                                                  feedback=self.feedback)

            if os.path.exists(self.output_vector):
                log(f'Task "{self.description()}" completed successfully.',
                    level=logging.INFO)
                return True
            log(f'Task "{self.description()}" encountered an error during thinning.',
                level=logging.ERROR)
            return False

        except Exception as e:
            self.exception = e
            log(f'Task "{self.description}" failed: {e}', level=logging.ERROR)
            return False
