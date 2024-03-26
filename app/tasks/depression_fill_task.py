from qgis.core import QgsProcessingFeedback, QgsProject, QgsRasterLayer
from dual_logger import log, ProgressBar
import processing
import logging
import os
import sys
import time
from datetime import datetime
from .base_task import BaseTask
from variables import saving_folder


class DepressionFillTask(BaseTask):
    def __init__(self, description, input_dem, filled_dem_output_path):
        super().__init__(description)
        self.input_dem = input_dem
        self.filled_dem_output_path = filled_dem_output_path
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)  # Initialize the progress bar here

        # Connect the progressChanged signal to the progress_changed method
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        raster_layer = QgsRasterLayer(self.input_dem, "Input DEM", "gdal")
        print(raster_layer)

        if not raster_layer.isValid():
            log("Failed to load the DEM layer. Please check the path.", level=logging.ERROR)
            return False
        else:
            log("DEM layer loaded successfully.", level=logging.INFO)
            # Implement further processing here


            params = {
                'ELEV': raster_layer,
                'MINSLOPE': 0.1,
                'FDIR': 'NULL',
                'FILLED': self.filled_dem_output_path,
                'WSHED': 'NULL'
            }


            try:
                log("Starting depression filling.")
                result = processing.run("sagang:fillsinksxxlwangliu", params)
                if result and os.path.exists(self.filled_dem_output_path):
                    log(
                        f"\nDepression filled DEM created successfully. Output saved to: {self.filled_dem_output_path}", level=logging.INFO)
                    return True
                else:
                    raise Exception("Error during depression filling.")
            except Exception as e:
                self.exception = e
                return False

