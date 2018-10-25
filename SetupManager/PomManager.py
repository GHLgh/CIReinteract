import os
import xml.etree.ElementTree as ET

# avoid ET filling namespace
POM_NAMESPACE = "http://maven.apache.org/POM/4.0.0"
ET.register_namespace("", POM_NAMESPACE)

class PomManager:
    def __init__(self, repo_dir):
        self.pom_list = self.find_pom_files(repo_dir)
        
    def find_pom_files(self, repo_dir, recursive=True):
        result = []
        for root, dirs, files in os.walk(repo_dir):
            if "pom.xml" in files:
                result.append(os.path.join(root, "pom.xml"))
            if (recursive):
                for sub_dir in dirs:
                    result += self.find_pom_files(sub_dir)
        return result

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

    def get_plugin_by_artifact_id(self, pom_root, plugin_artifact_id):
        for plugin in pom_root.iter("{" + POM_NAMESPACE + "}" + "plugin"):
            for artifact in plugin.iter("{" + POM_NAMESPACE + "}" + "artifactId"):
                if artifact.text == plugin_artifact_id:
                    return plugin
        return None

    def get_artifact_id(self, plugin_setting):
        if (type(plugin_setting) != type("str")):
            plugin = plugin_setting
        else:
            plugin_tree = ET.parse(plugin_setting)
            plugin = plugin_tree.getroot()
        for artifact in plugin.iter("artifactId"):
            return artifact.text
        return None