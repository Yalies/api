from .adapter import Adapter


class Management(Adapter):

    def get_profile_urls(self, parent, department_url):
        links = parent.select('h4.faculty--teaser-name a')
        return [department_url + link['href'] for link in links]

    def scrape_path(self, department, path):
        people = []
        people_soup = self.get_soup(department['url'] + path)
        profile_urls = self.get_profile_urls(people_soup, department['url'])

        for profile_url in profile_urls:
            person = {
                'profile_url': profile_url,
            }
            person_soup = self.get_soup(profile_url)
            person['name'] = person_soup.find('h1', {'id': 'page-title'}).text.strip()
            title = person_soup.find('h2', {'class': 'sub-title'})
            if title:
                person['title'] = title.text.strip()
            image = person_soup.select_one('div.faculty--image img')
            if image:
                person['image'] = image['src'].split('?')[0]

            card = person_soup.find('div', {'class': 'content-layout__aside'})
            info_list = card.find('ul', {'class': 'faculty--info-list'})
            email = info_list.find('li', {'class': 'email'})
            if email:
                person['email'] = email.text.strip()
            for link in info_list.select('li.url a'}):
                # TODO: are these all the options?
                if 'Website' in link.text or 'Webpage' in link.text:
                    person['website'] = link['href']
                elif 'CV' in link.text:
                    person['cv'] = link['href']

            people.append(person)
            print('Parsed ' + person['name'])

        return people
