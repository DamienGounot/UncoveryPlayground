#pip freeze .py > requirements

# get pip
curl https://bootstrap.pypa.io/get-pip.py > get-pip.py
python get-pip.py

# create requirement

pip install pipreqs

pipreqs /path/to/project

# install requirements
pip install -r requirements.txt


# workaround
# python -m pip install [packageName]