import subprocess
import xml.dom.minidom as minidom
import os
import sys

def findChildren(parentNode, tagName):
    return [nd for nd in parentNode.childNodes if hasattr(nd, 'tagName') and nd.tagName == tagName]

def findChild(parentNode, tagName):
    return findChildren(parentNode, tagName)[0]

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
        self.parentVersionNode = findChild(self.parentNode, 'version')

    def __eq__(self, other):
        return os.path.abspath(self.path) == os.path.abspath(other.path)

    @property
    def artifactId(self):
        return getChildValue(self.projectNode, 'artifactId')

    def update_original(self):
        pass

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

    def updateDependencyVersions(self, projectsDir:str):
        poms = self.getPomsFromDir(projectsDir)
        pom_dict = {p.artifactId:p for p in poms}
        for depNode in self.getDependencyNodes():
            depName = depNode.tagName.replace('.version', '')
            if depName in pom_dict:
                depNode.firstChild.nodeValue = pom_dict[depName].version
            else:
                print(f"WARNING: Could not find pom for dependency '{depName}' in directory '{projectsDir}'", file=sys.stderr)
        self.bumpVersion()

    def bumpVersion(self):
        print(f"this is version::::::::::::::::: {self.version}")
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
    pom = Pom(sys.argv[1])
    pom.updateDependencyVersions(sys.argv[2])
    print(pom)



