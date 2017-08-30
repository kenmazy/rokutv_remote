# RokuTV Remote
Whipped this hack together in an evening, does the job.

Standalone python GUI app (wxPython) that mimics a RokuTV remote.

Supported features are whatever buttons exist in the picture:

![Screenshot](/screenshot.png)

# Requirements

Normal python dependencies via requirements.txt, install via:

```
pip install -r requirements.txt
```

# Usage

Modify the hardcoded values `IP_ADDRESS`, `MAC_ADDRESS`, etc.

Run via:

```
python app.py
```

# Adding More Buttons

I added some passable blank buttons and spacers, though since there's fancy
lighting effects in the original image it doesn't quite line up.

You can modify `LAYOUT` and add some buttons, though there are some limitations
because I didn't feel like coding more.

## Adding More Apps

Add another row to `LAYOUT`, make the element name `app_FOO` where `FOO` is the
app name found via querying `curl http://IP_TO_YOUR_ROKU:8060/query/apps`.
Optionally add a button called `app_FOO.png` to the `images/` folder.

# Credits

All images credit to A. Cassidy Napoli at [remoku.tv](remoku.tv), except the ones I
photoshopped.

# License

MIT license
