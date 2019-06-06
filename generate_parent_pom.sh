#!/bin/bash

set -e
set -u
set -x

PARENT_POM="$1"
VERSION_PLACEHOLDER="==DYNAMIC_VERSION=="
PROJECTS_PARENT_DIR="./mypoms"

get_tag_value(){
    POM_PATH=$1
    TAG_NAME="$2"

    grep -E $POM_PATH -e "< *$TAG_NAME *>" | grep -o '>.*<' | tr -d '><'
}

get_dependencies(){
    POM_PATH=$1
    for line in $(cat $POM_PATH | grep " *$VERSION_PLACEHOLDER *"); do
        echo "$line" | sed 's@<\|>.*@@g' | sed 's@\.version@@g'
    done
}

get_artifact_id(){
    POM_PATH="$1"
    get_tag_value $POM_PATH artifactId
}

get_version(){
    POM_PATH=$1
    get_tag_value $POM_PATH version
}

get_tag_value pom.xml artifactId

exit 1

for dep in $(get_dependencies $PARENT_POM); do
    for pomfile in $(find $PROJECTS_PARENT_DIR -iname 'pom.xml'); do
        ARTIFACT_ID="$(get_artifact_id $pomfile)"
        echo "artifact id: $ARTIFACT_ID"
        if [ "$ARTIFACT_ID" = "$dep" ]; then
            VERSION="$(get_version $pomfile )"
            echo "Found dep $dep with version $VERSION"
        fi
    done
done
