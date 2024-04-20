from qgis.core import QgsProcessingFeedback, QgsProject, QgsVectorLayer
from dual_logger import log, ProgressBar
import processing
import logging
import os
import sys
import time
from datetime import datetime
from .base_task import BaseTask
from variables import saving_folder


class ClipMosaicByVectorTask(BaseTask):
    def __init__(self, description, mosaic_path, vector_layer, clipped_output_path):
        super().__init__(description)
        self.mosaic_path = mosaic_path
        self.vector_layer = vector_layer
        self.clipped_output_path = clipped_output_path
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)  # Initialize the progress bar here

        # Connect the progressChanged signal to the progress_changed method
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        params = {
                'INPUT': self.mosaic_path,
                'MASK': self.vector_layer,
                'MULTITHREADING': True,
                'NODATA': None,
                'OUTPUT': self.clipped_output_path
                }

        try:
            result = processing.run("gdal:cliprasterbymasklayer", params, feedback=self.feedback)
            if result and os.path.exists(self.clipped_output_path):
                log(f"Mosaic clipped successfully. Output saved to: {self.clipped_output_path}", level=logging.INFO)
                return True
        except Exception as e:
            self.exception = e
            log(e)
            return False

class ReprojectRasterTask(BaseTask):
    def __init__(self, description, input_raster_path, output_crs, reprojected_output_path):
        super().__init__(description)
        self.input_raster_path = input_raster_path
        self.output_crs = output_crs
        self.reprojected_output_path = reprojected_output_path
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)

        # Connect the progressChanged signal to the progress_changed method
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        params = {
            'INPUT': self.input_raster_path,
            'TARGET_CRS': self.output_crs,
            'OUTPUT': self.reprojected_output_path
        }

        try:
            result = processing.run("gdal:warpreproject", params, feedback=self.feedback)
            if result and os.path.exists(self.reprojected_output_path):
                log(f"Raster reprojected successfully. Output saved to: {self.reprojected_output_path}", level=logging.INFO)
                return True
        except Exception as e:
            self.exception = e
            log(str(e), level=logging.ERROR)
            return False

def create_file_list(raster_files):
    # Create a temporary file to store the list of raster paths
    temp_file_path = 'raster_file_list.txt'  # Consider using a temporary file path
    with open(temp_file_path, 'w') as file_list:
        for file_path in raster_files:
            file_list.write(f"{file_path}\n")
    return temp_file_path

class CreateMosaicTask(BaseTask):
    def __init__(self, description, raster_files, mosaic_output_path):
        super().__init__(description)
        self.raster_files = raster_files
        self.mosaic_output_path = mosaic_output_path
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)  # Initialize the progress bar here

        # Connect the progressChanged signal to the progress_changed method
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        log(self.raster_files)
        file_list_path = create_file_list(self.raster_files)

        params = {
                'INPUT': self.raster_files,
                'OUTPUT': self.mosaic_output_path,
        }
        try:
            log(f"Starting merging of mosaic. Saving to {self.mosaic_output_path}")
            result = processing.run("gdal:merge", params, feedback=self.feedback)
            if result and os.path.exists(self.mosaic_output_path):
                log(f"\nMosaic created successfully. Output saved to: {self.mosaic_output_path}", level=logging.INFO)
                return True
            log("Error with creating mosaick")
        except Exception as e:
            log(f"Failed to create mosaic: {e}", level=logging.ERROR)  # Ensure exceptions are logged
            return False




class CreateRasterMosaicTask(BaseTask):
    def __init__(self, description, input_folder, output_path):
        super().__init__(description)
        self.input_folder = input_folder
        self.output_path = output_path

    def task(self):
        raster_files = [os.path.join(self.input_folder, f)
                        for f in os.listdir(self.input_folder) if f.endswith(('.tif', '.tiff'))]
        if not raster_files:
            self.exception = Exception("No raster files found in the specified folder.")
            return False

        params = {
            'INPUT': raster_files,
            'PCT': False,
            'SEPARATE': False,
            'DATA_TYPE': 5,
            'OPTIONS': 'COMPRESS=LZW',
            'OUTPUT': self.output_path
        }
        try:
            result = processing.run("gdal:merge", params)
            if 'OUTPUT' in result:
                log(f"Mosaic created successfully. Output saved to: {self.output_path}", level=logging.INFO)
                return True
            else:
                raise Exception("Error during mosaic creation.")
        except Exception as e:
            self.exception = e
            return False
