#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import sys

try:
    import simplekml
except ImportError:
    sys.stderr.write("\033[91mNeed to install 'simplekml'\033[00m\n")
    sys.exit(-1)

KML_HEADER = 'xmlns="http://www.opengis.net/kml/2.2"'
XML_HEADER = 'version="1.0" encoding="UTF-8"'

NEEDS_JOIN_STATE = 1 # Magic number
NEEDS_INDENT_STATE = 2 # Magic number

SEPARATOR = ','

getStartEndTags = lambda key: ('<%s>'%(key), '</%s>'%(key))
isListOrTuple = lambda v: isinstance(v, list) or isinstance(v, tuple)
isStrOrNumber = lambda v: isinstance(v, str) or hasattr(v, '__divmod__')

def placemarkKMLConvert(markerList):
    """
    Extracts information needed for writing marker locations to a Google Earth kml.
    """
    markerskml = simplekml.Kml()

    for marker in markerList:
        marker_id = marker['Marker']['id']  
        marker_coords = (marker['Marker']['lon'], marker['Marker']['lat'])

        markerPoint = markerskml.newpoint(name=str(marker_id), coords=[marker_coords])
        markerPoint.description = marker['Marker']['comments']

    return markerskml.kml()


def textifyTree(content, indentLevel=1):
    if isStrOrNumber(content):
        return str(content), NEEDS_JOIN_STATE
    else:
        outText = ''
        lastState = NEEDS_JOIN_STATE
        if isListOrTuple(content):
            contentLen = len(content)
            tabsByLevel ='\t' * indentLevel 
            for index, elem in enumerate(content):
                text, state = textifyTree(elem, indentLevel)
                outText += text
                if index < contentLen-1 and state == NEEDS_JOIN_STATE:
                    outText += SEPARATOR
                lastState = state
            if lastState == NEEDS_JOIN_STATE:
                outText = tabsByLevel + '\t' + outText

        elif isinstance(content, dict):
            indentLevel += 1
            tabsByLevel = '\t' * indentLevel
            for k, v in content.items():
                startTag, endTag = getStartEndTags(k.__str__())
                specificText = tabsByLevel  + startTag
                text, state = textifyTree(v, indentLevel)
                if state == NEEDS_INDENT_STATE:
                    if text:
                        specificText += '\n' + text + '\n' + tabsByLevel
                else:
                    specificText += text
                    
                specificText +=  endTag + '\n'

                outText += specificText

        return outText, NEEDS_INDENT_STATE

def kmlDoc(tree):
    fmtdText = '{xmlH}\n{kmlH}\n\t<Document>'.format(
        xmlH='<?xml ' + XML_HEADER + '?>', kmlH='<kml ' + KML_HEADER + '>'
    )
        
    text , lastState = textifyTree(tree, 1)
    fmtdText += '\n' + text
    fmtdText += '\n\t</Document>\n</kml>'
    return fmtdText

def main():
    sampleTree = dict(
        Placemark=dict(name='New York City', description='NYC',
            point=dict(coordinates=(-74.0064, 40.71, 0,))
        )
    )

    content = kmlDoc(sampleTree)
    print(content)

if __name__ == '__main__':
    main()
