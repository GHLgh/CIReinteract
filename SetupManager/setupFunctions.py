from .PomManager import PomManager
import travis_yml
import yaml
import os

EKSTAZI_XML_PATH = "{}/ekstazi.xml".format(os.path.dirname(os.path.realpath(__file__)))
AZURE_FUNCTION_ENTRY = "https://cireinteract.azurewebsites.net/api/CINotificationEndPoint?code=AEW9Jm5ijk8SNN2PA0hIPwAxIcb3lqjqWL97EadKyB6qWSkNqNC0bQ=="

def travis_setup(repo_dir, tag, suffixes, keyWordReplacement):
    def restore_by_suffix(tag, suffix):
        return "(cd $HOME/{}_cache && find . -name '*.{}' -print | cpio -pvdumB /)".format(tag, suffix)

    def cache_by_suffix(tag, suffix):
        return "find $TRAVIS_BUILD_DIR -name '*.{}' -print | cpio -pvdumB $HOME/{}_cache".format(suffix, tag)

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
    for keyword in keyWordReplacement:
        for idx in range(len(travis_setting["script"])):
            if "mvn" in travis_setting["script"][idx][:3] and keyword in travis_setting["script"][idx]:
                travis_setting["script"][idx] = travis_setting["script"][idx].replace(keyword, keyWordReplacement[keyword])

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

    write_file = open(os.path.join(repo_dir, ".travis.yml"), 'w')
    yaml.dump(travis_setting, write_file, default_flow_style=False, width=float("inf"))
    write_file.close()
    return os.path.join(repo_dir, ".travis.yml")

def ekstazi_setup(ci_tool, repo_dir):
    modified_files = []
    # add ekstazi in pom.xml file
    pm = PomManager(repo_dir)
    pm.add_plugin(EKSTAZI_XML_PATH)
    modified_files += pm.pom_list
    if ci_tool is not None:
        modified_file = {
            "travis": travis_setup(repo_dir, "ekstazi", ["clz"], {})
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
def default_setup(ci_tool, repo_dir):
    # should only be called for seed branches to make sure the output are the same
    modified_files = []
    if ci_tool == "travis":
        read_file = open(os.path.join(repo_dir, ".travis.yml"), 'r')
        travis_setting = yaml.load(read_file)
        read_file.close()
        write_file = open(os.path.join(repo_dir, ".travis.yml"), 'w')
        yaml.dump(travis_setting, write_file, default_flow_style=False, width=float("inf"))
        write_file.close()
        modified_files.append(os.path.join(repo_dir, ".travis.yml"))
    return modified_files