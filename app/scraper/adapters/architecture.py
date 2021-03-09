
from .department_scraper import DepartmentScraper


class Architecture(DepartmentScraper):
    def parse_path(path, department):
        people = []

        page = 1
        profile_urls = []
        while True:
            people_page_soup = get_soup(department['url'] + path, params={'page': page})
            links_page = people_page_soup.select('div.faculty-member-thumbnail a')
            if len(links_page) == 0:
                break
            print(f'Found {len(links_page)} people on page {page}.')
            profile_urls += [department['url'] + link['href'] for link in links_page]
            page += 1

        for profile_url in profile_urls:
            person = {
                'profile_url': profile_url,
            }
            person_soup = get_soup(profile_url)
            image = person_soup.select_one('.faculty-show__top-area img')
            if image is not None:
                image = image['srcset'].split('?')[0].replace('/convert', '')
                person['image'] = image
            person['name'] = person_soup.find('h1', {'class': 'h2'}).text
            title = person_soup.find('div', {'class': 'h2'})
            if title:
                person['title'] = title.text
            # TODO: parse bio and education as well
            print('Parsing ' + person['name'])
            people.append(person)
        return people
