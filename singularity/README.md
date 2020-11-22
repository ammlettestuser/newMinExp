This repository contains several scripts that simplify the interactions with singularity containers for our experiments.

To install this submodules in your project:
1) Run the following commands:
```
mkdir -p submodules
git submodule add ../../../AIRL_tools/singularity_scripts ./submodules/singularity_scripts
```
The url is relative to the url of your project, so here we assumed that you project is for instance located in `/Students_projects/My_Self/My_Project`
You will now have a folder named `submodules/singularity_scripts` containing all the necessary scripts.

2) You can add in your singularity folder  symbolic links for a simplified access to the scripts of this submodules:
```
cd ./singularity/
ln -s ../submodules/singularity_scripts/*.sh ./
```

------
Quick tips with git submodules

- To update the gitlab_notebook tools in your project, run `git submodule update --remote`
- To clone a project with the submodules already configures: `git clone --recurse-submodules https://your_url.git`