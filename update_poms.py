import subprocess
import xml.dom.minidom as minidom
import os
import sys
from shutil import copyfile

def findChildren(parentNode, tagName):
    return [nd for nd in parentNode.childNodes if hasattr(nd, 'tagName') and nd.tagName == tagName]

def findChild(parentNode, tagName):
    try:
        return findChildren(parentNode, tagName)[0]
    except IndexError:
        return None

def findChildrenBySuffix(parentNode, suffix):
    return [nd for nd in parentNode.childNodes if hasattr(nd, 'tagName') and nd.tagName.endswith(suffix)]

def findDependencyVersion(depName:str, depDir:str):
    poms = subprocess.check_output(['find', '.', '-iname', 'pom.xml'], universal_newlines=True).splitlines()

def getChildValue(node, childTagName:str):
    return findChildren(node, childTagName)[0].firstChild.nodeValue

def getNodeValue(node):
    return node.firstChild.nodeValue

def setNodeValue(node, value):
    node.firstChild.nodeValue = value

class Pom:
    @classmethod
    def getPomsFromDir(cls, projectsDir:str):
        pomPaths = subprocess.check_output(['find', projectsDir, '-iname', 'pom.xml'], universal_newlines=True).splitlines()
        return [cls(path) for path in pomPaths]

    def __init__(self, path:str):
        self.path = path
        self.xml = minidom.parse(path)
        self.projectNode = findChild(self.xml, 'project')
        self.versionNode = findChild(self.projectNode, 'version')

        self.parentNode = findChild(self.projectNode, 'parent')
        self.parentVersionNode = findChild(self.parentNode, 'version') if self.parentNode else None
        self.parentArtifactIdNode = findChild(self.parentNode, 'artifactId') if self.parentNode else None

    def __eq__(self, other):
        return os.path.abspath(self.path) == os.path.abspath(other.path)

    @property
    def parentArtifactId(self):
        if self.parentArtifactIdNode is None:
            return None
        return getNodeValue(self.parentArtifactIdNode)

    @property
    def artifactId(self):
        return getChildValue(self.projectNode, 'artifactId')

    def updateOriginal(self, backup=True):
        print(f"INFO: Overwriting file {self.path}", file=sys.stderr)
        if backup:
            print(f"INFO: Creating backup at {self.path}.bak", file=sys.stderr)
            copyfile(self.path, self.path + '.bak')
        xml_file = open(self.path, 'w')
        xml_file.write(str(self))
        xml_file.close()

    @property
    def version(self):
        return getNodeValue(self.versionNode)

    def getPropertiesNodes(self):
        return findChildren(self.projectNode, 'properties')

    def getDependencyNodes(self):
        dependencyNodes = []
        for propertiesNode in self.getPropertiesNodes():
            dependencyNodes += findChildrenBySuffix(propertiesNode, '.version')
        return dependencyNodes

    def getDependencyNames(self):
        return [nd.tagName.replace('.version', '') for nd in self.getDependencyNodes()]

    def __repr__(self):
        return f"<Pom {self.artifactId} {self.version}>"

    def getChildPoms(self, childrenDirectory:str):
        poms = self.getPomsFromDir(childrenDirectory)
        return {pom.artifactId:pom for pom in poms if pom.artifactId in self.getDependencyNames()}

    def updateDependencyVersions(self, projectsDir:str):
        child_poms = self.getChildPoms(projectsDir)
        for depNode in self.getDependencyNodes():
            depName = depNode.tagName.replace('.version', '')
            if depName in child_poms:
                setNodeValue(depNode, child_poms[depName].version)
            else:
                print(f"WARNING: Could not find pom for dependency '{depName}' in directory '{projectsDir}'", file=sys.stderr)

    def bumpVersion(self):
        version_components = [int(comp) for comp in self.version.split('.')]
        version_components[-1] += 1
        setNodeValue(self.versionNode, '.'.join((str(comp) for comp in version_components)))

    def updateParentVersion(self, parentVersion):
        setNodeValue(self.parentVersionNode, parentVersion)

    def __str__(self):
        lines = []
        for line in self.xml.toprettyxml(encoding='UTF-8').decode('utf-8').splitlines():
            if line.strip() != '':
                lines.append(line)
        return '\n'.join(lines)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Update project pom's")
    parser.add_argument('--parent-path', required=True, help='The path to the parent pom.xml file')
    parser.add_argument('--children-dir', required=True, help='Path to directory containing the child pom.xml files')
    parser.add_argument('--no-backups', action='store_true', help="Do not create .bak files when overriting the pom's")
    parser.add_argument('--no-version-bump', action='store_true', help="Do not bump parent pom's version")
    args = parser.parse_args()
    print(args)

    parent_pom = Pom(args.parent_path)
    parent_pom.updateDependencyVersions(args.children_dir)
    if not args.no_version_bump:
        parent_pom.bumpVersion()
    parent_pom.updateOriginal(backup=not args.no_backups)

    for child_pom in parent_pom.getChildPoms(args.children_dir).values():
        if child_pom == parent_pom:
            continue
        #print(f"Child artifact: {child_pom.artifactId}  child.parent.artifactid: {child_pom.parentArtifactId}  parent id: {parent_pom.artifactId}")
        if child_pom.parentArtifactId is not None and child_pom.parentArtifactId == parent_pom.artifactId:
            child_pom.updateParentVersion(parent_pom.version)
            child_pom.updateOriginal(backup=not args.no_backups)
