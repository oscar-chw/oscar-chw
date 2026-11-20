# Maintaining this profile

Run the offline checks from the repository root:

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

Pull requests run these checks without fetching market data or changing images.
They verify the local image references, the SVG/GIF formats, known withdrawn
claim patterns and the order-book renderer. The claim scan is a regression
check, not a general fact checker. New claims still require source evidence.

The separate scheduled order-book workflow refreshes only the header's depth
bars. Its tests preserve the rest of the SVG; do not run the updater as part of
a profile-content review.

`profile-settings.json` is a proposed account/repository presentation update.
It records the intended website field, pin order, repository descriptions and
topics so those settings can be reviewed alongside this README. CI and merging
this file do not apply GitHub settings. Apply them only after the profile review
is accepted, then read back the actual settings. The LinkedIn social link stays
available separately from the personal website field.

The public showcase describes dated evidence. Local development checkpoints,
passing checks and accepted source reviews do not become performance claims.
