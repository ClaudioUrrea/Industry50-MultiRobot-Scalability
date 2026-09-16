# Upload guide

Both targets already exist and both are to be emptied and repopulated:

- GitHub: <https://github.com/ClaudioUrrea/Industry50-MultiRobot-Scalability>
- Figshare: <https://doi.org/10.6084/m9.figshare.33090107>

Do GitHub first; the Figshare description links to it.

## 0. Verify before touching either

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/verify_paper_numbers.py     # 80/80 checks passed
python -m pytest -q tests/                 # 42 passed
```

On Windows PowerShell the activation line is `.venv\Scripts\Activate.ps1`, and
it fails with a `PSSecurityException` unless script execution has been enabled
for the current user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

The virtual environment is a convenience, not a requirement. If you would
rather not change the execution policy, skip it entirely and run against the
system interpreter with `py` in place of `python`; the dependencies are the
ordinary scientific stack and nothing here pins a conflicting version.

If either command fails, stop.

## 1. GitHub

Replacing the contents of an existing repository, keeping its history:

```bash
cd Industry50-MultiRobot-Scalability
git init                        # only if this is a fresh working copy
git remote add origin https://github.com/ClaudioUrrea/Industry50-MultiRobot-Scalability.git
git fetch origin
git checkout -B main
git add -A
git commit -m "v2.0: align with the revised IEEE Access manuscript; correct provenance"
git push -u origin main --force-with-lease
git tag -a v2.0 -m "Resubmission to IEEE Access, September 2026"
git push origin v2.0
```

`--force-with-lease` replaces the tree while keeping the commit history. If you
would rather discard the history entirely, delete the repository on GitHub,
recreate it with the same name, and push without `--force-with-lease`.

Then, in the GitHub web interface: set the description to the first line of the
README, add the topics `industry-5-0`, `collaborative-robots`, `digital-twin`,
`reproducibility`, and create a release from tag `v2.0` with `CHANGELOG.md` as
the body.

## 2. Build the Figshare bundles

```bash
python scripts/make_release.py
```

This writes `dist/` with the four archives and `CHECKSUMS.txt`, excluding
`.git`, virtual environments and caches.

## 3. Figshare

Open the item, delete every existing file, then upload the four archives and
`CHECKSUMS.txt` from `dist/`.

Replace the description with the body of `docs/FIGSHARE_DESCRIPTION.md`. Set
the licence to CC BY 4.0. Under "Related materials", link the GitHub repository
and, once the article has a DOI, the article itself.

Publish. Figshare will mint a new version under the same DOI; cite the versioned
DOI in the manuscript if the journal asks for one.

## 4. After publication

Update `CITATION.cff` and the Data Availability Statement of the manuscript with
the article DOI, and push a `v2.0.1` tag.
