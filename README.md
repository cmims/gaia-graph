# gaia-graph

An interactive 3D visualization of Milky Way stars using data from the Gaia DR3 catalog, with stars colored by spectral class and key landmarks annotated.

## Usage

### With Docker (recommended)

```bash
docker-compose up
```

The plot is saved to `output/milky_way.html` on your host machine and can be opened in any browser. The `output/` and `gaia_cache/` directories are mounted as volumes so generated files persist between runs.

### Without Docker

```bash
pip install -r requirements.txt
python gaia.py
```

The plot is saved to `output/milky_way.html` and can be opened in any browser.

## Acknowledgements

This work has made use of data from the European Space Agency (ESA) mission Gaia (https://www.cosmos.esa.int/gaia), processed by the Gaia Data Processing and Analysis Consortium (DPAC, https://www.cosmos.esa.int/web/gaia/dpac/consortium). Funding for the DPAC has been provided by national institutions, in particular the institutions participating in the Gaia Multilateral Agreement.

### Citations

- Gaia Collaboration et al. ([2016b](https://gea.esac.esa.int/archive/documentation/GDR3/bib.html#bib336)): The Gaia mission (provides a description of the Gaia mission including spacecraft, instruments, survey and measurement principles, and operations);
- Gaia Collaboration et al. ([2023j](https://gea.esac.esa.int/archive/documentation/GDR3/bib.html#bib982)): Gaia DR3: Summary of the contents and survey properties;
- Babusiaux et al. ([2023](https://gea.esac.esa.int/archive/documentation/GDR3/bib.html#bib1013)): Gaia DR3: Catalogue validation;
- Please consult the entire list of official Gaia DR3 papers on https://www.cosmos.esa.int/web/gaia/dr3-papers.