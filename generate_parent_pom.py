import subprocess
import xml.dom.minidom as minidom
import sys

def findChildren(parentNode, tagName):
    return [nd for nd in parentNode.childNodes if hasattr(nd, 'tagName') and nd.tagName == tagName]

def findChildrenBySuffix(parentNode, suffix):
    return [nd for nd in parentNode.childNodes if hasattr(nd, 'tagName') and nd.tagName.endswith(suffix)]

def findDependencyVersion(depName:str, depDir:str):
    poms = subprocess.check_output(['find', '.', '-iname', 'pom.xml'], universal_newlines=True).splitlines()

def getChildValue(node, childTagName:str):
    return findChildren(node, childTagName)[0].firstChild.nodeValue

class Pom:
    def __init__(self, path:str):
        self.xml = minidom.parse(path)
        self.projectNode = findChildren(self.xml, 'project')[0]
        self.artifactId = getChildValue(self.projectNode, 'artifactId')
        self.version = getChildValue(self.projectNode, 'version')

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
        pomPaths = subprocess.check_output(['find', projectsDir, '-iname', 'pom.xml'], universal_newlines=True).splitlines()
        poms = [Pom(path) for path in pomPaths]
        pom_dict = {p.artifactId:p for p in poms}
        for depNode in self.getDependencyNodes():
            depName = depNode.tagName.replace('.version', '')
            if depName in pom_dict:
                depNode.firstChild.nodeValue = pom_dict[depName].version
            else:
                print(f"WARNING: Could not find pom for dependency '{depName}' in directory '{projectsDir}'", file=sys.stderr)

        return self.xml.toprettyxml(encoding='UTF-8')


if __name__ == '__main__':
    pom = Pom(sys.argv[1])
    for line in pom.updateDependencyVersions(sys.argv[2]).decode('utf-8').splitlines():
        if line.strip() == '':
            continue
        print(line)



