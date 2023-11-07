import requests

from qgis.PyQt.QtCore import QThread


class GetUnitsTask(QThread):
    def __init__(self, manager):
        super(GetUnitsTask, self).__init__()
        self.manager = manager

    def run(self):
        self.error = None
        config = self.auth_manager.currentConfig()
        uri = config.uri()
        self.manager.units = []
        headers = {
            'Authorization': 'Bearer %s' % self.token
        }
        available_countries = self.availableCountries(uri, headers)
        for code in available_countries:
            country = self.manager.country_codes.get(code, code)
            try:
                url = '%s/administrative-unit/%s' % (uri, code)
                response = requests.request("GET", url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    units = data.pop('types')
                    for unit in units:
                        self.manager.units.append('%s %s' % (country, unit))
                    self.getUnits(data.get('units'), units, 0, [country])
                else:
                    self.error = response.text
            except Exception as e:
                self.error = e

    def getUnits(self, unit_list, units, level, parents):
        level += 1
        for unit_dict in unit_list:
            parents2 = parents.copy()
            parents.append(unit_dict.get('name'))
            parents2.append('%s (%s)' % (unit_dict.get('name'), unit_dict.get('code')))
            self.manager.units.append(', '.join(parents2))
            for unit in units[level:]:
                self.manager.units.append('%s %s' % (', '.join(parents), unit))
            if len(unit_dict.get('subunits')) > 0:
                self.getUnits(unit_dict.get('subunits'), units, level, parents)
            if level == 1:
                parents = [parents[0]]
            else:
                parents = parents[:level]

    def availableCountries(self, uri, headers):
        try:
            response = requests.request("GET", '%s/administrative-unit/available-countries' % uri, headers=headers)
            if response.status_code == 200:
                available_countries = response.json()
            else:
                available_countries = ['pl']
        except Exception as e:
            available_countries = ['pl']
        return available_countries
