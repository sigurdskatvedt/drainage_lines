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


class AccumulationTask(BaseTask):
    def __init__(self, description, filled_dem_path, method, output_path):
        super().__init__(description)
        self.filled_dem_path = filled_dem_path
        self.method = method
        self.output_path = output_path
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)  # Initialize the progress bar here

        # Connect the progressChanged signal to the progress_changed method
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        raster_layer = QgsRasterLayer(self.filled_dem_path, "Input DEM", "gdal")

        if not raster_layer.isValid():
            log("Failed to load the DEM layer. Please check the path.", level=logging.ERROR)
            return False
        else:
            log("DEM layer loaded successfully.", level=logging.INFO)
            # Implement further processing here

            params = {
                # 'ELEVATION': self.filled_dem_path,
                'DEM':raster_layer,
                'METHOD': self.method,  # Multiple Maximum Downslope Gradient Based Flow Direction
                'FLOW': self.output_path,  # Assuming this is the intended output
                #'VAL_MEAN': 'TEMPORARY_OUTPUT',
                'CONVERGENCE':1.1,
                #'ACCU_TARGET': self.filled_dem_path,                # Add other parameters as needed, such as 'ACCU_TARGET' if required by your workflow
                # Other parameters can be set as needed, or left to their default values
                # 'SINKROUTE': None, 'WEIGHTS': None, 'FLOW': 'TEMPORARY_OUTPUT', 'VAL_INPUT': None, , 'ACCU_MATERIAL': None, , 'ACCU_TOTAL': 'TEMPORARY_OUTPUT', 'ACCU_LEFT': 'TEMPORARY_OUTPUT', 'ACCU_RIGHT': 'TEMPORARY_OUTPUT', 'STEP': 1, 'FLOW_UNIT': 1, 'FLOW_LENGTH': 'TEMPORARY_OUTPUT', 'LINEAR_VAL': None, 'LINEAR_DIR': None, 'WEIGHT_LOSS': 'TEMPORARY_OUTPUT', 'METHOD': 6, 'LINEAR_DO': False, 'LINEAR_MIN': 500, 'CONVERGENCE': 1.1, 'MFD_CONTOUR': False, 'NO_NEGATIVES': True
            }

            try:
                log(f"Starting flow accumulation with method {self.method}.")
                result = processing.run("sagang:flowaccumulationparallelizable", params)  # Update the algorithm ID as necessary
                if result and os.path.exists(self.output_path):
                    log(
                        f"\nFlow accumulation completed successfully. Output saved to: {self.output_path}", level=logging.INFO)
                    return True
                else:
                    raise Exception("Error during flow accumulation.")
            except Exception as e:
                self.exception = e
                return False
            processing.run("sagang:flowaccumulationparallelizable", {'DEM':'/Users/sigurdskatvedt/drainage_lines/data/dtm1/dtm1/clipped2/filled.tif','FLOW':'TEMPORARY_OUTPUT','update':0,'METHOD':2,'CONVERGENCE':1.1})

