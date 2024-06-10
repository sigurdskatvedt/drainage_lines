import os
from qgis.core import QgsProcessingFeedback, QgsProject
from .base_task import BaseTask
from qgis import processing
from qgis.core import QgsRasterLayer, QgsProject
from dual_logger import log, ProgressBar
import logging


class ThinRasterTask(BaseTask):

    def __init__(self, description, input_raster, output_raster, output_name):
        super().__init__(description)
        self.input_raster = input_raster
        self.output_raster = output_raster
        self.output_name = output_name
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        log(f'Starting task: {self.description()}')
        raster_name = "classified_d8_dtm_buildings_culverts_epsilon_least_1000dist_integer"

        try:
            params = {
                'input': self.input_raster,
                'iterations': 200,
                'output': self.output_raster,
                'GRASS_REGION_PARAMETER': None,
                'GRASS_REGION_CELLSIZE_PARAMETER': 0,
                'GRASS_RASTER_FORMAT_OPT': '',
                'GRASS_RASTER_FORMAT_META': ''
            }
            result = processing.runAndLoadResults("grass:r.thin",
                                                  params,
                                                  feedback=self.feedback)

            if os.path.exists(self.output_raster):
                log(f'Task "{self.description()}" completed successfully.',
                    level=logging.INFO)
                return True
            log(f'Task "{self.description()}" encountered an error during thinning.',
                level=logging.ERROR)
            return False
        except Exception as e:
            self.exception = e
            log(f'Task "{self.description()}" failed: {e}',
                level=logging.ERROR)
            return False
