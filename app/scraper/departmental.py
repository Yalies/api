import json
import hashlib
import adapters


class Scraper:
    pass


class Departmental(Scraper):

    ADAPTERS = {
        None: adapters.Default(),
        'architecture': adapters.Architecture(),
        'environment': adapters.Environment(),
        'jackson': adapters.Jackson(),
        'law': adapters.Law(),
        'management': adapters.Management(),
        'medicine': adapters.Medicine(),
        'nursing': adapters.Nursing(),
        'seas': adapters.Seas(),
    }

    def scrape_department(self, department):
        print('Scraping department: ' + department['name'])
        website_type = department.get('website_type')
        adapter = self.ADAPTERS.get(website_type)
        return adapter.scrape(department)

    def scrape(self):
        with open('../res/departments.json', 'r') as f:
            departments = json.load(f)
        # If any departments have been marked enabled, filter to just them
        enabled_departments = [department for department in departments if department.get('enabled')]
        if enabled_departments:
            departments = enabled_departments

        people = []
        for department in departments:
            people += self.scrape_department(department)
        return people

if __name__ == '__main__':
    departmental = Departmental()
    people = departmental.scrape()
    with open('/tmp/people.json', 'w') as f:
        json.dump(people, f)
