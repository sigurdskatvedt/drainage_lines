from qgis.core import QgsProcessingFeedback, QgsRasterLayer
from dual_logger import log, ProgressBar
import logging
import os
from datetime import datetime
from .base_task import BaseTask

import processing
from processing.core.Processing import Processing

class AddRastersTask(BaseTask):
    def __init__(self, description, raster1_path, raster2_path, raster_output_path):
        super().__init__(description)
        self.raster1_path = raster1_path
        self.raster2_path = raster2_path
        self.raster_output_path = raster_output_path
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)  # Initialize the progress bar here
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        # Load raster layers
        raster1_layer = QgsRasterLayer(self.raster1_path, "Raster_1")
        raster2_layer = QgsRasterLayer(self.raster2_path, "Raster_2")

        if not raster1_layer.isValid() or not raster2_layer.isValid():
            log(f"Failed to load raster layers: {self.raster1_path} or {self.raster2_path}", level=logging.ERROR)
            return False

        try:
            # Calculate the sum of both rasters
            expression = f'"{raster1_layer.name()}@1" + "{raster2_layer.name()}@1"'
            params = {
                'LAYERS': [raster1_layer, raster2_layer],
                'EXPRESSION': expression,
                'OUTPUT': self.raster_output_path
            }

            result = processing.run("native:rastercalc", params, feedback=self.feedback)
            if result and os.path.exists(self.raster_output_path):
                log(f"Addition of rasters completed successfully. Output saved to: {self.raster_output_path}", level=logging.INFO)
                return True
            else:
                log("Error during raster calculation", level=logging.ERROR)
                return False

        except Exception as e:
            log(f"An error occurred: {e}", level=logging.ERROR)
            return False

