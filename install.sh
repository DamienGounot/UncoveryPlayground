#pip freeze .py > requirements

# get pip
curl https://bootstrap.pypa.io/get-pip.py > get-pip.py
python get-pip.py

# install requirements
pip install -r requirements.txt
