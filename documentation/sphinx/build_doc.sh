# only needed if new modules have been added to TORO
sphinx-apidoc -o source/code/ ../../TORO/libs/toro

# symbolic link to README
cd source/contents
ln -s ../../../../README.md
cd ../..

# always call make from /documentation/sphinx 
make html
