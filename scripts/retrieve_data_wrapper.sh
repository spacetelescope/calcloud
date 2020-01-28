#! /bin/sh

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
#__conda_setup="$('/home/ec2-user/miniconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
#echo $__conda_setup
#eval "$__conda_setup"

#source /home/ec2-user/.bashrc

#if [ $? -eq 0 ]; then
#    eval "$__conda_setup"
#else
#    if [ -f "/home/ec2-user/miniconda3/etc/profile.d/conda.sh" ]; then
#        . "/home/ec2-user/miniconda3/etc/profile.d/conda.sh"
#    else
#        export PATH="/home/ec2-user/miniconda3/bin:$PATH"
#    fi
#fi
#unset __conda_setup
# <<< conda initialize <<<

#printenv
echo $USER
echo $HOME
pwd
source /home/ec2-user/.bashrc

conda activate hstdp
which python
which conda

python retrieve_data.py $*
