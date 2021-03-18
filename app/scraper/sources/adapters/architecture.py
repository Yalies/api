from .adapter import Adapter


class Architecture(Adapter):

    def scrape_path(self, department, path):
        people = []

        page = 1
        profile_urls = []
        while True:
            people_page_soup = self.get_soup(department['url'] + path, params={'page': page})
            links_page = people_page_soup.select('div.faculty-member-thumbnail a')
            if len(links_page) == 0:
                break
            print(f'Found {len(links_page)} people on page {page}.')
            profile_urls += [department['url'] + link['href'] for link in links_page]
            page += 1

        for profile_url in profile_urls:
            person = {
                'profile': profile_url,
            }
            person_soup = self.get_soup(profile_url)
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
