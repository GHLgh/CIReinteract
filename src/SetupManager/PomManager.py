import os
import xml.etree.ElementTree as ET

# avoid ET filling namespace
POM_NAMESPACE = "http://maven.apache.org/POM/4.0.0"
ET.register_namespace("", POM_NAMESPACE)

# PomManager class is a wrapper over xml library to handle common operations
# specifically for pom.xml files: finding specific plugin and adding specific plugin
# Note that the PomManager modify pom.xml files in a given directory recursively if specified.
# In other words, the specific modification will applies to all pom.xml files in the directory
# because the RTS tools we are interested in often need to be included in every pom.xml file
class PomManager:
    # Constructor that instantiate the PomManager object with respect to the provided directory
    # @param repo_dir: the path to directory that contains pom.xml files to be operated on
    def __init__(self, repo_dir):
        self.pom_list = self.find_pom_files(repo_dir)
        
    # Function that will return a list of pom.xml files that are inside the given directory
    # @param repo_dir: the path to directory that contains pom.xml files
    # @param recursive: boolean to indicate if the pom.xml files in sub directories
    #    will be included. If False, only returns the pom.xml files in the given directories
    # @return a list of pom.xml files
    def find_pom_files(self, repo_dir, recursive=True):
        result = []
        for root, dirs, files in os.walk(repo_dir):
            if "pom.xml" in files:
                result.append(os.path.join(root, "pom.xml"))
            if (recursive):
                for sub_dir in dirs:
                    result += self.find_pom_files(sub_dir)
        return result

    # Add a plugin defined in a separate xml file to all the pom.xml files managed by this PomManager
    # The separate xml file should be in the following format:
    #   <plugin>
    #       ....
    #   </plugin>
    # @param plugin_setting_xml: path to the separate xml file that defines the plugin configuration
    # @param ignore: boolean to indicate if the plugin will be added even if 
    #    it has been included in the pom.xml file. If False, the plugin will be added anyway
    # @param output_file_name: the output file to be written to. If None, overwrite the pom.xml file.
    #    Usually used to verify if the output matches the expectation before trying to
    #    overwrite the original files
    def add_plugin(self, plugin_setting_xml, ignore=True, output_file_name=None):
        plugin_tree = ET.parse(plugin_setting_xml)
        plugin = plugin_tree.getroot()
        plugin_artifact_id = self.get_artifact_id(plugin)
        for pom_file in self.pom_list:
            pom_tree = ET.parse(pom_file)
            pom_root = pom_tree.getroot()
            # only care about the (immediate) plugins field in the first build (ignore plugins in pluginManagement)
            # [TODO] refine filter (and check if first build is enough)
            for build in pom_root.iter("{" + POM_NAMESPACE + "}" + "build"):
                for child in build:
                    if child.tag == "{" + POM_NAMESPACE + "}" + "plugins":
                        # The plugin has been added
                        if self.get_plugin_by_artifact_id(child, plugin_artifact_id) is not None \
                            and ignore:
                            continue
                        child.append(plugin)
                break
            if output_file_name is not None:
                pom_tree.write(os.path.join(os.path.dirname(pom_file), output_file_name))
            else:
                pom_tree.write(pom_file)

    # Get the specified plugin configuration as ET object if it exists
    # @param pom_root: the root as ET object to search for the specified plugin
    # @param plugin_artifact_id: the artifact ID that specify the plugin
    # @return the plugin configuration as ET object. None otherwise
    def get_plugin_by_artifact_id(self, pom_root, plugin_artifact_id):
        for plugin in pom_root.iter("{" + POM_NAMESPACE + "}" + "plugin"):
            for artifact in plugin.iter("{" + POM_NAMESPACE + "}" + "artifactId"):
                if artifact.text == plugin_artifact_id:
                    return plugin
        return None

    # Get the artifact ID in a plugin configuration
    # @param plugin_setting: plugin configuration that is either as string or ET object
    # @return the artifact ID as string. None otherwise
    def get_artifact_id(self, plugin_setting):
        if (type(plugin_setting) != type("str")):
            plugin = plugin_setting
        else:
            plugin_tree = ET.parse(plugin_setting)
            plugin = plugin_tree.getroot()
        for artifact in plugin.iter("artifactId"):
            return artifact.text
        return None