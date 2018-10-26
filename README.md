# CIReinteract

This is the repository for part of the CS599DM project, which provides researchers a tool to perform experiments on Regression Test Selection (RTS) in a Continuous Intergration (CI) environment.

### Workflow
With this tool, you are able to:
* Decompose a git repository into numorous branches by commit history, each generated branch, `seed_#`, will represent the repository status at # commits away from master HEAD.
* Create new branches out of each "seed" branch for the RTS tool being examined, `{tool's name}_seed_#` and `{tool's name}_#-(#-1)`. In the new branches, the CI configuration and build configuration will be modified to run the RTS tool.
* After the CI build are completed on `{tool's name}_#-(#-1)` branches, those branches' commit history will be "incremented" by merging corresponding `{tool's name}_seed_(#-1)` branch. In this way, each `{tool's name}_#-(#-1)` branch simulates the development behavior of making a new commit (#-1) and using RTS tool to check the correctness.

Therefore, the CI results of `{tool's name}_seed_(#-1)` branches can be used to examine the effect of the RTS tool. Similarly, the last two points described above can apply to other RTS tools simultaneously to generate results programatically.

### RTS Tool Support
* Ekstazi

### CI Support
* Travis-ci

### Customize Tool Support
[TODO]
