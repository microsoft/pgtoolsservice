####################################################################
# Currently not being maintained. Please use test-all.sh instead. #
####################################################################

#!/usr/bin/env bash
if [ ! -d 'ossdbtoolsservice' ] || [ ! -d 'tests' ] || [ ! -d 'pgsmo' ]
then
  echo "Script must be executed from root of repo"
  exit 1
fi

nosetests -a '!is_integration_test' --with-xunit "$@"
