#! /usr/bin/env python3
import csv
import ipdb
from pykml import parser


class CorrelationEngine:

    def __init__(self):
        self.reference = []
        self.collected = []


    def addReference(self, filename):
        """
        Loads reference data from filename

        >>> c = CorrelationEngine()
        >>> c.addReference("myCoolFile.kml")
        """

        self.importKML(filename, self.reference)

    def clearReference(self):
        """
        Clears internal reference data

        >>> c = CorrelationEngine()
        >>> c.clearReference()
        """
        self.reference = []


    def addCollected(self, filename):
        """
        Loads collected data from filename

        >>> c = CorrelationEngine()
        >>> c.addReference("myOtherCoolFile.kml")
        """

        self.importKML(filename, self.collected)

    def clearCollected(self):
        """
        Clears internal Collected data

        >>> c = CorrelationEngine()
        >>> c.clearCollected()

        """
        self.collected = []

    def importKML(self, filename, destination, noDuplicates = True):
        """
        Imports a kml file and appends the found points to desination

        NOTE that this will NOT add duplicate entries by default

        Probably you would want to use addReference and addCollected instead.

        >>> c = CorrelationEngine()
        >>> c.importKML("Pizza.kml", myCoolListLikeVariable)

        """

        print(filename)

        # try:
        with open(filename, 'r') as f:
            doc = parser.parse(f)
        # except UnicodeDecodeError as e:
        #     with open(filename, 'rb') as f:
        #         doc = parser.parse(f)

        pm = doc.getroot().getchildren()[0].getchildren()


        for child in pm:

            entry = []
            try:
                entry = child.Point.coordinates.text.split(',')[:2]

                entry = [float(e) for e in entry]
                entry.append(child.name)

                if noDuplicates and (tuple(entry) not in destination):
                    destination.append(tuple(entry))

            except Exception as e:
                print(e)

    def exportResults(self, filename):
        """
        Do a correlation, and then export the results to filename

        >>> c = new CorrelationEngine()
        >>> c.addReference("MyReferenceData.kml")
        >>> c.addCollected("MyCollectedData.kml")
        >>> c.exportResults("MyCoolFile.csv")

        """

        results = self.correlateInternal()
        header = ['Reference x', 'Reference y', 'comment', 'Collected x', 'Collected y', 'Comment']

        with open(filename if filename.endswith('.csv') else filename + '.csv', 'w') as f:
            writer = csv.writer(f)

            for row in results:
                writer.writerow(row[0] + row[1])


    def correlateInternal(self):
        """
        Run correlate on the internally stored data
        """
        return self.correlate(self.reference, self.collected)


    def correlate(self, reference, collected):
        """
        Returns tuples of the nearest match

        Args
            - reference: list-like of (x, y, [other info]) reference data
            - collected: list-like of (x, y, [other info]) collected data

        >>> ref = [(100, 20), (2000, 13), (-15, 10)]
        >>> col = [(99, 19), (1999, 20)]
        >>> closest_node(ref, col)
        [((100, 20), (99, 19)), ((2000,13), (1999, 20))]

        """
        return [(self.closest_node(reference, coordinate), coordinate) for coordinate in collected]


    def closest_node(self, reference, node):
        """
        Returns the closest node to node in reference


        >>> ref = [(100, 20), (2000, 13), (-15, 10)]
        >>> closest_node(ref, (1, 10))
        (-15, 10)

        """
        return min(reference, key=lambda pair:(node[0] - pair[0])**2 + (node[1] - pair[1])**2)


class XYPair:
    def __init__(self, x, y, info=None):
        self.x = x
        self.y = y
        self.info = info


if __name__ == "__main__":

    cr = CorrelationEngine()

    x = [XYPair(-10,5,"pizza"), XYPair(100,200,"pizza")]
    y = [XYPair(1,3)]
    # print(cr.correlate(x,y))

    cr.addCollected('test.kml')
    cr.addReference('test2.kml')

    cr.addCollected('test2.kml')

    cr.exportResults("pizza")



