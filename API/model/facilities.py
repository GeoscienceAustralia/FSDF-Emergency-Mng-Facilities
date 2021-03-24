# -*- coding: utf-8 -*-

from flask import render_template, Response

import conf
from pyldapi import Renderer, Profile
from rdflib import Graph, URIRef, RDF, Namespace, Literal, BNode
from rdflib.namespace import XSD, SKOS   #imported for 'export_rdf' function

from .gazetteer import GAZETTEERS, NAME_AUTHORITIES
from .dggs_in_line import get_cells_in_json_and_return_in_json

# for DGGSC:C zone attribution
import requests
import ast
DGGS_API_URI = "http://ec2-54-206-28-241.ap-southeast-2.compute.amazonaws.com/api/search/"
# test_DGGS_API_URI = "https://dggs.loci.cat/api/search/"
DGGS_uri = 'https://fsdf.org.au/dataset/auspix-dggs/ausPIX/'

from rhealpixdggs import dggs
rdggs = dggs.RHEALPixDGGS()

TABLE_NAME = 'Facilities_all84_with_dggs'
NAME_FIELD = 'name'


class Facilities(Renderer):
    """
    This class represents a placename and methods in this class allow a placename to be loaded from the GA placenames
    database and to be exported in a number of formats including RDF, according to the 'PlaceNames Ontology'

    [[and an expression of the Dublin Core ontology, HTML, XML in the form according to the AS4590 XML schema.]]??
    """

    def __init__(self, request, uri):
        format_list = ['text/html', 'text/turtle', 'application/ld+json', 'application/rdf+xml']
        profiles = {
            'Facilities': Profile(
                'http://linked.data.gov.au/def/facilities/',
                'Facilities View',
                'This view is for facilities delivered by the facilities dataset'
                ' in accordance with the Facilities Profile',
                format_list,
                'text/html'
            )
        }

        super(Facilities, self).__init__(request, uri, profiles, 'Facilities')

        self.id = uri.split('/')[-1]

        q = '''
               SELECT
                   "name",
                   "AusPIX_DGGS",
                   "uri_auspix",
                   "cellsarea_m2",                   
                   "featuresubtype",
                   "feature_date",
                   "feature_source",
                   "attribute_date",
                   "attribute_source",
                   "source_ufi",
                   "source_jurisdiction",
                   "custodian_agency",
                   "custodian_licensing",
                   "loading_date",
                   "building_id",
                   "main_function",
                   "operationalstatus",
                   "height",
                   "address",
                   "suburb",
                   "local_construction_type",
                   "local_year_built",
                   "state",
                   "category",
                   "facility_type",
                   "xcoord84",
                   "ycoord84",
                   "uri_facility",
                   ST_AsEWKT(geom) As geom_wkt,
                   ST_AsGeoJSON(geom) As geom
               FROM "{}"
               WHERE "id" = '{}'
           '''.format(TABLE_NAME, self.id)

        self.hasName = {
            'uri': 'http://linked.data.gov.au/def/facilities/',
            'label': 'Facilities',
            'comment': 'The Entity has a name (label) which is a text string.',
            'value': None
        }

        self.thisFeature = []
        self.featureCords = []

        for row in conf.db_select(q):
            self.hasName['value'] = str(row[0])
            self.AusPIX_DGGS = str(row[1])
            self.uri_auspix = row[2]
            self.cellsarea_m2 = str(row[3])
            self.featuresubtype = row[4]
            self.feature_date = str(row[5])
            self.feature_source = row[6]
            self.attribute_date = str(row[7])
            self.attribute_source = row[8]
            self.source_ufi = str(row[9])
            self.source_jurisdiction = row[10]
            self.custodian_agency = row[11]
            self.custodian_licensing = row[12]
            self.loading_date = row[13]
            self.building_id = str(row[14])
            self.main_function = row[15]
            self.operationalstatus = row[16]
            self.height = row[17]
            self.address = row[18]
            self.suburb = row[19]
            self.local_construction_type = row[20]
            self.local_year_built = row[21]
            self.state = row[22]
            self.category = str(row[23])
            self.facility_type = row[24]
            self.xcoord84 = str(row[25])
            self.ycoord84 = row[26]
            self.uri_facility = row[27]

            # get geometry from database
            self.geom = ast.literal_eval(row[-1])
            self.featureCords = self.geom['coordinates']
            self.wkt = row[-2]
            self.geometry_type = self.geom['type']
            self.thisFeature.append({'label': str(self.AusPIX_DGGS),
                                      'uri': self.uri_auspix})



    def render(self):
        if self.profile == 'alt':
            return self._render_alt_profile()  # this function is in Renderer
        elif self.mediatype in ['text/turtle', 'application/ld+json', 'application/rdf+xml']:
            return self.export_rdf(self.profile)
        else:  # default is HTML response: self.format == 'text/html':
            return self.export_html(self.profile)


    def export_html(self, model_view='SA1_AEIP'):
        html_page = 'facilities.html'
        return Response(        # Response is a Flask class imported at the top of this script
            render_template(     # render_template is also a Flask module
                html_page,   # uses the html template to send all this data to it.
                id=self.id,
                hasName=self.hasName,
                coordinate_list=self.featureCords,
                geometry_type=self.geometry_type,
                uri_auspix=self.uri_auspix,
                cellsarea_m2=self.cellsarea_m2,
                featuresubtype=self.featuresubtype,
                feature_date=self.feature_date,
                feature_source=self.feature_source,
                attribute_date=self.attribute_date,
                attribute_source=self.attribute_source,
                source_ufi=self.source_ufi,
                source_jurisdiction=self.source_jurisdiction,
                custodian_agency=self.custodian_agency,
                custodian_licensing=self.custodian_licensing,
                loading_date=self.loading_date,
                building_id=self.building_id,
                main_function=self.main_function,
                operationalstatus=self.operationalstatus,
                height=self.height,
                address=self.address,
                suburb=self.suburb,
                local_construction_type=self.local_construction_type,
                local_year_built=self.local_year_built,
                state=self.state,
                category=self.category,
                facility_type=self.facility_type,
                xcoord84=self.xcoord84,
                ycoord84=self.ycoord84,
                uri_facility=self.uri_facility,
                ausPIX_DGGS = self.thisFeature,
                wkt=self.wkt
            ),
            status=200,
            mimetype='text/html'
        )



    def _generate_dggs(self):
        if self.id is not None and self.thisFeature is not None:
            dggs_uri = []
            for item in self.thisFeature:
                dggs_uri.append(item['uri'])
            return '{}'.format(dggs_uri)
        else:
            return ''


    def export_rdf(self, model_view='SA1_AEIP'):
        g = Graph()  # make instance of a RDF graph

        # namespace declarations
        dcterms = Namespace('http://purl.org/dc/terms/')  # already imported
        g.bind('dcterms', dcterms)
        geo = Namespace('http://www.opengis.net/ont/geosparql#')
        g.bind('geo', geo)
        owl = Namespace('http://www.w3.org/2002/07/owl#')
        g.bind('owl', owl)
        rdfs = Namespace('http://www.w3.org/2000/01/rdf-schema#')
        g.bind('rdfs', rdfs)
        sf = Namespace('http://www.opengis.net/ont/sf#')
        g.bind('sf', sf)
        skos = Namespace('https://www.w3.org/2009/08/skos-reference/skos.html')

        geox = Namespace('http://linked.data.gov.au/def/geox#')
        g.bind('geox', geox)
        g.bind('xsd', XSD)

        core = Namespace('http://linked.data.gov.au/def/core#')
        g.bind('core', core)
        net = Namespace('http://linked.data.gov.au/def/net#')
        g.bind('net', net)

        auspix = URIRef('http://ec2-52-63-73-113.ap-southeast-2.compute.amazonaws.com/AusPIX-DGGS-dataset/')
        g.bind('auspix', auspix)

        ptype = Namespace('http://pid.geoscience.gov.au/def/voc/ga/PlaceType/')
        g.bind('ptype', ptype)

        # specific to powerline datasdet
        pline_ds = Namespace('http://linked.data.gov.au/dataset/powerlines/')
        g.bind('pline_ds', pline_ds)

        # made the cell ID the subject of the triples
        pline = Namespace('http://linked.data.gov.au/def/powerlines/')
        g.bind('pline', pline)

        # build the graphs
        power_line = URIRef('{}{}'.format(pline_ds, self.id))
        g.add((power_line, RDF.type, URIRef(pline + 'Powerline')))
        g.add((power_line, dcterms.identifier, Literal(self.id, datatype=pline.ID)))
        # g.add((power_line, pline.operator, Literal(str(self.operator), datatype=dcterms.Agent)))
        # g.add((power_line, pline.owner, Literal(str(self.owner), datatype=dcterms.Agent)))
        g.add((power_line, pline.description, Literal(str(self.descripton))))
        g.add((power_line, pline.lineclass, Literal(str(self.lineclass))))
        g.add((power_line, pline.capacityKV, Literal(str(self.capacitykv))))
        g.add((power_line, pline.state, Literal(str(self.state))))


        g.add((power_line, core.name, Literal(self.hasName['value'], lang='en-AU')))
        g.add((power_line, core.attriuteSource, Literal(str(self.attributesource))))
        # g.add((power_line, core.custodianAgency, Literal(str(self.custodianagency), datatype=SKOS.Concept)))
        # g.add((power_line, core.custodianLicensing, Literal(str(self.custodianlicensing), datatype=dcterms.LicenseDocument)))
        g.add((power_line, core.featureSource, Literal(str(self.featuresource))))
        g.add((power_line, core.featureType, URIRef(ptype + self.featuretype)))
        g.add((power_line, core.operationalStatus, Literal(str(self.operationalstatus), datatype=SKOS.Concept)))
        # g.add((power_line, core.sourceJurisdiction, Literal(str(self.sourcejurisdication), datatype=SKOS.Concept)))
        g.add((power_line, core.attriuteDate, Literal(str(self.attributedate), datatype=XSD.dateTime)))
        g.add((power_line, core.featureDate, Literal(str(self.featuredate), datatype=XSD.dateTime)))
        # g.add((power_line, core.loadingDate, Literal(str(self.loadingdate), datatype=XSD.dateTime)))
        g.add((power_line, core.planimetricAccuracy, Literal(str(self.planimetricaccuracy), datatype=core.Measure)))
        # g.add((power_line, core.sourceUFI, Literal(str(self.sourceUFI))))
        # g.add((power_line, core.verticalAccuracy, Literal(str(self.verticalaccuracy), datatype=core.Measure)))
        g.add((power_line, core.spatialConfidence, Literal(str(self.spatialconfidence))))


        pline_wkt = BNode()
        g.add((pline_wkt, RDF.type, URIRef(sf + self.geometry_type)))
        g.add((pline_wkt, geo.asWKT, Literal(self.wkt, datatype=geo.wktLiteral)))
        g.add((power_line, geo.hasGeometry, pline_wkt))

        pline_dggs = BNode()
        g.add((pline_dggs, RDF.type, URIRef(geo + 'Geometry')))
        g.add((pline_dggs, geox.asDGGS, Literal(self._generate_dggs(), datatype=geox.dggsLiteral)))
        g.add((power_line, geo.hasGeometry, pline_dggs))



        if self.mediatype == 'text/turtle':
            return Response(
                g.serialize(format='turtle'),
                mimetype = 'text/turtle'
            )
        elif self.mediatype == 'application/rdf+xml':
            return Response(
                g.serialize(format='application/rdf+xml'),
                mimetype = 'application/rdf+xml'
            )
        else: # JSON-LD
            return Response(
                g.serialize(format='json-ld'),
                mimetype = 'application/ld+json'
            )





if __name__ == '__main__':
    pass




