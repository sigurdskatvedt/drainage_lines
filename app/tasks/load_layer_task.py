from qgis.core import QgsProject, QgsVectorLayer
from .base_task import BaseTask
from dual_logger import log
import logging

import sys
# Add the path to Processing framework
sys.path.append('/usr/share/qgis/python/plugins/')

# Import processing after initializing QGIS application
from qgis import processing
from processing.core.Processing import Processing
from processing.algs.gdal.GdalAlgorithmProvider import GdalAlgorithmProvider, GdalUtils

class LoadLayersTask(BaseTask):
    """
    This class is responsible for loading, optionally filtering, and merging vector layers from GML files.
    
    Attributes:
        description (str): The description of the task.
        gml_path (str): The base path to the GML file containing the layers.
        layer_names (list of str): The names of the layers to be loaded from the GML file.
        output_name (str): The name assigned to the merged output layer.
        expression (str, optional): The expression used to filter features within the layers. Default is None.
    
    Methods:
        task: Loading, optionally filtering, and merging the specified layers into a single vector layer.
    """

    def __init__(self,
                 description,
                 gml_path,
                 layer_names,
                 output_name,
                 expression=None):
        super().__init__(description)
        self.gml_path = gml_path
        self.layer_names = [layer_names] if isinstance(layer_names,
                                                       str) else layer_names
        self.output_name = output_name
        self.expression = expression
        self.merged_layer = None

    def task(self):
        selected_layers = []

        for name in self.layer_names:
            layer_path = f"{self.gml_path}|layername={name}"

            if self.expression is not None:
                # Extract features based on the attribute value
                result = processing.run(
                    "native:extractbyexpression", {
                        'INPUT': layer_path,
                        'EXPRESSION': self.expression,
                        'OUTPUT': 'memory:'
                    })
                layer = result['OUTPUT']
            else:
                # Load the entire layer if no attribute filter is provided
                layer = QgsVectorLayer(layer_path, name)

            if not layer.isValid() or layer.featureCount() == 0:
                log(f"Layer {name} is not valid or has no features.",
                    level=logging.ERROR)
                continue

            selected_layers.append(layer)

        if selected_layers:
            if len(selected_layers) > 1:
                # Merge the layers that have passed the filtering
                self.merged_layer = processing.run(
                    "native:mergevectorlayers", {
                        'LAYERS': selected_layers,
                        'CRS': None,
                        'OUTPUT': 'memory:'
                    })['OUTPUT']
            else:
                self.merged_layer = selected_layers[0]

            if not self.merged_layer.isValid():
                log("Failed to merge layers into a valid layer.",
                    level=logging.ERROR)
                return False

            self.merged_layer.setName(self.output_name)
            QgsProject.instance().addMapLayer(self.merged_layer)
            log(f"Successfully merged layers into {self.output_name}",
                level=logging.INFO)
            return True
        else:
            log("No layers with features to merge after applying attribute filter.",
                level=logging.WARNING)
            return False
