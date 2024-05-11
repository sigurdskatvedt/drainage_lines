from qgis.core import QgsProcessingFeedback
from dual_logger import log, ProgressBar
import logging
import os
from .base_task import BaseTask

import sys
# Add the path to Processing framework
sys.path.append('/usr/share/qgis/python/plugins/')

# Import processing after initializing QGIS application
from qgis import processing
from processing.core.Processing import Processing
from processing.algs.gdal.GdalAlgorithmProvider import GdalAlgorithmProvider, GdalUtils

class ClipMosaicByVectorTask(BaseTask):
    """
        This class handles the process of clipping a raster mosaic using a dissolved and buffered vector layer as the mask.

    Attributes:
        description (str): The description of the task.
        mosaic_path (str): The file path to the raster mosaic to be clipped.
        vector_layer (QgsVectorLayer): The vector layer used to generate the mask.
        buffer_amount (float): The amount to buffer the vector layer, in meters.
        clipped_output_path (str): The file path where the clipped raster output will be saved.
    
    """
    def __init__(self, description, mosaic_path, vector_layer, buffer_amount, clipped_output_path):
        super().__init__(description)
        self.mosaic_path = mosaic_path
        self.vector_layer = vector_layer
        self.buffer_amount = buffer_amount
        self.clipped_output_path = clipped_output_path
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)  # Initialize the progress bar here

        # Connect the progressChanged signal to the progress_changed method
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
                # Dissolve the vector layer
        dissolve_params = {
            'INPUT': self.vector_layer,
            'FIELD': [],  # Dissolve all features into one, no specific field
            'OUTPUT': 'memory:'
        }
        dissolved_result = processing.run("native:dissolve", dissolve_params, feedback=self.feedback)
        dissolved_layer = dissolved_result['OUTPUT']

        buffer_params = {
            'INPUT': dissolved_layer,
            'DISTANCE': self.buffer_amount,  # Buffer distance in meters, adjust if the CRS is not in meters
            'SEGMENTS': 5,  # Quality of the rounded edge
            'DISSOLVE': False,
            'END_CAP_STYLE': 0,  # Round end cap style
            'JOIN_STYLE': 0,  # Round join style
            'MITER_LIMIT': 2,
            'OUTPUT': 'memory:'
        }
        buffered_result = processing.run("native:buffer", buffer_params, feedback=self.feedback)
        buffered_layer = buffered_result['OUTPUT']

        # Clip the mosaic with the buffered and dissolved layer
        params = {
            'INPUT': self.mosaic_path,
            'MASK': buffered_layer,
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
    """
    This class manages the task of reprojecting a raster file from its original coordinate reference system (CRS)
    to a specified target CRS.

    Attributes:
        description (str): A description of the task for identification and logging purposes.
        input_raster_path (str): The file path of the raster to be reprojected.
        output_crs (str): The coordinate reference system (CRS) code to which the raster will be reprojected.
        reprojected_output_path (str): The file path where the reprojected raster will be saved.
    
    """
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
    """ Create a temporary file to store the list of raster paths """
    temp_file_path = 'raster_file_list.txt'  # Consider using a temporary file path
    with open(temp_file_path, 'w') as file_list:
        for file_path in raster_files:
            file_list.write(f"{file_path}\n")
    return temp_file_path

class CreateMosaicTask(BaseTask):
    """
    Handles the process of creating a raster mosaic from a list of raster files.

    Attributes:
        description (str): The description of the task.
        raster_files (list of str): The file paths of the raster files to be merged into the mosaic.
        mosaic_output_path (str): The file path where the resultant mosaic will be saved.
    
    """
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
        params = {
                'INPUT': self.raster_files,
                'OUTPUT': self.mosaic_output_path,
        }
        try:
            log(f"Starting merging of mosaic. Saving to {self.mosaic_output_path}")
            result = processing.run("gdal:merge", params, feedback=self.feedback)
            if result and os.path.exists(self.mosaic_output_path):
                log(f"Mosaic created successfully. Output saved to: {self.mosaic_output_path}", level=logging.INFO)
                return True
            log("Error with creating mosaick")
        except Exception as e:
            log(f"Failed to create mosaic: {e}", level=logging.ERROR)  # Ensure exceptions are logged
            return False
