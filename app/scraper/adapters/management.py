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
            name = person_soup.find('h1', {'id': 'page-title'})
            if name:
                person['name'] = name.text.strip()
                title = person_soup.find('h2', {'class': 'sub-title'})
                if title:
                    person['title'] = title.text.strip()
                image = person_soup.select_one('div.faculty--image noscript img')
                if image and not 'filler' in image['src']:
                    person['image'] = self.clean_image(image['src'])

                card = person_soup.select_one('section.content-layout--grid div.content-layout__aside')
                print(card)
                info_list = card.find('ul', {'class': 'faculty--info-list'})
                if info_list:
                    email = info_list.find('li', {'class': 'email'})
                    if email:
                        person['email'] = email.text.strip()
                    for link in info_list.select('li.url a'):
                        # TODO: are these all the options?
                        if 'Website' in link.text or 'Webpage' in link.text:
                            person['website'] = link['href']
                        elif 'CV' in link.text:
                            person['cv'] = link['href']

                education = person_soup.find('ul', {'class': 'faculty--education-list'})
                if education:
                    degrees = education.find_all('li')
                    person['education'] = '\n'.join([degree.text for degree in degrees])
            else:
                # We're in a faculty.som.yale.edu page
                person['name'] = person_soup.find('h1', {'class': 'faculty-nameplate__name'}).text.strip()
                title = person_soup.find('h2', {'class': 'faculty-nameplate__title'})
                if title:
                    person['title'] = title.text.strip()
                website = person_soup.select_one('.wpb_wrapper p > a')
                if website:
                    person['website'] = website['href']
                image = person_soup.select_one('.wpb_wrapper img')
                cv = person_soup.select_one('a[href$="curriculum-vitae/"]')
                if person:
                    person['cv'] = cv['href']

                contact_information = person_soup.select_one('a[href$="contact-information/"]')
                if contact_information:
                    contact_url = contact_information['href']
                    contact_soup = self.get_soup(contact_url)
                    body = contact_soup.select_one('.wpb_wrapper .wpb_wrapper')
                    ps = body.find_all('p')
                    email = body.find('a[href^="mailto:"]')
                    if email:
                        person['email'] = email.text.strip()

                    address_next = False
                    for p in ps:
                        if 'Postal Address:' in p.text:
                            address_next = True
                        elif address_next:
                            person['address'] = p.text.strip()
                            address_next = False
                        elif 'office:' in p.text:
                            person['room_number'] = p.text.replace('office:', '').strip()

            people.append(person)
            print('Parsed ' + person['name'])

        return people
