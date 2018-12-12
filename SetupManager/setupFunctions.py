from .PomManager import PomManager
import travis_yml
import yaml
import os

EKSTAZI_XML_PATH = "{}/ekstazi.xml".format(os.path.dirname(os.path.realpath(__file__)))
AZURE_FUNCTION_ENTRY = "https://cireinteract.azurewebsites.net/api/CINotificationEndPoint?code=AEW9Jm5ijk8SNN2PA0hIPwAxIcb3lqjqWL97EadKyB6qWSkNqNC0bQ=="
AZURE_REPORT_STORAGE_ENTRY = "https://cireinteract.azurewebsites.net/api/StoreReportEndPoint?code=tl93p4oBpLOxwwYgaFanI/JhDdlynBag5LXYETBfNAM6QSjUaIfXgw=="

# Function that can be used to set up Travis for utilizing RTS tool
# assuming that:
#   the RTS tool uses some kind of cache for the work
#   the project is using Maven
# @param tag: the tag to identify the cache location
# @param suffixes: list of suffixs (extensions) of the files used for cache
# @param predefined_command: the mvn command to override the existing one in
#    Travis configuration, often use for generate RTS results to be analyzed.
#    If None, nothing will be overridden
def travis_setup(repo_dir, tag, suffixes, predefined_command = None):
    def restore_by_suffix(tag, suffix):
        return "(cd $HOME/{}_cache && find . -name '*.{}' -print | cpio -pvdumB /)".format(tag, suffix)

    def cache_by_suffix(tag, suffix):
        return "find $TRAVIS_BUILD_DIR -name '*.{}' -print | cpio -pvdumB $HOME/{}_cache".format(suffix, tag)

    def compress_test_reports():
        return r"tar -zcf ${TRAVIS_BRANCH}.tar.gz $HOME/report_placeholder"

    def report_uploader(predefined_after_script):
        predefined_after_script.append("find $TRAVIS_BUILD_DIR -name 'TEST*.xml' -print | cpio -pvdumB $HOME/report_placeholder")
        predefined_after_script.append(compress_test_reports())
        predefined_after_script.append(r'curl -F "ekstazi=@${TRAVIS_BUILD_DIR}/${TRAVIS_BRANCH}.tar.gz" ' + AZURE_REPORT_STORAGE_ENTRY)
        return predefined_after_script


    read_file = open(os.path.join(repo_dir, ".travis.yml"), 'r')
    travis_setting = yaml.load(read_file)
    read_file.close()
    # set up cache directory
    if "cache" not in travis_setting:
        travis_setting["cache"] = {}
    new_directories = ["$HOME/{}_cache".format(tag)]
    if "directories" in travis_setting["cache"]:
        if "$HOME/{}_cache".format(tag) not in travis_setting["cache"]["directories"]:
            travis_setting["cache"]["directories"] += new_directories
    else:
        travis_setting["cache"]["directories"] = new_directories
        
    # set before_script (restore artifacts) and before_cache (store artifacts)
    if "before_script" not in travis_setting:
        travis_setting["before_script"] = []
    if "before_cache" not in travis_setting:
        travis_setting["before_cache"] = []

    for suffix in suffixes:
        if restore_by_suffix(tag, suffix) not in travis_setting["before_script"]:
            travis_setting["before_script"].append(restore_by_suffix(tag, suffix))
        if cache_by_suffix(tag, suffix) not in travis_setting["before_cache"]:
            travis_setting["before_cache"].append(cache_by_suffix(tag, suffix))
    
    # Replace maven command if it is necessary,
    # i.e. STARTS needs to call "starts:starts" explicitly to run
    if "script" not in travis_setting:
        # shouldn't reach here
        travis_setting["script"] = ["mvn test"]
    if predefined_command is not None:
        for idx in range(len(travis_setting["script"])):
            if "mvn" in travis_setting["script"][idx][:3]:
                travis_setting["script"][idx] = predefined_command

    # Add notification [TODO make this configurable]
    if "notifications" not in travis_setting:
        travis_setting["notifications"] = {}
    if "webhooks" not in travis_setting["notifications"]:
        travis_setting["notifications"]["webhooks"] = {}
    travis_setting["notifications"]["webhooks"]["urls"] = [AZURE_FUNCTION_ENTRY]
    travis_setting["notifications"]["webhooks"]["on_success"] = "always"
    travis_setting["notifications"]["webhooks"]["on_failure"] = "always"
    travis_setting["notifications"]["webhooks"]["on_start"] = "never"
    travis_setting["notifications"]["webhooks"]["on_cancel"] = "never"
    travis_setting["notifications"]["webhooks"]["on_error"] = "always"

    # Add after_script to upload test reports as compressed file for now
    if "after_script" not in travis_setting:
        travis_setting["after_script"] = []
    if compress_test_reports() not in travis_setting["after_script"]:
        travis_setting["after_script"] = report_uploader(travis_setting["after_script"])

    write_file = open(os.path.join(repo_dir, ".travis.yml"), 'w')
    yaml.dump(travis_setting, write_file, default_flow_style=False, width=float("inf"))
    write_file.close()
    return os.path.join(repo_dir, ".travis.yml")

def ekstazi_setup(ci_tool, overwrite_run_command, repo_dir):
    modified_files = []
    # add ekstazi in pom.xml file
    pm = PomManager(repo_dir)
    pm.add_plugin(EKSTAZI_XML_PATH)
    modified_files += pm.pom_list
    if ci_tool is not None:
        run_command = None
        if overwrite_run_command:
            run_command = "mvn test"
        # [TODO] generalize the predefined command
        modified_file = {
            "travis": travis_setup(repo_dir, "ekstazi", ["clz"], run_command)
        }.get(ci_tool.lower(), None)
        if modified_file is None:
            print("Finished Ekstazi setup for local testing as setup for {} is not supported".format(ci_tool))
        else:
            print("Finished Ekstazi setup for {}".format(ci_tool))
            modified_files.append(modified_file)
    else:
        print("Finished Ekstazi setup for local testing")
    return modified_files

# [TODO] clean up, not being used
def setup_template(rts_setup_function, ci_setup_function, repo_dir):
    modified_files = rts_setup_function(repo_dir)
    modified_files.append(ci_setup_function(repo_dir))
    return modified_files