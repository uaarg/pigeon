AUVSI SUAS: Interoperability Client Tools
=========================================

interop_cli.py
--------------

This command line tool can be used to get mission details, upload targets, and
probe the server with dummy data.

```
URL=http://10.10.130.2:8000
USER=testuser
./interop_cli.py --url $URL --username $USER missions
./interop_cli.py --url $URL --username $USER targets \
    --target_filepath tools/testdata/targets.txt \
    --imagery_dir tools/testdata/
./interop_cli.py --url $URL --username $USER probe
```

The target upload currently uses the old text file "Electronic Target Data
Format" as defined by the competition 2016 rules.

Uploader Limitations:
* Only non-ADLC targets.
* Only upload (POST), no retrieval (GET) or removal (DELETE).
* Only performs format conversion, not client-side data validation. Invalid
  data (e.g. invalid shape) will attempt to be uploaded, and the server will
  reject it.
* Does not detect duplicates- executing the script twice will upload two sets
  of targets.
