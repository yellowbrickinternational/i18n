Steps to use YB-i18n tool

* install python3 and make (optional)
* make a venv

```sh
python3 -m venv /path/to/venv/my-venv
source /path/to/venv/my-venv/bin/activate
```

* install requirements

```sh
make install

or

pip install -r requirements.txt
```

i18n tool is using google-drive api. To enable apis, you can follow this link
[Gdrive API](https://developers.google.com/drive/api/v3/quickstart/python)

and then run:

```sh
python main.py ${sheet-id} ${root-folder}
```

example:

```sh
python main.py 1tUavqx2MwstEJui2039d-jtLFFUDlDjHNRFNt5dG9pg 3.4.7
```

SQL files are then generated under 3.4.7 for each concerned schema: **brickparking**, **billing** or **app**
