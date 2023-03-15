# bibliography
Useful scripts for bibliography

A python script is used to create a markdown file from a DOI.
It takes several interesting informations like author names, year of publication, journal and abstract if provided.
DOI information are retrived either from crossref of arxiv.

The following methods can be used directly from a terminal:
```
getMarkdonwNotes https://doi.org/10.1038/s41467-021-27317-1
```
or 
```
getMarkdonwNotes 10.1038/s41467-021-27317-1  
```

after implementing the following alias:
```
PDFPATH="'/your/folder/for/saving/mardown/files'"
alias getMarkdonwNotes='python3 -c "import sys; import DOI_to_markdown as dd; dd.create_md_file(sys.argv[1], '$PDFPATH')"'
```
