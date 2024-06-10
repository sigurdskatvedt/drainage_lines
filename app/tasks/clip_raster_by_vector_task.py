from qgis.core import QgsProcessingFeedback, QgsVectorLayer, QgsRasterLayer
from dual_logger import log, ProgressBar
import logging
import os
from .base_task import BaseTask

import sys
# Add the path to Processing framework
sys.path.append('/usr/share/qgis/python/plugins/')

from qgis import processing


class ClipRasterByVectorTask(BaseTask):
    """
    This class handles the process of clipping a raster mosaic using a buffered vector layer as the mask.
    """

    def __init__(self, description, raster_path, mask_layer,
                 clipped_output_path):
        super().__init__(description)
        self.raster_path = raster_path
        self.mask_layer = mask_layer
        self.clipped_output_path = clipped_output_path
        self.feedback = QgsProcessingFeedback()
        self.progress_bar = ProgressBar(description)
        self.feedback.progressChanged.connect(self.progress_changed)

    def progress_changed(self, progress):
        self.progress_bar.update(progress)

    def task(self):
        try:
            vector_layer = QgsVectorLayer(f"{self.mask_layer}|crs=epsg:32633",
                                          "vector_mask", "ogr")
            # Clip the mosaic with the buffered and dissolved layer
            params = {
                'INPUT': self.raster_path,
                'MASK': vector_layer,
                'MULTITHREADING': True,
                'KEEP_RESOLUTION': True,
                'NODATA': None,
                'OUTPUT': self.clipped_output_path
            }

            result = processing.run("gdal:cliprasterbymasklayer",
                                    params,
                                    feedback=self.feedback)

            input_layer = QgsRasterLayer(self.clipped_output_path,
                                         "Input_Raster")

            expression = f'("{input_layer.name()}@1" > 0.1) * "{input_layer.name()}@1" / (("{input_layer.name()}@1" > 0.1) * 1 + ("{input_layer.name()}@1" <= 0.1) * 0)'

            params = {
                'EXPRESSION': expression,
                'LAYERS': [input_layer],
                'OUTPUT': self.clipped_output_path
            }
            result_clippednodata = processing.run("native:rastercalc",
                                                  params,
                                                  feedback=self.feedback)

            output_raster = result_clippednodata['OUTPUT']
            if result and os.path.exists(self.clipped_output_path):
                log(f"Mosaic clipped successfully. Output saved to: {self.clipped_output_path}",
                    level=logging.INFO)
                return True
            else:
                log(f"Task '{self.description}' encountered an error during clipping.",
                    level=logging.ERROR)
                return False
        except Exception as e:
            self.exception = e
            log(f"Task '{self.description}' failed: {e}", level=logging.ERROR)
            return False
